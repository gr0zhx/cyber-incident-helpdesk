"""Routes untuk alur pelapor: identitas -> chat -> status tiket."""
import html as _html
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
    """Convert LLM markdown output to HTML with source citation block."""
    t = str(text)

    # Extract trailing "Sumber: ..." block before markdown processing
    src_match = re.search(r'\n*Sumber:\s*(.+)$', t, flags=re.DOTALL | re.IGNORECASE)
    if src_match:
        t = t[:src_match.start()].rstrip()
        sources_raw = src_match.group(1).strip()
        parts = re.split(r'\[(\d+)\]', sources_raw)

        def _base_label(lbl: str) -> str:
            """Strip trailing section refs like ', Bagian 2.a.4'."""
            stripped = re.sub(
                r',?\s*(bagian|pasal|lampiran|ayat|huruf|angka|poin[t]?|bab|butir|klausul|section|article|chapter)\b.*$',
                '', lbl, flags=re.IGNORECASE,
            ).strip().rstrip(',').strip()
            return stripped if stripped else lbl

        items = []
        seen_nums: set[str] = set()      # dedup by [N]
        seen_bases: set[str] = set()     # dedup same doc under different [N]
        for i in range(1, len(parts) - 1, 2):
            num = parts[i]
            raw_label = parts[i + 1].strip().lstrip('.,; ')
            if not raw_label or num in seen_nums:
                continue
            base = _base_label(raw_label)
            base_key = base.lower()
            if base_key in seen_bases:
                continue
            seen_nums.add(num)
            seen_bases.add(base_key)
            items.append(
                f'<li><span class="src-num">[{num}]</span>'
                f' {_html.escape(base)}</li>'
            )
        if items:
            sources_html = (
                '<div class="sources-block">'
                '<span class="sources-label">📎 Sumber</span>'
                f'<ul>{"".join(items)}</ul></div>'
            )
        else:
            sources_html = (
                '<div class="sources-block">'
                '<span class="sources-label">📎 Sumber</span>'
                f'<p>{_html.escape(sources_raw)}</p></div>'
            )
    else:
        sources_html = ''

    # Ensure blank line before list blocks so markdown detects them
    t = re.sub(r'([^\n])\n([ \t]*[-*][ \t])', r'\1\n\n\2', t)
    t = re.sub(r'([^\n])\n([ \t]*\d+\.[ \t])', r'\1\n\n\2', t)
    body = _md.markdown(t)
    # Strip <p> wrappers inside <li> (loose → tight list rendering)
    body = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', body, flags=re.DOTALL)
    return body + sources_html


templates.env.filters["render_md"] = _render_md


def _redis_client():
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return _redis_lib.from_url(url, decode_responses=False)


def _support_whatsapp_url() -> str:
    return os.getenv("CSIRT_WHATSAPP_URL", "https://wa.me/62822xxxxx")


def _support_phone_label() -> str:
    return os.getenv("CSIRT_PHONE_LABEL", "+62822xxxxx")


def _support_email() -> str:
    return os.getenv("CSIRT_EMAIL", "kamsiber@pusdatin.kementan.go.id")


def _normalize_contact(value: str) -> str:
    value = (value or "").strip().lower()
    if "@" in value:
        return re.sub(r"\s+", "", value)
    digits = re.sub(r"\D", "", value)
    if digits.startswith("62"):
        digits = "0" + digits[2:]
    return digits


def _render_identitas(
    request: Request,
    *,
    error: str | None = None,
    mode: str = "new",
):
    mode = mode if mode in {"new", "track"} else "new"
    return templates.TemplateResponse(
        "pelapor/identitas.html",
        {
            "request": request,
            "csrf_token": request.session.get("csrf_token", ""),
            "error": error,
            "mode": mode,
            "resume_link": request.session.get("reporter_resume_link", ""),
        },
    )


def _get_reporter_ticket_ids(
    reporter: dict,
    db: Session,
    *,
    redis_client=None,
) -> list[str]:
    access_token = reporter.get("reporter_access_token", "")
    if access_token:
        svc = ChatService(redis=redis_client or _redis_client())
        ticket_ids = svc.get_reporter_tickets(access_token)
        if ticket_ids:
            return ticket_ids

        db_ticket_ids = [
            ticket.ticket_id
            for ticket in (
                db.query(IncidentTicket)
                .filter_by(reporter_access_token=access_token)
                .order_by(IncidentTicket.created_at.desc())
                .all()
            )
        ]
        if db_ticket_ids:
            return db_ticket_ids

    tracked_ticket_id = reporter.get("reporter_tracked_ticket_id", "")
    if tracked_ticket_id:
        return [tracked_ticket_id]

    return []


