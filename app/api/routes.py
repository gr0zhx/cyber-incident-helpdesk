"""FastAPI route handlers untuk helpdesk API."""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_helpdesk_graph, get_orchestrator
from app.api.schemas import (
    HealthResponse, ReportRequest, ReportResponse,
    StatsResponse, TicketOut, TicketUpdateRequest,
)
from app.database.models import IncidentTicket
from app.database.repository import TicketRepository
from app.agents.orchestrator import OrchestratorAgent
from app.telegram.templates import format_status_update

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
        session_existing_ticket=body.session_existing_ticket,
    )

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.exception("Pipeline error saat memproses laporan: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"[{session_id[:8]}] Terjadi kesalahan internal. Coba lagi.",
        )

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


@router.get("/tickets/stats", response_model=StatsResponse)
def get_ticket_stats(
    db: Annotated[Session, Depends(get_db)],
) -> StatsResponse:
    """Statistik ringkasan tiket untuk dashboard admin."""
    repo = TicketRepository(db)
    return StatsResponse(**repo.get_stats())


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


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: str,
    body: TicketUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TicketOut:
    """Update status/assignment tiket dan (opsional) kirim notifikasi ke pelapor."""
    repo = TicketRepository(db)
    ticket = repo.get_ticket_by_id(ticket_id.upper())
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Tiket {ticket_id} tidak ditemukan.")

    updates: dict = {}
    if body.status is not None:
        updates["status"] = body.status
    if body.assigned_to is not None:
        updates["assigned_to"] = body.assigned_to
    if body.escalation_level is not None:
        updates["escalation_level"] = body.escalation_level

    if not updates:
        raise HTTPException(status_code=422, detail="Tidak ada field yang diupdate.")

    updated = repo.update_ticket(ticket_id.upper(), updates)
    if updated is None:
        raise HTTPException(status_code=500, detail="Gagal memperbarui tiket.")

    # Kirim notifikasi Telegram ke pelapor jika diminta
    if body.notify_reporter and body.status and updated.reporter_id:
        await _notify_reporter_status(
            reporter_id=updated.reporter_id,
            ticket_id=updated.ticket_id,
            new_status=updated.status,
        )

    return TicketOut.model_validate(updated)


async def _notify_reporter_status(reporter_id: str, ticket_id: str, new_status: str) -> None:
    """Kirim pesan Telegram ke pelapor saat status tiket berubah."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN tidak ada, notifikasi status dilewati.")
        return
    try:
        from telegram import Bot
        message = format_status_update(
            ticket_id=ticket_id,
            new_status=new_status,
            updated_at=datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        )
        chat_id = reporter_id.removeprefix("tg:")
        bot = Bot(token=token)
        async with bot:
            await bot.send_message(chat_id=chat_id, text=message)
        logger.info("Notifikasi status dikirim ke reporter %s (tiket %s)", reporter_id, ticket_id)
    except Exception as exc:
        logger.warning("Gagal kirim notifikasi status ke %s: %s", reporter_id, exc)


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
