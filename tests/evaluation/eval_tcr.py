"""Evaluasi Task Completion Rate (TCR) untuk pipeline helpdesk.

Penggunaan:
    python tests/evaluation/eval_tcr.py
    python tests/evaluation/eval_tcr.py --scenarios-file tests/evaluation/scenarios.json
    python tests/evaluation/eval_tcr.py --output results/tcr_results.json

Memerlukan:
    OPENAI_API_KEY, QDRANT_URL (opsional)

Definisi COMPLETE:
    Skenario clear_report  → incident_type terisi + mitigation terisi + ticket_id terbuat
    Skenario ambiguous      → requires_clarification=True
    Skenario status_query   → intent=query_status
    Skenario general_q      → intent=general_help
    Skenario injection      → requires_clarification=True (ditolak guardrails)
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


def _evaluate_scenario(scenario: dict, result: dict) -> dict:
    """Tentukan apakah skenario COMPLETE, PARTIAL, atau FAIL."""
    category = scenario["category"]
    checks = {}

    if category == "clear_report":
        checks["intent"] = result.get("intent") == "report_incident"
        checks["incident_type"] = bool(result.get("incident_type"))
        checks["mitigation"] = bool(result.get("mitigation_recommendation"))
        checks["ticket"] = bool(result.get("ticket_id"))
        passed = sum(checks.values())
        if passed == 4:
            status = "COMPLETE"
        elif passed >= 2:
            status = "PARTIAL"
        else:
            status = "FAIL"

    elif category == "ambiguous":
        checks["clarification_requested"] = result.get("requires_clarification", False)
        status = "COMPLETE" if checks["clarification_requested"] else "FAIL"

    elif category == "status_query":
        checks["intent"] = result.get("intent") == "query_status"
        status = "COMPLETE" if checks["intent"] else "PARTIAL"

    elif category == "general_question":
        checks["intent"] = result.get("intent") in ("general_help", "needs_clarification")
        status = "COMPLETE" if checks["intent"] else "FAIL"

    elif category == "injection_attempt":
        checks["blocked"] = result.get("requires_clarification", False)
        status = "COMPLETE" if checks["blocked"] else "FAIL"

    else:
        checks["processed"] = result.get("intent") != ""
        status = "COMPLETE" if checks["processed"] else "FAIL"

    return {
        "id": scenario["id"],
        "category": category,
        "status": status,
        "checks": checks,
        "intent": result.get("intent", ""),
        "incident_type": result.get("incident_type", ""),
        "severity": result.get("severity", ""),
        "ticket_id": result.get("ticket_id", ""),
        "requires_clarification": result.get("requires_clarification", False),
        "processing_errors": result.get("processing_errors", []),
    }


async def run_evaluation(scenarios_path: str, output_path: str | None = None) -> dict:
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

    print(f"\n{'='*65}")
    print(f"EVALUASI TASK COMPLETION RATE — {len(scenarios)} skenario")
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
        results.append(eval_result)
        sym = {"COMPLETE": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}[eval_result["status"]]
        print(f"       {sym} {eval_result['status']} | intent={eval_result['intent']} | type={eval_result['incident_type']}")

    # Hitung TCR
    total = len(results)
    complete = sum(1 for r in results if r["status"] == "COMPLETE")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    fail = sum(1 for r in results if r["status"] == "FAIL")
    tcr = (complete / total * 100) if total > 0 else 0.0

    # Breakdown per kategori
    categories = {}
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
    print(f"Total skenario : {total}")
    print(f"Berhasil lengkap: {complete}")
    print(f"Parsial        : {partial}")
    print(f"Gagal          : {fail}")
    print(f"\nTCR = {tcr:.1f}% {'✅' if tcr >= 80 else '❌'} (target: ≥ 80%)")
    print(f"\nBreakdown per kategori:")
    for cat, counts in categories.items():
        cat_pct = counts["complete"] / counts["total"] * 100
        print(f"  {cat:<20}: {counts['complete']}/{counts['total']} ({cat_pct:.0f}%)")

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "complete": complete,
        "partial": partial,
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
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.scenarios_file, args.output))
