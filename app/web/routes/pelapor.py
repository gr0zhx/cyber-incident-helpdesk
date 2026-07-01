"""Routes untuk alur pelapor: identitas -> chat -> status tiket."""
import logging
import os
import re
import uuid

import markdown as _md

import redis as _redis_lib
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.dependencies import get_helpdesk_graph, get_orchestrator
from app.database.models import IncidentTicket
from app.web.dependencies import get_db_session, get_reporter_session
from app.web.middleware.rate_limit import limiter
from app.web.services.chat_service import ChatService
from app.web.services.upload_service import UploadError, UploadService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lapor", tags=["pelapor"])
templates = Jinja2Templates(directory="app/web/templates")


def _render_md(text: str) -> str:
    """Convert LLM markdown output to HTML. Normalises lists that lack a preceding blank line."""
    t = str(text)
    # Ensure blank line before list blocks so markdown detects them
    t = re.sub(r'([^\n])\n([ \t]*[-*][ \t])', r'\1\n\n\2', t)
    t = re.sub(r'([^\n])\n([ \t]*\d+\.[ \t])', r'\1\n\n\2', t)
    html = _md.markdown(t)
    # Strip <p> wrappers inside <li> (loose → tight list rendering)
    html = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', html, flags=re.DOTALL)
    return html


templates.env.filters["render_md"] = _render_md


def _redis_client():
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return _redis_lib.from_url(url, decode_responses=False)


def _get_graph(db: Session):
    return get_helpdesk_graph(db)


def _get_orch():
    return get_orchestrator()


@router.get("", response_class=HTMLResponse)
def identitas_form(request: Request):
    return templates.TemplateResponse(
        "pelapor/identitas.html",
        {"request": request, "csrf_token": request.session.get("csrf_token", ""), "error": None},
    )


@router.post("", response_class=HTMLResponse)
async def identitas_submit(
    request: Request,
    reporter_name: str = Form(...),
    reporter_contact: str = Form(""),
    reporter_unit: str = Form(""),
    db: Session = Depends(get_db_session),
):
    reporter_name = reporter_name.strip()
    reporter_contact = reporter_contact.strip()
    reporter_unit = reporter_unit.strip()

    if not reporter_name:
        return templates.TemplateResponse(
            "pelapor/identitas.html",
            {"request": request, "csrf_token": request.session.get("csrf_token", ""),
             "error": "Nama tidak boleh kosong."},
        )
    session_id = str(uuid.uuid4())
    request.session["session_id"] = session_id
    request.session["reporter_id"] = f"web:{session_id}"
    request.session["reporter_name"] = reporter_name
    request.session["reporter_contact"] = reporter_contact
    request.session["reporter_unit"] = reporter_unit
    return RedirectResponse(url="/lapor/chat", status_code=303)


@router.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
):
    svc = ChatService(redis=_redis_client())
    history = svc.get_history(reporter["session_id"])
    return templates.TemplateResponse(
        "pelapor/chat.html",
        {
            "request": request,
            "reporter": reporter,
            "history": history,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.post("/chat/message", response_class=HTMLResponse)
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    text: str = Form(...),
    reporter: dict = Depends(get_reporter_session),
    db: Session = Depends(get_db_session),
):
    text = text.strip()
    if not text:
        return HTMLResponse("")

    svc = ChatService(redis=_redis_client())
    graph = _get_graph(db)
    orchestrator = _get_orch()

    result = await svc.handle_message(
        session_id=reporter["session_id"],
        reporter_id=reporter["reporter_id"],
        reporter_name=reporter["reporter_name"],
        reporter_contact=reporter["reporter_contact"],
        text=text,
        graph=graph,
        orchestrator=orchestrator,
        db=db,
    )

    if result.get("error"):
        return templates.TemplateResponse(
            "pelapor/_error_bubble.html",
            {"request": request, "trace_id": result.get("trace_id", "")},
        )

    return templates.TemplateResponse(
        "pelapor/_message.html",
        {"request": request, **result},
    )


@router.post("/chat/upload", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
):
    form = await request.form()
    file_field = form.get("file")
    if file_field is None:
        return HTMLResponse('<p style="color: #dc2626; font-size: 13px;">Tidak ada file dipilih.</p>')

    filename = file_field.filename or "upload"
    data = await file_field.read()
    upload_svc = UploadService(redis=_redis_client(), upload_root="web_uploads")
    try:
        meta = upload_svc.save_pending(
            session_id=reporter["session_id"],
            filename=filename,
            data=data,
        )
    except UploadError as exc:
        return HTMLResponse(f'<p style="color: #dc2626; font-size: 13px;">{_html.escape(str(exc))}</p>')

    size_kb = meta["size_bytes"] // 1024
    return templates.TemplateResponse(
        "pelapor/_attachment_pill.html",
        {"request": request, "filename": filename, "size_kb": size_kb},
    )


@router.post("/chat/reset", response_class=HTMLResponse)
def reset_session(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
):
    svc = ChatService(redis=_redis_client())
    svc.clear_history(reporter["session_id"])
    request.session.clear()
    # If request is from HTMX, perform an HTMX redirect (HX-Redirect header).
    # Otherwise return a normal HTTP redirect so tests and non-HTMX clients
    # receive a 303 redirect as expected.
    is_hx = str(request.headers.get("HX-Request", "")).lower() == "true"
    if is_hx:
        response = HTMLResponse("", status_code=200)
        response.headers["HX-Redirect"] = "/lapor"
        return response

    return RedirectResponse(url="/lapor", status_code=303)


@router.get("/tiket/{ticket_id}", response_class=HTMLResponse)
def ticket_status(
    request: Request,
    ticket_id: str,
    reporter: dict = Depends(get_reporter_session),
    db: Session = Depends(get_db_session),
):
    ticket = db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan.")
    if ticket.reporter_id != reporter["reporter_id"]:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
    return templates.TemplateResponse(
        "pelapor/tiket_detail.html",
        {"request": request, "ticket": ticket},
    )
