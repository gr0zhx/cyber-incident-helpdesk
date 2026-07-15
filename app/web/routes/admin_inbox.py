"""Routes untuk inbox tiket admin."""
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin, TicketAttachment
from app.web.constants import ESCALATION_LEVELS, TICKET_STATUSES
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.ticket_service import TicketFilters, TicketService
from app.utils.datetime_utils import format_input_time, format_system_wib

router = APIRouter(prefix="/admin", tags=["admin-inbox"])
templates = Jinja2Templates(directory="app/web/templates")
templates.env.filters["fmt_wib"] = format_system_wib
templates.env.filters["fmt_input_time"] = format_input_time


def _parse_date(value: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    if end_of_day:
        dt = datetime.combine(dt.date(), time.max)
    return dt.replace(tzinfo=timezone.utc)


def _build_filters(
    status: Optional[str],
    severity: Optional[str],
    search: Optional[str],
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> TicketFilters:
    return TicketFilters(
        status=status or None,
        severity=severity or None,
        search=search or None,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to, end_of_day=True),
    )


@router.get("/inbox", response_class=HTMLResponse)
def inbox_page(
    request: Request,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    filters = _build_filters(status, severity, search, date_from, date_to)
    service = TicketService(db)
    result = service.list_tickets(filters, page=page, page_size=25)
    return templates.TemplateResponse(
        "admin/inbox.html",
        {
            "request": request,
            "result": result,
            "filters": filters,
            "raw_filters": {"date_from": date_from or "", "date_to": date_to or ""},
            "statuses": TICKET_STATUSES,
            "csrf_token": request.session.get("csrf_token", ""),
            "admin": admin,
        },
    )


@router.get("/inbox/table", response_class=HTMLResponse)
def inbox_table_fragment(
    request: Request,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    filters = _build_filters(status, severity, search, date_from, date_to)
    service = TicketService(db)
    result = service.list_tickets(filters, page=page, page_size=25)
    return templates.TemplateResponse(
        "admin/_inbox_table.html",
        {
            "request": request,
            "result": result,
            "filters": filters,
            "raw_filters": {"date_from": date_from or "", "date_to": date_to or ""},
        },
    )


@router.get("/inbox/stats", response_class=HTMLResponse)
def inbox_stats_fragment(
    request: Request,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    filters = _build_filters(status, severity, search, date_from, date_to)
    service = TicketService(db)
    result = service.list_tickets(filters, page=1, page_size=1)
    return templates.TemplateResponse(
        "admin/_inbox_stats.html",
        {"request": request, "result": result},
    )


@router.get("/tiket/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(
    request: Request,
    ticket_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    ticket = TicketService(db).get_ticket_detail(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan.")
    attachments = (
        db.query(TicketAttachment)
        .filter_by(ticket_id=ticket_id)
        .order_by(TicketAttachment.id)
        .all()
    )
    admins = db.query(Admin).filter_by(is_active=True).order_by(Admin.full_name).all()
    return templates.TemplateResponse(
        "admin/tiket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "attachments": attachments,
            "statuses": TICKET_STATUSES,
            "escalation_levels": ESCALATION_LEVELS,
            "csrf_token": request.session.get("csrf_token", ""),
            "admin": admin,
            "admins": admins,
        },
    )


@router.get("/tiket/{ticket_id}/attachment/{att_id}")
def download_attachment(
    ticket_id: str,
    att_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    """Serve file lampiran tiket untuk admin."""
    att = db.query(TicketAttachment).filter_by(id=att_id, ticket_id=ticket_id).first()
    if att is None:
        raise HTTPException(status_code=404, detail="Lampiran tidak ditemukan.")
    path = Path(att.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan di server.")
    return FileResponse(
        path=path,
        media_type=att.mime_type,
        filename=att.original_filename,
    )
