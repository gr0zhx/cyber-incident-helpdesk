# Plan D — Web Admin RAG Management & Report Generation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bangun dua fitur admin terakhir — (1) manajemen knowledge base RAG (upload PDF, lihat koleksi, reindex) dan (2) generate laporan insiden per-tiket dalam format HTML yang bisa didownload — melengkapi dashboard admin web.

**Architecture:** `RagService` membungkus `app/dashboard/rag_client.py` (sudah ada, pure-Python non-Streamlit). `ReportService` membungkus `app/dashboard/report_generator.py` (sudah ada). Background ingest via FastAPI `BackgroundTasks`; status job di Redis key `rag:job:{job_id}`. Tidak ada migration baru. Report dibuat in-memory, dikembalikan langsung sebagai `HTMLResponse` dengan `Content-Disposition: attachment`.

**Tech Stack:** FastAPI · BackgroundTasks · Jinja2 · HTMX · SQLAlchemy · Redis · pytest

**Spec reference:** `docs/superpowers/specs/2026-04-13-web-interface-design.md` Sections 5.6, 5.7, 5.9 (audit events `RAG_*`, `REPORT_GENERATED`)

**Depends on:** Plan A + Plan B committed. Plans C tidak diperlukan untuk Plan D.

---

## File Structure

### Create

```
app/web/
├── services/
│   ├── rag_service.py                 # Wrap rag_client + BackgroundTasks + Redis job status
│   └── report_service.py              # Wrap report_generator, ambil tiket dari DB
├── routes/
│   ├── admin_rag.py                   # GET /admin/rag, POST /admin/rag/upload, POST /admin/rag/reindex
│   └── admin_report.py                # GET /admin/report, POST /admin/report/generate
├── templates/
│   └── admin/
│       ├── rag.html                   # Dashboard KB: info koleksi + daftar dokumen + upload form
│       └── report.html                # Form generate laporan

tests/test_web/
├── test_services/
│   ├── test_rag_service.py
│   └── test_report_service.py
└── test_routes/
    ├── test_admin_rag.py
    └── test_admin_report.py
```

### Modify

- `app/web/app.py` — register `admin_rag` dan `admin_report` routers

### Out of scope

- Delete collection (spec ada, tapi butuh konfirmasi ganda yang komplex UI — YAGNI untuk prototipe)
- STIX management (sudah di Streamlit dashboard, tidak duplikasi)
- Audit log table writes (deferred, Plan A-D pakai logger.info — konsisten)

---

## Task 1: RagService

**Files:**
- Create: `app/web/services/rag_service.py`
- Test: `tests/test_web/test_services/test_rag_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_services/test_rag_service.py
import json
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from app.web.services.rag_service import RagService


def _make_service():
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    return RagService(redis=r), r


def test_get_collection_info_wraps_rag_client(tmp_path):
    svc, _ = _make_service()
    with patch("app.web.services.rag_service.get_collection_info",
               return_value={"name": "cybersecurity_knowledge", "total_vectors": 42}):
        info = svc.get_collection_info()
    assert info["total_vectors"] == 42


def test_list_documents_wraps_rag_client(tmp_path):
    svc, _ = _make_service()
    with patch("app.web.services.rag_service.list_metadata_documents",
               return_value=[{"doc_id": "doc-1", "doc_title": "NIST Guide"}]):
        docs = svc.list_documents()
    assert len(docs) == 1 and docs[0]["doc_id"] == "doc-1"


def test_start_ingest_job_stores_status_pending(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("nist-guide.json")
    status = json.loads(r.get(f"rag:job:{job_id}"))
    assert status["state"] == "pending"
    assert status["meta_filename"] == "nist-guide.json"


def test_get_job_status_returns_none_for_unknown(tmp_path):
    svc, _ = _make_service()
    assert svc.get_job_status("nonexistent") is None


def test_get_job_status_returns_stored(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("doc.json")
    status = svc.get_job_status(job_id)
    assert status is not None and status["state"] == "pending"


def test_run_ingest_updates_status_to_done(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("doc.json")
    with patch("app.web.services.rag_service.reingest_document",
               return_value={"doc_id": "d1", "uploaded": 10, "deleted": 5}):
        svc.run_ingest(job_id)
    status = svc.get_job_status(job_id)
    assert status["state"] == "done"
    assert status["result"]["uploaded"] == 10


def test_run_ingest_updates_status_to_error_on_failure(tmp_path):
    svc, _ = _make_service()
    job_id = svc.start_ingest_job("bad.json")
    with patch("app.web.services.rag_service.reingest_document",
               side_effect=RuntimeError("Qdrant down")):
        svc.run_ingest(job_id)
    status = svc.get_job_status(job_id)
    assert status["state"] == "error"
    assert "Qdrant down" in status["error"]
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_services/test_rag_service.py -v`
Expected: ImportError

