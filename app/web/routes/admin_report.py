"""Routes generate laporan insiden."""
import html
import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.report_service import ReportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/report", tags=["admin-report"])


@router.get("", response_class=HTMLResponse)
def report_page():
    return RedirectResponse(url="/admin/inbox", status_code=302)


@router.post("/generate", response_class=HTMLResponse)
def generate_report(
    ticket_id: str = Form(...),
    prepared_by: str = Form("Tim Keamanan Siber Pusdatin"),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    svc = ReportService(db)
    try:
        report_html, filename = svc.generate(ticket_id.strip(), prepared_by=prepared_by.strip())
    except LookupError:
        logger.warning("REPORT_NOT_FOUND ticket=%s admin=%s", ticket_id, admin.username)
        return HTMLResponse(
            content=f"<p>Tiket '<strong>{html.escape(ticket_id)}</strong>' tidak ditemukan.</p>",
            status_code=404,
        )
    logger.info("REPORT_GENERATED admin=%s ticket=%s", admin.username, ticket_id)
    return HTMLResponse(
        content=report_html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
