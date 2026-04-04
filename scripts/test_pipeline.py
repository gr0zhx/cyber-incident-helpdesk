"""Script uji manual pipeline end-to-end (tanpa Telegram, tanpa guardrails).

Penggunaan:
    python scripts/test_pipeline.py "Saya menerima email phishing dari CEO meminta transfer"
    python scripts/test_pipeline.py "Ada yang aneh di komputer saya"
    python scripts/test_pipeline.py "Status tiket TICKET-2026-0001"

Memerlukan variabel lingkungan:
    OPENAI_API_KEY, QDRANT_URL (opsional), QDRANT_API_KEY (opsional)
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from qdrant_client import QdrantClient

from app.agents.graph import build_helpdesk_graph
from app.agents.identifier import IncidentIdentifierAgent
from app.agents.mitigation import MitigationAdvisorAgent
from app.agents.notifier import NotifierAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.ticket_manager import TicketManagerAgent
from app.database.connection import get_db
from app.database.repository import TicketRepository
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank


def _check_env() -> None:
    missing = [k for k in ("OPENAI_API_KEY",) if not os.getenv(k)]
    if missing:
        print(f"[ERROR] Variabel lingkungan tidak ditemukan: {', '.join(missing)}")
        sys.exit(1)


async def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    raw_input = sys.argv[1]
    load_dotenv()
    _check_env()

    print(f"\n{'='*65}")
    print(f"INPUT: {raw_input}")
    print(f"{'='*65}\n")

    # --- Init klien ---
    llm = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    embedder = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)

    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)

    # --- Init agen ---
    orchestrator = OrchestratorAgent(llm_client=llm)
    identifier = IncidentIdentifierAgent(llm_client=llm)
    mitigation_advisor = MitigationAdvisorAgent(
        llm_client=llm, retriever=retriever, reranker_fn=rerank
    )
    notifier = NotifierAgent(telegram_client=None)  # log only

    # TicketManager butuh DB — jika tidak ada, gunakan mock
    try:
        db_gen = get_db()
        db = next(db_gen)
        ticket_manager = TicketManagerAgent(TicketRepository(db))
        print("[DB] Menggunakan PostgreSQL")
    except Exception as exc:
        print(f"[DB] Tidak bisa konek DB ({exc.__class__.__name__}), pakai mock ticket manager")
        from unittest.mock import MagicMock
        mock_ticket = MagicMock()
        mock_ticket.ticket_id = "TICKET-MOCK-0001"
        mock_ticket.status = "PENDING_REVIEW"
        mock_ticket.escalation_level = "Standar"
        repo = MagicMock()
        repo.check_duplicate.return_value = None
        repo.create_ticket.return_value = mock_ticket
        ticket_manager = TicketManagerAgent(repo)

    # --- Build graf ---
    graph = build_helpdesk_graph(
        orchestrator=orchestrator,
        identifier=identifier,
        mitigation_advisor=mitigation_advisor,
        ticket_manager=ticket_manager,
        notifier=notifier,
    )

    # --- Inisialisasi state ---
    state = orchestrator.initialize_state(
        raw_input=raw_input,
        reporter_id="test_user_001",
        reporter_name="Test User",
        reporter_contact="@test",
        session_id="test_session",
    )

    print("Menjalankan pipeline...")
    result = await graph.ainvoke(state)

    # --- Output ringkasan ---
    print(f"\n{'='*65}")
    print("HASIL PIPELINE")
    print(f"{'='*65}")
    print(f"Intent          : {result.get('intent', '-')}")
    print(f"Klarifikasi     : {result.get('requires_clarification', False)}")
    if result.get("clarification_message"):
        print(f"Pesan           : {result['clarification_message']}")
    print(f"Jenis Insiden   : {result.get('incident_type', '-')}")
    print(f"Severity        : {result.get('severity', '-')}")
    print(f"Confidence      : {result.get('confidence_score', 0.0):.2f}")
    print(f"RAG Confidence  : {result.get('rag_confidence', 0.0):.3f}")
    print(f"Ticket ID       : {result.get('ticket_id', '-')}")
    print(f"Ticket Status   : {result.get('ticket_status', '-')}")
    print(f"Eskalasi        : {result.get('escalation_level', '-')}")
    print(f"Notifikasi      : {result.get('notification_sent', False)}")
    print(f"\nRekomendasi Mitigasi:\n{result.get('mitigation_recommendation', '-')}")
    print(f"\nSitasi ({len(result.get('citations', []))}):")
    for c in result.get("citations", []):
        print(f"  - {c.get('source', '')}")
    print(f"\nAgent Trace ({len(result.get('agent_trace', []))}):")
    for t in result.get("agent_trace", []):
        print(f"  [{t['status']}] {t['agent']} @ {t['timestamp'][:19]}")
    if result.get("processing_errors"):
        print(f"\nErrors: {result['processing_errors']}")


if __name__ == "__main__":
    asyncio.run(main())