def _get_graph(db: Session):
    return get_helpdesk_graph(db)


def _get_orch():
    return get_orchestrator()


@router.get("", response_class=HTMLResponse)
def identitas_form(request: Request):
    alert = request.query_params.get("alert", "")
    if alert == "session_invalid":
        return _render_identitas(
            request,
            mode=request.query_params.get("mode", "new"),
            error="Sesi Anda sudah tidak valid atau sudah habis. Silakan mulai lagi dari halaman ini.",
        )
    return _render_identitas(request, mode=request.query_params.get("mode", "new"))


@router.post("", response_class=HTMLResponse)
async def identitas_submit(
    request: Request,
    reporter_name: str = Form(...),
    reporter_contact: str = Form(""),
    reporter_unit: str = Form(""),
    incident_time: str = Form(""),
    affected_asset: str = Form(""),
    db: Session = Depends(get_db_session),
):
    reporter_name = reporter_name.strip()
    reporter_contact = reporter_contact.strip()
    reporter_unit = reporter_unit.strip()

    if not reporter_name:
        return _render_identitas(request, error="Nama tidak boleh kosong.", mode="new")
    if not reporter_unit:
        return _render_identitas(request, error="Unit / Divisi tidak boleh kosong.", mode="new")
    if not reporter_contact:
        return _render_identitas(request, error="Kontak tidak boleh kosong.", mode="new")
    session_id = str(uuid.uuid4())
    access_token = uuid.uuid4().hex + uuid.uuid4().hex
    request.session["session_id"] = session_id
    request.session["reporter_id"] = f"web:{session_id}"
    request.session["reporter_access_token"] = access_token
    request.session["reporter_tracked_ticket_id"] = ""
    request.session["reporter_resume_link"] = "/lapor/tiket-saya"
    request.session["reporter_name"] = reporter_name
    request.session["reporter_contact"] = reporter_contact
    request.session["reporter_unit"] = reporter_unit
    request.session["media_pelaporan"] = "Sistem Tiket"
    request.session["incident_time"] = incident_time.strip()
    request.session["affected_asset"] = affected_asset.strip()
    return RedirectResponse(url="/lapor/chat", status_code=303)


@router.post("/track", response_class=HTMLResponse)
def track_ticket(
    request: Request,
    ticket_id: str = Form(...),
    reporter_contact: str = Form(...),
    db: Session = Depends(get_db_session),
):
    ticket_id = ticket_id.strip()
    reporter_contact = reporter_contact.strip()
    if not ticket_id:
        return _render_identitas(request, error="Nomor tiket tidak boleh kosong.", mode="track")
    if not reporter_contact:
        return _render_identitas(request, error="Kontak verifikasi tidak boleh kosong.", mode="track")

    ticket = db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
    if ticket is None:
        return _render_identitas(request, error="Tiket tidak ditemukan.", mode="track")

    if _normalize_contact(ticket.reporter_contact or "") != _normalize_contact(reporter_contact):
        return _render_identitas(
            request,
            error="Kontak verifikasi tidak cocok dengan tiket tersebut.",
            mode="track",
        )

    request.session["session_id"] = str(uuid.uuid4())
    request.session["reporter_id"] = ticket.reporter_id
    request.session["reporter_access_token"] = ticket.reporter_access_token or ""
    request.session["reporter_tracked_ticket_id"] = ticket.ticket_id
    request.session["reporter_resume_link"] = "/lapor/tiket-saya"
    request.session["reporter_name"] = ticket.reporter_name or ""
    request.session["reporter_contact"] = ticket.reporter_contact or reporter_contact
    request.session["reporter_unit"] = ticket.reporter_department or ""
    request.session["media_pelaporan"] = ticket.media_pelaporan or "Sistem Tiket"
    request.session["incident_time"] = (
        ticket.incident_time.isoformat(timespec="minutes")
        if ticket.incident_time else ""
    )
    request.session["affected_asset"] = ticket.affected_asset or ""
    return RedirectResponse(url="/lapor/tiket-saya", status_code=303)


