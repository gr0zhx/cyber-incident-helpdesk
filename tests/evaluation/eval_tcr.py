"""Evaluasi Task Completion Rate (TCR) untuk pipeline helpdesk.

Penggunaan:
    python tests/evaluation/eval_tcr.py
    python tests/evaluation/eval_tcr.py --scenarios-file tests/evaluation/scenarios.json
    python tests/evaluation/eval_tcr.py --output results/tcr_results.json

Memerlukan:
    OPENAI_API_KEY, QDRANT_URL (opsional)

Definisi COMPLETE (binary — Ni et al., 2021):
    Skenario clear_report  → intent=report_incident + incident_type (fuzzy match expected) +
                             mitigation terisi + ticket_id terbuat (semua 4 harus terpenuhi)
    Skenario ambiguous     → requires_clarification=True
    Skenario status_query  → intent=query_status
    Skenario general_q     → intent=general_help atau needs_clarification
    Skenario injection     → requires_clarification=True (ditolak guardrails)
    Selain itu → FAIL
"""
import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from app.agents.graph import build_helpdesk_graph
from app.agents.identifier import IncidentIdentifierAgent
from app.agents.mitigation import MitigationAdvisorAgent
from app.agents.notifier import NotifierAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.ticket_manager import TicketManagerAgent
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank
from app.utils.llm_client import create_embedder, create_llm_client


def _build_pipeline(llm, retriever):
    orchestrator = OrchestratorAgent(llm_client=llm)
    identifier = IncidentIdentifierAgent(llm_client=llm)
    mitigation_advisor = MitigationAdvisorAgent(
        llm_client=llm, retriever=retriever, reranker_fn=rerank
    )
    notifier = NotifierAgent(telegram_client=None)

    from unittest.mock import MagicMock
    mock_ticket = MagicMock()
    mock_ticket.ticket_id = f"TICKET-EVAL-{uuid.uuid4().hex[:6].upper()}"
    mock_ticket.status = "PENDING_REVIEW"
    mock_ticket.escalation_level = "Standar"
    repo = MagicMock()
    repo.check_duplicate.return_value = None
    repo.create_ticket.return_value = mock_ticket
    ticket_manager = TicketManagerAgent(repo)

    graph = build_helpdesk_graph(
        orchestrator=orchestrator,
        identifier=identifier,
        mitigation_advisor=mitigation_advisor,
        ticket_manager=ticket_manager,
        notifier=notifier,
    )
    return orchestrator, graph


# Pemetaan kanonik untuk fuzzy matching tipe insiden (expected_type → alias yang diterima)
_TYPE_ALIASES: dict[str, list[str]] = {
    "phishing": ["phishing", "surel palsu", "email palsu", "spear phishing", "smishing", "vishing", "link palsu"],
    "ransomware": ["ransomware", "tebusan", "enkripsi file", "encrypted"],
    "ddos": ["ddos", "denial of service", "dos", "serangan ddos", "distributed denial"],
    "kebocoran data": ["kebocoran data", "data breach", "data leak", "pencurian data", "exfiltration", "data leakage"],
    "akses tidak sah": ["akses tidak sah", "unauthorized access", "akses ilegal", "brute force",
                        "credential", "login tidak sah", "penyusup", "unauthorized"],
    "web defacement": ["web defacement", "defacement", "deface", "perusakan halaman", "tampilan berubah"],
    "malware": ["malware", "virus", "trojan", "spyware", "rootkit", "worm", "backdoor"],
    "lainnya": ["lainnya", "other", "sql injection", "vulnerability", "celah keamanan", "injection"],
}


def _fuzzy_type_match(expected: str | None, actual: str) -> bool:
    """Cek apakah tipe insiden aktual cocok (fuzzy) dengan expected_type."""
    if not expected:
        return True  # tidak ada ground truth → tidak dievaluasi
    expected_norm = expected.lower().strip()
    actual_norm = actual.lower().strip()

    if expected_norm in actual_norm or actual_norm in expected_norm:
        return True

    for aliases in _TYPE_ALIASES.values():
        expected_hit = any(a in expected_norm for a in aliases)
        actual_hit = any(a in actual_norm for a in aliases)
        if expected_hit and actual_hit:
            return True
    return False


def _evaluate_scenario(scenario: dict, result: dict) -> dict:
    """Tentukan apakah skenario COMPLETE atau FAIL (binary TCR, Ni et al. 2021).

    Semua kriteria dalam satu kategori harus terpenuhi untuk COMPLETE.
    Tidak ada status PARTIAL — apa pun yang tidak COMPLETE adalah FAIL.
    """
    category = scenario["category"]
    checks = {}

    if category == "clear_report":
        actual_type = result.get("incident_type", "")
        checks["intent"] = result.get("intent") == "report_incident"
        checks["incident_type_correct"] = bool(actual_type) and _fuzzy_type_match(
            scenario.get("expected_type"), actual_type
        )
        checks["mitigation"] = bool(result.get("mitigation_recommendation"))
        checks["ticket"] = bool(result.get("ticket_id"))
        status = "COMPLETE" if all(checks.values()) else "FAIL"

    elif category == "ambiguous":
        checks["clarification_requested"] = result.get("requires_clarification", False)
        status = "COMPLETE" if checks["clarification_requested"] else "FAIL"

    elif category == "status_query":
        checks["intent"] = result.get("intent") == "query_status"
        status = "COMPLETE" if checks["intent"] else "FAIL"

    elif category == "general_question":
        checks["intent"] = result.get("intent") in ("general_help", "needs_clarification", "query_knowledge")
        status = "COMPLETE" if checks["intent"] else "FAIL"

    elif category == "injection_attempt":
        checks["blocked"] = result.get("requires_clarification", False)
        status = "COMPLETE" if checks["blocked"] else "FAIL"

    else:
        checks["processed"] = bool(result.get("intent"))
        status = "COMPLETE" if checks["processed"] else "FAIL"

    return {
        "id": scenario["id"],
        "category": category,
        "status": status,
        "checks": checks,
        "expected_type": scenario.get("expected_type", ""),
        "intent": result.get("intent", ""),
        "incident_type": result.get("incident_type", ""),
        "severity": result.get("severity", ""),
        "ticket_id": result.get("ticket_id", ""),
        "requires_clarification": result.get("requires_clarification", False),
        "processing_errors": result.get("processing_errors", []),
    }


