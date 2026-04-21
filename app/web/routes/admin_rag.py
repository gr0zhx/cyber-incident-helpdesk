"""Routes dashboard manajemen knowledge base RAG."""
import logging
import os
from typing import Optional

import redis as _redis_lib
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.rag_service import RagService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/rag", tags=["admin-rag"])
templates = Jinja2Templates(directory="app/web/templates")


def _redis_client():
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return _redis_lib.from_url(url, decode_responses=False)


def _make_service():
    return RagService(redis=_redis_client())


@router.get("", response_class=HTMLResponse)
def rag_page(
    request: Request,
    job_id: Optional[str] = None,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    svc = _make_service()
    return templates.TemplateResponse(
        "admin/rag.html",
        {
            "request": request,
            "collection": svc.get_collection_info(),
            "documents": svc.list_documents(),
            "csrf_token": request.session.get("csrf_token", ""),
            "admin": admin,
            "job_id": job_id,
        },
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    doc_id: str = Form(...),
    doc_title: str = Form(...),
    source_framework: str = Form("LAINNYA"),
    incident_types: str = Form(""),
    language: str = Form("id"),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    data = await file.read()
    filename = file.filename or "upload.pdf"
    types_list = [t.strip() for t in incident_types.split(",") if t.strip()] or ["general"]
    svc = _make_service()
    try:
        meta_filename = svc.upload_pdf(
            filename=filename, data=data, doc_id=doc_id,
            doc_title=doc_title, source_framework=source_framework,
            incident_types=types_list, language=language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    job_id = svc.start_ingest_job(meta_filename)
    background_tasks.add_task(svc.run_ingest, job_id)
    logger.info("RAG_INGEST_STARTED admin=%s doc_id=%s job=%s", admin.username, doc_id, job_id)
    return RedirectResponse(url=f"/admin/rag?job_id={job_id}", status_code=303)


@router.post("/reindex", response_class=HTMLResponse)
def reindex_all(
    request: Request,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
):
    svc = _make_service()
    docs = svc.list_documents()
    for doc in docs:
        meta_filename = doc.get("_meta_file")
        if meta_filename:
            job_id = svc.start_ingest_job(meta_filename)
            background_tasks.add_task(svc.run_ingest, job_id)
    logger.info("RAG_REINDEX_STARTED admin=%s docs=%d", admin.username, len(docs))
    return RedirectResponse(url="/admin/rag", status_code=303)