- [ ] **Step 3: Implement RagService**

```python
# app/web/services/rag_service.py
"""Wrap rag_client untuk manajemen knowledge base dari web dashboard."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from app.dashboard.rag_client import (
    get_collection_info,
    get_collection_stats_by_source,
    list_metadata_documents,
    reingest_document,
    save_metadata,
    save_pdf,
)

logger = logging.getLogger(__name__)
_JOB_TTL = 3600  # 1 jam


class RagService:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    def get_collection_info(self) -> dict:
        """Info Qdrant collection (total vectors, status)."""
        try:
            return get_collection_info()
        except Exception as exc:
            logger.warning("get_collection_info gagal: %s", exc)
            return {"error": str(exc)}

    def list_documents(self) -> list[dict]:
        """Daftar dokumen yang terdaftar di knowledge base."""
        try:
            return list_metadata_documents()
        except Exception as exc:
            logger.warning("list_metadata_documents gagal: %s", exc)
            return []

    def upload_pdf(
        self,
        filename: str,
        data: bytes,
        doc_id: str,
        doc_title: str,
        source_framework: str,
        incident_types: list[str],
        language: str = "id",
    ) -> str:
        """Simpan PDF + metadata ke knowledge_base/, return meta_filename."""
        safe_name = filename.replace(" ", "_")
        save_pdf(safe_name, data)
        meta_filename = f"{doc_id}.json"
        save_metadata(meta_filename, {
            "doc_id": doc_id,
            "doc_title": doc_title,
            "filename": safe_name,
            "source_framework": source_framework,
            "incident_types": incident_types,
            "language": language,
            "version": "1.0",
        })
        return meta_filename

    def start_ingest_job(self, meta_filename: str) -> str:
        """Buat job ID dan simpan status 'pending' ke Redis."""
        job_id = str(uuid.uuid4())
        status = {"state": "pending", "meta_filename": meta_filename}
        self._redis.setex(f"rag:job:{job_id}", _JOB_TTL, json.dumps(status).encode())
        return job_id

    def get_job_status(self, job_id: str) -> Optional[dict]:
        raw = self._redis.get(f"rag:job:{job_id}")
        if not raw:
            return None
        return json.loads(raw)

    def run_ingest(self, job_id: str) -> None:
        """Eksekusi reingest (dipanggil dari BackgroundTasks)."""
        raw = self._redis.get(f"rag:job:{job_id}")
        if not raw:
            logger.error("Job %s tidak ditemukan di Redis", job_id)
            return
        status = json.loads(raw)
        meta_filename = status["meta_filename"]
        try:
            result = reingest_document(meta_filename)
            status["state"] = "done"
            status["result"] = result
        except Exception as exc:
            logger.exception("Ingest job %s gagal", job_id)
            status["state"] = "error"
            status["error"] = str(exc)
        self._redis.setex(f"rag:job:{job_id}", _JOB_TTL, json.dumps(status).encode())
        logger.info("RAG_INGEST_COMPLETED job=%s state=%s", job_id, status["state"])
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_rag_service.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/rag_service.py tests/test_web/test_services/test_rag_service.py
git commit -m "feat(web): RagService wrapping rag_client with background job tracking"
```

---

## Task 2: ReportService

**Files:**
- Create: `app/web/services/report_service.py`
- Test: `tests/test_web/test_services/test_report_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_services/test_report_service.py
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, IncidentTicket
from app.web.services.report_service import ReportService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(IncidentTicket(
        ticket_id="INC-R1",
        reporter_id="tg:1",
        reporter_name="Budi",
        incident_type="PHISHING",
        severity="HIGH",
        description_raw="x",
        description_sanitized="Phishing email",
        status="RESOLVED",
        mitigation_recommendation="Isolasi host.",
    ))
    session.commit()
    yield session
    session.close()


def test_generate_returns_html_string(db):
    svc = ReportService(db)
    html, filename = svc.generate("INC-R1")
    assert "<html" in html.lower() or "<!DOCTYPE" in html.lower()
    assert "INC-R1" in html
    assert filename.endswith(".html")


def test_generate_raises_for_missing_ticket(db):
    svc = ReportService(db)
    with pytest.raises(LookupError):
        svc.generate("NOPE")
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_services/test_report_service.py -v`
Expected: ImportError

