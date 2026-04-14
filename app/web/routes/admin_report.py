"""Routes generate laporan insiden."""
import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.report_service import ReportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/report", tags=["admin-report"])
templates = Jinja2Templates(directory="app/web/templates")


@router.get("", response_class=HTMLResponse)
def report_page(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    return templates.TemplateResponse(
        "admin/report.html",
        {
            "request": request,
            "csrf_token": request.session.get("csrf_token", ""),
            "admin": admin,
            "error": None,
        },
    )


@router.post("/generate", response_class=HTMLResponse)
def generate_report(
    request: Request,
    ticket_id: str = Form(...),
    prepared_by: str = Form("Tim Keamanan Siber Pusdatin"),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    svc = ReportService(db)
    try:
        html, filename = svc.generate(ticket_id.strip(), prepared_by=prepared_by.strip())
    except LookupError:
        return templates.TemplateResponse(
            "admin/report.html",
            {
                "request": request,
                "csrf_token": request.session.get("csrf_token", ""),
                "admin": admin,
                "error": f"Tiket '{ticket_id}' tidak ditemukan.",
            },
        )
    logger.info("REPORT_GENERATED admin=%s ticket=%s", admin.username, ticket_id)
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
