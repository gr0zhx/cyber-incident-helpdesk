"""FastAPI dependency injection — pipeline & DB."""
import os
from functools import lru_cache
from typing import Generator

from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.agents.graph import build_helpdesk_graph
from app.agents.identifier import IncidentIdentifierAgent
from app.agents.mitigation import MitigationAdvisorAgent
from app.agents.notifier import NotifierAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.ticket_manager import TicketManagerAgent
from app.database.connection import get_db as _get_db
from app.database.repository import AuditRepository, TicketRepository
from app.rag.retriever import HybridRetriever
from app.rag.reranker import rerank
from app.utils.llm_client import create_embedder, create_llm_client


@lru_cache
def _build_pipeline():
    """Inisialisasi pipeline sekali saat startup (singleton)."""
    llm = create_llm_client()
    embedder = create_embedder()
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    retriever = HybridRetriever(qdrant_client=qdrant, embedder=embedder)

    orchestrator = OrchestratorAgent(llm_client=llm)
    identifier = IncidentIdentifierAgent(llm_client=llm)
    mitigation_advisor = MitigationAdvisorAgent(
        llm_client=llm, retriever=retriever, reranker_fn=rerank
    )
    notifier = NotifierAgent(telegram_client=None)  # log-only di API mode

    return orchestrator, identifier, mitigation_advisor, notifier


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_orchestrator() -> OrchestratorAgent:
    return _build_pipeline()[0]


def get_helpdesk_graph(db: Session):
    orchestrator, identifier, mitigation_advisor, notifier = _build_pipeline()
    ticket_repo = TicketRepository(db)
    ticket_manager = TicketManagerAgent(ticket_repo)
    return build_helpdesk_graph(
        orchestrator=orchestrator,
        identifier=identifier,
        mitigation_advisor=mitigation_advisor,
        ticket_manager=ticket_manager,
        notifier=notifier,
    )