- [ ] **Step 3: Implement ReportService**

```python
# app/web/services/report_service.py
"""Wrap report_generator untuk download laporan insiden dari web dashboard."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.dashboard.report_generator import generate_report_filename, generate_report_html
from app.database.models import IncidentTicket


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate(self, ticket_id: str, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> tuple[str, str]:
        """Generate laporan HTML untuk satu tiket. Return (html_string, filename)."""
        ticket = self.db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
        if ticket is None:
            raise LookupError(f"Tiket {ticket_id} tidak ditemukan.")
        ticket_dict = {
            "ticket_id": ticket.ticket_id,
            "incident_type": ticket.incident_type,
            "severity": ticket.severity,
            "status": ticket.status,
            "escalation_level": ticket.escalation_level,
            "reporter_name": ticket.reporter_name,
            "reporter_id": ticket.reporter_id,
            "assigned_to": ticket.assigned_to,
            "description_sanitized": ticket.description_sanitized,
            "mitigation_recommendation": ticket.mitigation_recommendation,
            "confidence_score": float(ticket.confidence_score or 0),
            "created_at": str(ticket.created_at) if ticket.created_at else None,
            "updated_at": str(ticket.updated_at) if ticket.updated_at else None,
            "reviewed_at": str(ticket.reviewed_at) if ticket.reviewed_at else None,
            "resolved_at": str(ticket.resolved_at) if ticket.resolved_at else None,
        }
        html = generate_report_html(ticket_dict, prepared_by=prepared_by)
        filename = generate_report_filename(ticket_dict)
        return html, filename
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_report_service.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/report_service.py tests/test_web/test_services/test_report_service.py
git commit -m "feat(web): ReportService wrapping report_generator"
```

---

## Task 3: RAG admin templates

**Files:**
- Create: `app/web/templates/admin/rag.html`
- Create: `app/web/templates/admin/report.html`

- [ ] **Step 1: Create rag.html**

