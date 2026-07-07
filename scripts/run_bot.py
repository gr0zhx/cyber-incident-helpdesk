"""Entry point untuk menjalankan bot Telegram helpdesk.

Penggunaan:
    python scripts/run_bot.py

Memerlukan variabel lingkungan:
    TELEGRAM_BOT_TOKEN   — wajib
    OPENAI_API_KEY       — wajib
    QDRANT_URL           — opsional (default: http://localhost:6333)
    QDRANT_API_KEY       — opsional
    CSIRT_CHAT_ID        — opsional (ID grup Telegram untuk notifikasi CSIRT)
    DATABASE_URL         — opsional (untuk fitur /status)
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
from app.telegram.bot import build_bot_application
from app.utils.llm_client import create_embedder, create_llm_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_notifier(telegram_bot) -> NotifierAgent:
    """NotifierAgent log-only untuk pipeline bot Telegram.

    app/telegram/bot.py::_send_result sudah mengirim konfirmasi ke pelapor
    (reply_text) dan alert ke grup CSIRT (context.bot.send_message) untuk
    channel ini. Memberi telegram_client asli di sini akan membuat node
    send_notification di graph JUGA mengirim pesan Telegram — setiap laporan
    jadi terkirim dua kali ke pelapor maupun grup CSIRT.
    """
    return NotifierAgent(telegram_client=None)


def _check_env() -> None:
    missing = []
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        missing.append("TELEGRAM_BOT_TOKEN")
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GITHUB_TOKEN"):
        missing.append("OPENAI_API_KEY atau GITHUB_TOKEN")
    if missing:
        logger.error("Variabel lingkungan tidak ditemukan: %s", ", ".join(missing))
        sys.exit(1)


def main() -> None:
    load_dotenv()
    _check_env()

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    llm = create_llm_client()
    embedder = create_embedder()
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)

    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)

    orchestrator = OrchestratorAgent(llm_client=llm)
    identifier = IncidentIdentifierAgent(llm_client=llm)
    mitigation_advisor = MitigationAdvisorAgent(
        llm_client=llm, retriever=retriever, reranker_fn=rerank
    )

    # Telegram notifier — gunakan token yang sama
    from telegram import Bot as TelegramBot
    telegram_bot = TelegramBot(token=token)
    notifier = _build_notifier(telegram_bot)

    # TicketManager — coba DB, fallback ke mock
    ticket_repository = None
    try:
        from app.database.connection import get_db
        from app.database.repository import TicketRepository
        db_gen = get_db()
        db = next(db_gen)
        ticket_repository = TicketRepository(db)
        ticket_manager = TicketManagerAgent(ticket_repository)
        logger.info("Menggunakan PostgreSQL untuk tiket")
    except Exception as exc:
        logger.warning("DB tidak tersedia (%s), pakai mock ticket manager", exc.__class__.__name__)
        from unittest.mock import MagicMock
        mock_ticket = MagicMock()
        mock_ticket.ticket_id = "TICKET-MOCK-0001"
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

    bot_app = build_bot_application(
        token=token,
        helpdesk_graph=graph,
        orchestrator=orchestrator,
        ticket_repository=ticket_repository,
    )

    logger.info("Bot Telegram helpdesk siap berjalan...")
    bot_app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
