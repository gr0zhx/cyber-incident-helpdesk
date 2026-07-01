"""Routes untuk inbox tiket admin."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.constants import ESCALATION_LEVELS, TICKET_STATUSES
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.ticket_service import TicketFilters, TicketService

router = APIRouter(prefix="/admin", tags=["admin-inbox"])
templates = Jinja2Templates(directory="app/web/templates")


def _build_filters(
    status: Optional[str], severity: Optional[str], search: Optional[str]
) -> TicketFilters:
    return TicketFilters(
        status=status or None,
        severity=severity or None,
        search=search or None,
    )


@router.get("/inbox", response_class=HTMLResponse)
def inbox_page(
    request: Request,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    filters = _build_filters(status, severity, search)
    service = TicketService(db)
    result = service.list_tickets(filters, page=page, page_size=25)
    return templates.TemplateResponse(
        "admin/inbox.html",
        {
            "request": request,
            "result": result,
            "filters": filters,
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
    page: int = Query(1, ge=1),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    filters = _build_filters(status, severity, search)
    service = TicketService(db)
    result = service.list_tickets(filters, page=page, page_size=25)
    return templates.TemplateResponse(
        "admin/_inbox_table.html",
        {"request": request, "result": result, "filters": filters},
    )


@router.get("/inbox/stats", response_class=HTMLResponse)
def inbox_stats_fragment(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    service = TicketService(db)
    result = service.list_tickets(TicketFilters(), page=1, page_size=1)
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
    attachments = ticket.evidence_files or []
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
        },
    )