@router.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
    db: Session = Depends(get_db_session),
):
    svc = ChatService(redis=_redis_client())
    history = svc.get_history(reporter["session_id"], reporter.get("reporter_access_token", ""))
    session_ticket_id = (
        svc.get_session_ticket(reporter["session_id"])
        or svc.get_reporter_ticket(reporter.get("reporter_access_token", ""))
    )
    session_ticket = None
    if session_ticket_id:
        session_ticket = db.query(IncidentTicket).filter_by(ticket_id=session_ticket_id).first()
    reporter_tickets = []
    ticket_ids = _get_reporter_ticket_ids(reporter, db, redis_client=svc._redis)
    if ticket_ids:
        reporter_tickets = (
            db.query(IncidentTicket)
            .filter(IncidentTicket.ticket_id.in_(ticket_ids))
            .order_by(IncidentTicket.created_at.desc())
            .all()
        )
    return templates.TemplateResponse(
        "pelapor/chat.html",
        {
            "request": request,
            "reporter": reporter,
            "history": history,
            "session_ticket": session_ticket,
            "reporter_tickets": reporter_tickets,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.post("/chat/message", response_class=HTMLResponse)
@limiter.limit("60/minute")
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
        reporter_access_token=reporter.get("reporter_access_token", ""),
        reporter_unit=reporter.get("reporter_unit", ""),
        text=text,
        graph=graph,
        orchestrator=orchestrator,
        db=db,
        media_pelaporan=reporter.get("media_pelaporan", ""),
        incident_time=reporter.get("incident_time", ""),
        affected_asset=reporter.get("affected_asset", ""),
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
@limiter.limit("20/minute")
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
        {
            "request": request,
            "filename": filename,
            "size_kb": size_kb,
            "file_id": meta["file_id"],
            "mime_type": meta["mime_type"],
        },
    )


@router.post("/chat/upload/remove", response_class=HTMLResponse)
async def remove_upload(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
):
    """Hapus satu pending upload berdasarkan file_id."""
    import json as _json
    from pathlib import Path as _Path

    form = await request.form()
    file_id = (form.get("file_id") or "").strip()
    if not file_id:
        return HTMLResponse("")

    redis = _redis_client()
    key = f"web:pending_uploads:{reporter['session_id']}"
    raw = redis.get(key)
    if raw:
        try:
            pending = _json.loads(raw)
        except (ValueError, _json.JSONDecodeError):
            pending = []
        to_delete = [p for p in pending if p.get("file_id") == file_id]
        new_pending = [p for p in pending if p.get("file_id") != file_id]
        # Hapus file dari disk
        for p in to_delete:
            try:
                _Path(p["stored_path"]).unlink(missing_ok=True)
            except Exception:
                pass
        redis.setex(key, 86400, _json.dumps(new_pending).encode())

    return HTMLResponse("")  # HTMX akan swap pill dengan string kosong


@router.post("/chat/reset", response_class=HTMLResponse)
def reset_session(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
):
    svc = ChatService(redis=_redis_client())
    svc.clear_history(reporter["session_id"], reporter.get("reporter_access_token", ""))
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


@router.get("/akses/{access_token}", response_class=HTMLResponse)
def restore_reporter_access(
    request: Request,
    access_token: str,
    db: Session = Depends(get_db_session),
):
    latest_ticket = (
        db.query(IncidentTicket)
        .filter_by(reporter_access_token=access_token)
        .order_by(IncidentTicket.created_at.desc())
        .first()
    )
    if latest_ticket is None:
        raise HTTPException(status_code=404, detail="Tautan akses tidak ditemukan.")

    request.session["session_id"] = str(uuid.uuid4())
    request.session["reporter_id"] = latest_ticket.reporter_id
    request.session["reporter_access_token"] = access_token
    request.session["reporter_tracked_ticket_id"] = ""
    request.session["reporter_resume_link"] = f"/lapor/akses/{access_token}"
    request.session["reporter_name"] = latest_ticket.reporter_name or ""
    request.session["reporter_contact"] = latest_ticket.reporter_contact or ""
    request.session["reporter_unit"] = latest_ticket.reporter_department or ""
    request.session["media_pelaporan"] = latest_ticket.media_pelaporan or "Sistem Tiket"
    request.session["affected_asset"] = latest_ticket.affected_asset or ""
    request.session["incident_time"] = (
        latest_ticket.incident_time.isoformat(timespec="minutes")
        if latest_ticket.incident_time else ""
    )
    return RedirectResponse(url=f"/lapor/akses/{access_token}/riwayat", status_code=303)


@router.get("/akses/{access_token}/riwayat", response_class=HTMLResponse)
def reporter_ticket_history(
    request: Request,
    access_token: str,
    db: Session = Depends(get_db_session),
):
    tickets = (
        db.query(IncidentTicket)
        .filter_by(reporter_access_token=access_token)
        .order_by(IncidentTicket.created_at.desc())
        .all()
    )
    if not tickets:
        raise HTTPException(status_code=404, detail="Riwayat tiket tidak ditemukan.")
    return templates.TemplateResponse(
        "pelapor/riwayat_tiket.html",
        {
            "request": request,
            "tickets": tickets,
            "resume_link": f"/lapor/akses/{access_token}/chat",
            "resume_label": "Kembali ke Chat",
        },
    )


@router.get("/akses/{access_token}/chat", response_class=HTMLResponse)
def reporter_ticket_chat(
    request: Request,
    access_token: str,
    db: Session = Depends(get_db_session),
):
    latest_ticket = (
        db.query(IncidentTicket)
        .filter_by(reporter_access_token=access_token)
        .order_by(IncidentTicket.created_at.desc())
        .first()
    )
    if latest_ticket is None:
        raise HTTPException(status_code=404, detail="Tautan akses tidak ditemukan.")

    request.session["session_id"] = str(uuid.uuid4())
    request.session["reporter_id"] = latest_ticket.reporter_id
    request.session["reporter_access_token"] = access_token
    request.session["reporter_tracked_ticket_id"] = ""
    request.session["reporter_resume_link"] = f"/lapor/akses/{access_token}"
    request.session["reporter_name"] = latest_ticket.reporter_name or ""
    request.session["reporter_contact"] = latest_ticket.reporter_contact or ""
    request.session["reporter_unit"] = latest_ticket.reporter_department or ""
    request.session["media_pelaporan"] = latest_ticket.media_pelaporan or "Sistem Tiket"
    request.session["affected_asset"] = latest_ticket.affected_asset or ""
    request.session["incident_time"] = (
        latest_ticket.incident_time.isoformat(timespec="minutes")
        if latest_ticket.incident_time else ""
    )
    return RedirectResponse(url="/lapor/chat", status_code=303)


@router.get("/tiket-saya", response_class=HTMLResponse)
def reporter_ticket_home(
    request: Request,
    reporter: dict = Depends(get_reporter_session),
    db: Session = Depends(get_db_session),
):
    tickets = []
    ticket_ids = _get_reporter_ticket_ids(reporter, db)
    if ticket_ids:
        tickets = (
            db.query(IncidentTicket)
            .filter(IncidentTicket.ticket_id.in_(ticket_ids))
            .order_by(IncidentTicket.created_at.desc())
            .all()
        )
    return templates.TemplateResponse(
        "pelapor/riwayat_tiket.html",
        {
            "request": request,
            "tickets": tickets,
            "resume_link": "/lapor/chat",
            "resume_label": "Kembali ke Chat",
        },
    )


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
        return templates.TemplateResponse(
            "pelapor/tiket_detail.html",
            {
                "request": request,
                "ticket": None,
                "warning": "Tiket ini tidak terhubung dengan sesi Anda. Silakan kembali ke daftar tiket yang Anda miliki.",
                "resume_link": request.session.get("reporter_resume_link", "/lapor") or "/lapor",
                "support_whatsapp_url": _support_whatsapp_url(),
                "support_phone_label": _support_phone_label(),
                "support_email": _support_email(),
            },
            status_code=403,
        )
    return templates.TemplateResponse(
        "pelapor/tiket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "resume_link": request.session.get("reporter_resume_link", ""),
            "support_whatsapp_url": _support_whatsapp_url(),
            "support_phone_label": _support_phone_label(),
            "support_email": _support_email(),
        },
    )