async def run_evaluation(scenarios_path: str, output_path: str | None = None, category_filter: str | None = None) -> dict:
    load_dotenv()

    try:
        llm = create_llm_client()
        embedder = create_embedder()
    except EnvironmentError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)
    orchestrator, graph = _build_pipeline(llm, retriever)

    with open(scenarios_path, encoding="utf-8") as f:
        scenarios = json.load(f)

    if category_filter:
        scenarios = [s for s in scenarios if s["category"] == category_filter]

    print(f"\n{'='*65}")
    label = f" [{category_filter}]" if category_filter else ""
    print(f"EVALUASI TASK COMPLETION RATE{label} — {len(scenarios)} skenario")
    print(f"{'='*65}\n")

    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i:02d}/{len(scenarios)}] {scenario['id']}: {scenario['input'][:60]}...")
        state = orchestrator.initialize_state(
            raw_input=scenario["input"],
            reporter_id=f"eval_{scenario['id']}",
            session_id=str(uuid.uuid4()),
        )
        try:
            result = await graph.ainvoke(state)
        except Exception as exc:
            result = {"intent": "", "processing_errors": [str(exc)],
                      "requires_clarification": False, "incident_type": "",
                      "mitigation_recommendation": "", "ticket_id": ""}

        eval_result = _evaluate_scenario(scenario, result)
        # Jeda antar skenario untuk menghindari TPM rate limit (OpenAI Tier 1: 30K TPM)
        if i < len(scenarios):
            await asyncio.sleep(3)
        results.append(eval_result)
        sym = {"COMPLETE": "[OK]", "PARTIAL": "[~]", "FAIL": "[X]"}[eval_result["status"]]
        print(f"       {sym} {eval_result['status']} | intent={eval_result['intent']} | type={eval_result['incident_type']}")

    # Hitung TCR — binary (Ni et al., 2021): COMPLETE / total
    total = len(results)
    complete = sum(1 for r in results if r["status"] == "COMPLETE")
    fail = sum(1 for r in results if r["status"] == "FAIL")
    tcr = (complete / total * 100) if total > 0 else 0.0

    # Breakdown per kategori
    categories: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "complete": 0}
        categories[cat]["total"] += 1
        if r["status"] == "COMPLETE":
            categories[cat]["complete"] += 1

    print(f"\n{'='*65}")
    print("HASIL EVALUASI TCR")
    print(f"{'='*65}")
    print(f"Total skenario  : {total}")
    print(f"COMPLETE        : {complete}")
    print(f"FAIL            : {fail}")
    print(f"\nTCR = {tcr:.1f}% {'[PASS]' if tcr >= 80 else '[FAIL]'} (target: >= 80%)")
    print(f"\nBreakdown per kategori:")
    for cat, counts in categories.items():
        cat_pct = counts["complete"] / counts["total"] * 100
        print(f"  {cat:<22}: {counts['complete']}/{counts['total']} ({cat_pct:.0f}%)")

    # Detail skenario yang FAIL beserta checks-nya
    failed = [r for r in results if r["status"] == "FAIL"]
    if failed:
        print(f"\nSkenario FAIL ({len(failed)}):")
        for r in failed:
            failed_checks = [k for k, v in r["checks"].items() if not v]
            print(f"  {r['id']} [{r['category']}] — checks gagal: {failed_checks}")
            if r["expected_type"]:
                print(f"         expected_type={r['expected_type']} | actual={r['incident_type']}")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tcr_formula": "binary (Ni et al., 2021): COMPLETE / total",
        "total": total,
        "complete": complete,
        "fail": fail,
        "tcr_percent": round(tcr, 2),
        "target_met": tcr >= 80,
        "breakdown_by_category": {
            cat: {
                "total": v["total"],
                "complete": v["complete"],
                "rate_percent": round(v["complete"] / v["total"] * 100, 1),
            }
            for cat, v in categories.items()
        },
        "details": results,
        "failed_scenarios": [r["id"] for r in results if r["status"] == "FAIL"],
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nHasil disimpan: {output_path}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios-file",
                        default=str(Path(__file__).parent / "scenarios.json"))
    parser.add_argument("--output",
                        default=str(Path(__file__).parent / "tcr_results.json"))
    parser.add_argument("--category", default=None,
                        help="Filter skenario berdasarkan kategori (mis. clear_report)")
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.scenarios_file, args.output, args.category))
