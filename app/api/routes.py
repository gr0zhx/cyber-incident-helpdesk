"""FastAPI route handlers untuk helpdesk API."""
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_helpdesk_graph, get_orchestrator
from app.api.schemas import HealthResponse, ReportRequest, ReportResponse, TicketOut
from app.database.models import IncidentTicket
from app.database.repository import TicketRepository
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="helpdesk-api", pipeline_ready=True)


@router.post("/report", response_model=ReportResponse)
async def create_report(
    body: ReportRequest,
    db: Annotated[Session, Depends(get_db)],
    orchestrator: Annotated[OrchestratorAgent, Depends(get_orchestrator)],
) -> ReportResponse:
    """Terima laporan insiden dan proses melalui pipeline multi-agent.

    Menjalankan: guardrails → klasifikasi intent → identifikasi insiden →
    rekomendasi mitigasi → pembuatan tiket → notifikasi.
    """
    session_id = body.session_id or str(uuid.uuid4())

    graph = get_helpdesk_graph(db)
    state = orchestrator.initialize_state(
        raw_input=body.raw_input,
        reporter_id=body.reporter_id,
        reporter_name=body.reporter_name,
        reporter_contact=body.reporter_contact,
        session_id=session_id,
    )

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.exception("Pipeline error saat memproses laporan: %s", exc)
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal. Coba lagi.")

    citations = [
        {"source": c.get("source", ""), "section": c.get("section", ""),
         "content_preview": c.get("content", "")[:200]}
        for c in result.get("citations", [])
    ]

    return ReportResponse(
        ticket_id=result.get("ticket_id", ""),
        ticket_status=result.get("ticket_status", ""),
        intent=result.get("intent", ""),
        incident_type=result.get("incident_type", ""),
        severity=result.get("severity", ""),
        confidence_score=result.get("confidence_score", 0.0),
        escalation_level=result.get("escalation_level", ""),
        mitigation_recommendation=result.get("mitigation_recommendation", ""),
        citations=citations,
        rag_confidence=result.get("rag_confidence", 0.0),
        requires_clarification=result.get("requires_clarification", False),
        clarification_message=result.get("clarification_message", ""),
        notification_sent=result.get("notification_sent", False),
        processing_errors=result.get("processing_errors", []),
    )


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> TicketOut:
    """Ambil detail satu tiket berdasarkan ticket_id."""
    repo = TicketRepository(db)
    ticket = repo.get_ticket_by_id(ticket_id.upper())
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Tiket {ticket_id} tidak ditemukan.")
    return TicketOut.model_validate(ticket)


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    db: Annotated[Session, Depends(get_db)],
    reporter_id: Annotated[str | None, Query(description="Filter berdasarkan reporter_id")] = None,
) -> list[TicketOut]:
    """Daftar tiket. Filter opsional berdasarkan reporter_id."""
    repo = TicketRepository(db)
    if reporter_id:
        tickets = repo.get_tickets_by_reporter(reporter_id)
    else:
        # Ambil semua — batasi 100 untuk prototipe
        tickets = (
            db.query(IncidentTicket)
            .order_by(IncidentTicket.created_at.desc())
            .limit(100)
            .all()
        )
    return [TicketOut.model_validate(t) for t in tickets]