```html
{# app/web/templates/admin/rag.html #}
{% extends "admin/_shell.html" %}
{% block page_title %}Knowledge Base RAG{% endblock %}
{% block content %}

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
  <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
    <h3 style="font-size: 13px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Koleksi Qdrant</h3>
    {% if collection.error %}
    <p style="color: #dc2626;">{{ collection.error }}</p>
    {% else %}
    <div style="font-size: 28px; font-weight: 700; color: #0f172a;">{{ collection.total_vectors or 0 }}</div>
    <div style="color: #64748b; font-size: 13px;">total vectors · status: {{ collection.status or "—" }}</div>
    {% endif %}
  </div>
  <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
    <h3 style="font-size: 13px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Dokumen Terdaftar</h3>
    <div style="font-size: 28px; font-weight: 700; color: #0f172a;">{{ documents|length }}</div>
    <div style="color: #64748b; font-size: 13px;">PDF di knowledge_base/</div>
  </div>
</div>

<div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-bottom: 24px;">
  <h2 style="font-size: 16px; margin-bottom: 16px;">Upload Dokumen Baru</h2>
  <form method="post" action="/admin/rag/upload" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">File PDF *</label>
        <input type="file" name="file" accept=".pdf" required class="form-control">
      </div>
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Doc ID (unik) *</label>
        <input type="text" name="doc_id" required class="form-control" placeholder="nist-csf-v2">
      </div>
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Judul Dokumen *</label>
        <input type="text" name="doc_title" required class="form-control" placeholder="NIST Cybersecurity Framework v2">
      </div>
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Framework Sumber</label>
        <select name="source_framework" class="form-control">
          {% for f in ["NIST","MITRE","BSSN","ISO27001","LAINNYA"] %}
          <option value="{{ f }}">{{ f }}</option>{% endfor %}
        </select>
      </div>
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Incident Types (pisah koma)</label>
        <input type="text" name="incident_types" class="form-control" placeholder="phishing,malware">
      </div>
      <div>
        <label style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Bahasa</label>
        <select name="language" class="form-control">
          <option value="id">Indonesia</option>
          <option value="en">English</option>
        </select>
      </div>
    </div>
    <button type="submit" class="btn btn-primary">Upload & Ingest →</button>
  </form>
  {% if job_id %}
  <div style="margin-top: 16px; padding: 12px; background: #eff6ff; border-radius: 6px; color: #1e40af;">
    Ingest dimulai. Job ID: <code>{{ job_id }}</code> — Refresh halaman untuk melihat status.
  </div>
  {% endif %}
</div>

<div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <h2 style="font-size: 16px;">Dokumen Terdaftar</h2>
    <form method="post" action="/admin/rag/reindex">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <button type="submit" class="btn" style="font-size: 13px;">Reindex Semua</button>
    </form>
  </div>
  <table style="width: 100%; border-collapse: collapse;">
    <thead style="background: #f1f5f9;">
      <tr>
        <th style="padding: 10px; text-align: left;">Doc ID</th>
        <th style="padding: 10px; text-align: left;">Judul</th>
        <th style="padding: 10px; text-align: left;">Framework</th>
        <th style="padding: 10px; text-align: left;">PDF</th>
      </tr>
    </thead>
    <tbody>
      {% for doc in documents %}
      <tr style="border-top: 1px solid #e2e8f0;">
        <td style="padding: 10px; font-family: monospace; font-size: 13px;">{{ doc.doc_id }}</td>
        <td style="padding: 10px;">{{ doc.doc_title }}</td>
        <td style="padding: 10px;">{{ doc.source_framework }}</td>
        <td style="padding: 10px; font-size: 13px; color: {% if doc._pdf_exists %}#16a34a{% else %}#dc2626{% endif %};">
          {% if doc._pdf_exists %}✓ {{ doc._pdf_size_kb }} KB{% else %}✗ hilang{% endif %}
        </td>
      </tr>
      {% else %}
      <tr><td colspan="4" style="padding: 24px; text-align: center; color: #94a3b8;">Belum ada dokumen.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 2: Create report.html**

```html
{# app/web/templates/admin/report.html #}
{% extends "admin/_shell.html" %}
{% block page_title %}Generate Laporan{% endblock %}
{% block content %}
<div style="max-width: 600px;">
  <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
    <p style="color: #64748b; margin-bottom: 24px; font-size: 14px;">
      Generate laporan insiden per-tiket dalam format HTML yang dapat dicetak sebagai PDF via browser.
    </p>
    {% if error %}
    <div style="background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; padding: 12px; margin-bottom: 16px; color: #dc2626;">{{ error }}</div>
    {% endif %}
    <form method="post" action="/admin/report/generate">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <div style="margin-bottom: 16px;">
        <label for="ticket_id" style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Ticket ID *</label>
        <input id="ticket_id" type="text" name="ticket_id" required class="form-control"
               placeholder="INC-YYYYMMDD-XXXX" style="font-family: monospace;">
      </div>
      <div style="margin-bottom: 24px;">
        <label for="prepared_by" style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Disiapkan Oleh</label>
        <input id="prepared_by" type="text" name="prepared_by" class="form-control"
               value="Tim Keamanan Siber Pusdatin">
      </div>
      <button type="submit" class="btn btn-primary">Download Laporan →</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add app/web/templates/admin/rag.html app/web/templates/admin/report.html
git commit -m "feat(web): RAG management + report generation templates"
```

---

## Task 4: Admin RAG routes

**Files:**
- Create: `app/web/routes/admin_rag.py`
- Test: `tests/test_web/test_routes/test_admin_rag.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_routes/test_admin_rag.py
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.routes.admin_rag import router


@pytest.fixture
def client():
    admin = Admin(id=1, username="admin1", email="a@x.com", full_name="A",
                  password_hash="h", is_active=True)

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_db_session] = lambda: iter([MagicMock()])
    app.include_router(router)
    return TestClient(app)


def _patch_rag(collection=None, docs=None):
    return (
        patch("app.web.routes.admin_rag._redis_client",
              return_value=fakeredis.FakeStrictRedis(decode_responses=False)),
        patch("app.web.routes.admin_rag.RagService.get_collection_info",
              return_value=collection or {"total_vectors": 10, "status": "green"}),
        patch("app.web.routes.admin_rag.RagService.list_documents",
              return_value=docs or []),
    )


