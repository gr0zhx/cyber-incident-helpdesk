"""Routes HTMX untuk aksi update tiket admin."""
import html
import logging
import os

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.notification_service import NotificationService
from app.web.services.ticket_service import TicketService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/tiket", tags=["admin-actions"])
templates = Jinja2Templates(directory="app/web/templates")

UPLOAD_ROOT = os.path.abspath(os.environ.get("WEB_UPLOAD_DIR", "web_uploads"))


def _get_ticket_or_404(db: Session, ticket_id: str):
    ticket = TicketService(db).get_ticket_detail(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan.")
    return ticket


@router.post("/{ticket_id}/status", response_class=HTMLResponse)
def update_status(
    request: Request,
    ticket_id: str,
    status: str = Form(...),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    try:
        TicketService(db).update_status(ticket_id, status, modified_by=admin.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(ticket)
    logger.info(
        "TICKET_STATUS_UPDATED ticket=%s admin=%s new=%s",
        ticket_id, admin.username, status,
    )
    return templates.TemplateResponse(
        "admin/_status_badge.html",
        {"request": request, "ticket": ticket},
    )


@router.post("/{ticket_id}/assign", response_class=HTMLResponse)
def assign_ticket(
    request: Request,
    ticket_id: str,
    assignee: str = Form(...),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    _get_ticket_or_404(db, ticket_id)
    TicketService(db).assign(ticket_id, assignee.strip(), modified_by=admin.username)
    db.commit()
    logger.info(
        "TICKET_ASSIGNED ticket=%s admin=%s assignee=%s",
        ticket_id, admin.username, assignee,
    )
    return HTMLResponse(
        f'<p style="color: #16a34a; font-size: 13px; margin-top: 8px;">Ditugaskan ke <strong>{html.escape(assignee)}</strong></p>'
    )


@router.post("/{ticket_id}/escalation", response_class=HTMLResponse)
def set_escalation(
    request: Request,
    ticket_id: str,
    level: str = Form(...),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    _get_ticket_or_404(db, ticket_id)
    try:
        TicketService(db).set_escalation(ticket_id, level, modified_by=admin.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    logger.info(
        "TICKET_ESCALATION_UPDATED ticket=%s admin=%s level=%s",
        ticket_id, admin.username, level,
    )
    return HTMLResponse(
        f'<p style="color: #16a34a; font-size: 13px; margin-top: 8px;">Escalation diset ke <strong>{html.escape(level)}</strong></p>'
    )


@router.post("/{ticket_id}/notify", response_class=HTMLResponse)
async def notify_reporter(
    request: Request,
    ticket_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    service = NotificationService()
    ok = await service.notify_status(
        reporter_id=ticket.reporter_id,
        ticket_id=ticket.ticket_id,
        new_status=ticket.status,
    )
    logger.info(
        "NOTIFICATION_SENT ticket=%s admin=%s success=%s",
        ticket_id, admin.username, ok,
    )
    if ok:
        return HTMLResponse(
            '<p style="color: #16a34a; font-size: 13px; margin-top: 8px;">Notifikasi berhasil dikirim ke pelapor.</p>'
        )
    return HTMLResponse(
        '<p style="color: #dc2626; font-size: 13px; margin-top: 8px;">Notifikasi gagal (channel non-telegram atau error bot).</p>'
    )


@router.get("/{ticket_id}/attachment/{att_index}", response_class=FileResponse)
def download_attachment(
    ticket_id: str,
    att_index: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    files = ticket.evidence_files or []
    if att_index < 0 or att_index >= len(files):
        raise HTTPException(status_code=404, detail="Attachment tidak ditemukan.")
    entry = files[att_index]
    raw_path = entry.get("path", "")
    filename = entry.get("filename", "download.bin")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nama file tidak valid.")

    abs_path = os.path.abspath(raw_path)
    try:
        if os.path.commonpath([abs_path, UPLOAD_ROOT]) != UPLOAD_ROOT:
            raise HTTPException(status_code=400, detail="Path file di luar direktori upload.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Path file tidak valid.")
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="File fisik hilang.")

    logger.info(
        "FILE_DOWNLOADED ticket=%s admin=%s file=%s",
        ticket_id, admin.username, filename,
    )
    return FileResponse(
        abs_path,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