def test_rag_page_renders(client):
    with _patch_rag()[0], _patch_rag()[1], _patch_rag()[2]:
        r = client.get("/admin/rag")
    assert r.status_code == 200
    assert "Knowledge Base" in r.text


def test_rag_reindex_redirects(client):
    with patch("app.web.routes.admin_rag._redis_client",
               return_value=fakeredis.FakeStrictRedis(decode_responses=False)), \
         patch("app.web.routes.admin_rag.RagService.start_ingest_job", return_value="job-1"), \
         patch("app.web.routes.admin_rag.RagService.run_ingest"):
        r = client.post("/admin/rag/reindex", data={"csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (302, 303)
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_rag.py -v`
Expected: ImportError

- [ ] **Step 3: Implement admin_rag routes**

```python
# app/web/routes/admin_rag.py
"""Routes dashboard manajemen knowledge base RAG."""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
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
    from app.web.services.auth_service import _redis_client as _rc
    return _rc()


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
    meta_filename = svc.upload_pdf(
        filename=filename, data=data, doc_id=doc_id,
        doc_title=doc_title, source_framework=source_framework,
        incident_types=types_list, language=language,
    )
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_web/test_routes/test_admin_rag.py -v`
Expected: 2 PASS

Note: `test_rag_page_renders` melakukan 3 patch terpisah. Refactor fixture jika perlu. Patch harus ke `app.web.routes.admin_rag.RagService.*`, bukan ke `app.web.services.rag_service.*`, karena yang dipakai adalah instance di dalam routes.

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/admin_rag.py tests/test_web/test_routes/test_admin_rag.py
git commit -m "feat(web): admin RAG dashboard routes (view/upload/reindex)"
```

---

## Task 5: Admin Report routes

**Files:**
- Create: `app/web/routes/admin_report.py`
- Test: `tests/test_web/test_routes/test_admin_report.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_routes/test_admin_report.py
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from app.database.models import Admin, Base, IncidentTicket
from app.web.dependencies import get_current_admin, get_db_session
from app.web.routes.admin_report import router
from datetime import datetime, timezone


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = Admin(id=1, username="admin1", email="a@x.com", full_name="A",
                  password_hash="h", is_active=True)
    db.add(admin)
    db.add(IncidentTicket(
        ticket_id="INC-R1",
        reporter_id="tg:1",
        reporter_name="Budi",
        incident_type="PHISHING",
        severity="HIGH",
        description_raw="x",
        description_sanitized="phishing",
        status="RESOLVED",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_db_session] = lambda: iter([db])
    app.include_router(router)
    return TestClient(app)


def test_report_page_renders(client):
    r = client.get("/admin/report")
    assert r.status_code == 200
    assert "Generate Laporan" in r.text


def test_report_generate_returns_html_download(client):
    r = client.post("/admin/report/generate",
                    data={"ticket_id": "INC-R1", "prepared_by": "Admin", "csrf_token": "x"})
    assert r.status_code == 200
    assert "INC-R1" in r.text
    assert "attachment" in r.headers.get("content-disposition", "")


def test_report_generate_missing_ticket_shows_error(client):
    r = client.post("/admin/report/generate",
                    data={"ticket_id": "NOPE", "prepared_by": "Admin", "csrf_token": "x"})
    assert r.status_code == 200
    assert "tidak ditemukan" in r.text.lower()
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_report.py -v`
Expected: ImportError

- [ ] **Step 3: Implement admin_report routes**

```python
# app/web/routes/admin_report.py
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
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_admin_report.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/admin_report.py tests/test_web/test_routes/test_admin_report.py
git commit -m "feat(web): admin report generation route (HTML download)"
```

---

## Task 6: Wire routers + update sidebar nav

**Files:**
- Modify: `app/web/app.py`
- Modify: `app/web/templates/admin/_shell.html` — aktifkan link Knowledge Base + Laporan

- [ ] **Step 1: Update app.py**

Tambah import dan register router:

```python
from app.web.routes.admin_rag import router as admin_rag_router
from app.web.routes.admin_report import router as admin_report_router

# dalam register_web():
app.include_router(admin_rag_router)
app.include_router(admin_report_router)
```

- [ ] **Step 2: Update sidebar links di _shell.html**

Ubah warna link "Knowledge Base" dan "Laporan" dari `#64748b` (disabled) ke `#cbd5e1` (aktif), sama dengan "Inbox Tiket":

```html
<a href="/admin/rag" style="color: #cbd5e1; text-decoration: none; padding: 8px 12px; border-radius: 6px;">Knowledge Base</a>
<a href="/admin/report" style="color: #cbd5e1; text-decoration: none; padding: 8px 12px; border-radius: 6px;">Laporan</a>
```

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/test_web/ -v`
Expected: semua PASS

- [ ] **Step 4: Commit**

```bash
git add app/web/app.py app/web/templates/admin/_shell.html
git commit -m "chore(web): wire RAG + report routers, activate sidebar links"
```

---

## Task 7: Manual smoke test checklist

**Files:** (none — verifikasi manual)

- [ ] **Step 1: Start server**

```bash
uvicorn app.main:app --reload --port 8000
```

Pastikan Qdrant dan environment vars tersedia:
- `QDRANT_URL` (default: `http://localhost:6333`)
- `OPENAI_API_KEY` atau `GITHUB_TOKEN` (lihat `app/utils/llm_client.py`)

- [ ] **Step 2: RAG browser flow**

1. Login admin → buka `http://localhost:8000/admin/rag`
2. Sidebar link "Knowledge Base" aktif → halaman terbuka
3. Lihat statistik koleksi (total vectors, status)
4. Upload PDF: pilih file PDF + isi doc_id/doc_title/framework → klik "Upload & Ingest"
5. Redirect ke `/admin/rag?job_id=...` → pesan "Ingest dimulai" muncul
6. Refresh → dokumen muncul di tabel daftar
7. Klik "Reindex Semua" → redirect kembali ke RAG page

- [ ] **Step 3: Report browser flow**

1. Buka `http://localhost:8000/admin/report`
2. Isi ticket_id yang ada di DB → klik "Download Laporan"
3. Browser download file `Laporan-Insiden-{id}-{tanggal}.html`
4. Buka file → laporan tampil dengan info tiket, mitigasi, dll
5. Tes ticket_id yang tidak ada → pesan error muncul di form

- [ ] **Step 4: Verifikasi log**

Cek stdout server untuk:

```
RAG_INGEST_STARTED admin=admin1 doc_id=... job=...
RAG_INGEST_COMPLETED job=... state=done
REPORT_GENERATED admin=admin1 ticket=INC-...
```

- [ ] **Step 5: Tag release**

```bash
git tag plan-d-complete
```

---

## Notes for the Executing Subagent

- **`_meta_file` key**: `list_metadata_documents()` mengembalikan list dict yang masing-masing punya key `_meta_file` (nama file JSON metadata). Route `/admin/rag/reindex` iterasi docs dan ambil `doc.get("_meta_file")`.
- **`RagService` patch di test**: patch via `app.web.routes.admin_rag.RagService.method_name`, bukan `app.web.services.rag_service.RagService.method_name` — karena di routes kita instantiate `RagService()` secara lokal.
- **`test_rag_page_renders`**: Butuh 3 context managers sekaligus. Simplifikasi dengan `@patch` di class level atau gunakan satu `patch.multiple`. Contoh:
  ```python
  with patch.multiple(
      "app.web.routes.admin_rag",
      _redis_client=lambda: fakeredis.FakeStrictRedis(decode_responses=False),
  ), patch.object(RagService, "get_collection_info", return_value={...}), \
     patch.object(RagService, "list_documents", return_value=[]):
      r = client.get("/admin/rag")
  ```
- **Form `@router.get("")`**: Gunakan `""` bukan `"/"` untuk prefix `/admin/rag` agar tidak ada redirect trailing slash.
- **BackgroundTasks**: Di TestClient, background tasks run synchronously setelah response dikirim — tidak perlu mock untuk unit test, tapi `reingest_document` butuh Qdrant. Patch `svc.run_ingest` atau `reingest_document` jika tidak ada Qdrant di test.
- **ReportService**: `generate_report_html()` dari `report_generator.py` sudah ada, tidak perlu ditulis ulang.
- **Tidak ada migration baru**: Semua tabel sudah ada.
