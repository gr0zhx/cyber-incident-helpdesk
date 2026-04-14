# Plan C — Web Pelapor Chat & Upload

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bangun alur pelapor web lengkap — form identitas → sesi cookie → halaman chat HTMX (request-response, bukan streaming) → upload file lampiran → status tiket read-only — sehingga pelapor bisa melaporkan insiden via browser tanpa Telegram.

**Architecture:** `ChatService` mengurus history Redis + invoke `helpdesk_graph` in-process. `UploadService` validasi file via python-magic + simpan ke `web_uploads/`. Sesi pelapor disimpan di cookie Starlette yang sudah tersedia dari Plan A. `TicketAttachment` model baru di PostgreSQL via Alembic. Pipeline LangGraph di-inject via FastAPI Depends yang sama dengan `app/api/dependencies.py` — tidak duplikasi setup.

**Tech Stack:** FastAPI · Jinja2 · HTMX · python-magic (python-magic-bin on Windows) · Redis · LangGraph · SQLAlchemy · Alembic · pytest · fakeredis

**Spec reference:** `docs/superpowers/specs/2026-04-13-web-interface-design.md` Sections 3 (TicketAttachment, Redis keys), 4 (chat flow, upload, rate limit, privacy)

**Depends on:** Plan A + Plan B committed to `feat/web-plan-a`.

---

## File Structure

### Create

```
app/web/
├── services/
│   ├── upload_service.py              # MIME validation, UUID filename, disk write, Redis pending
│   └── chat_service.py                # Redis history, pipeline invoke, flush uploads
├── routes/
│   └── pelapor.py                     # GET/POST /lapor, GET /lapor/chat, POST message/upload/reset, GET tiket
├── templates/
│   └── pelapor/
│       ├── identitas.html             # Form nama/kontak/unit
│       ├── chat.html                  # Full chat page (extends _shell pelapor variant)
│       ├── _message.html              # HTMX fragment: satu bubble
│       ├── _tiket_card.html           # HTMX fragment: ringkasan tiket terbentuk
│       ├── _attachment_pill.html      # HTMX fragment: pill upload berhasil
│       └── _error_bubble.html         # HTMX fragment: error pipeline/timeout

app/database/migrations/versions/
└── 20260414_01_add_ticket_attachments.py

tests/test_web/
├── test_services/
│   ├── test_upload_service.py
│   └── test_chat_service.py
├── test_routes/
│   └── test_pelapor.py
└── test_integration/
    └── test_reporter_flow.py
```

### Modify

- `app/database/models.py` — tambah class `TicketAttachment`
- `app/web/dependencies.py` — tambah `get_reporter_session`
- `app/web/app.py` — register `pelapor` router
- `requirements.txt` — tambah `python-magic` platform markers

### Out of scope

- Streaming token response (spec request-response, bukan streaming)
- Email notification ke pelapor (spec: future work)
- Playwright E2E test (spec: optional)
- Rate limit 429 bubble (slowapi sudah aktif dari Plan A — hanya tambah routes)

---

## Task 1: TicketAttachment model + migration

**Files:**
- Modify: `app/database/models.py`
- Create: `app/database/migrations/versions/20260414_01_add_ticket_attachments.py`
- Test: tidak perlu (model test terlalu trivial; ditest lewat service)

- [ ] **Step 1: Tambah model ke models.py**

Append setelah class `Admin`:

```python
class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(32), nullable=False, index=True)  # FK logis, tanpa constraint (prototipe)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_by = Column(String(128), nullable=False)  # session_id pelapor atau admin username
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Buat Alembic migration**

```python
# app/database/migrations/versions/20260414_01_add_ticket_attachments.py
"""add ticket_attachments table

Revision ID: 20260414_01
Revises: <isi dengan revision ID migration terakhir di folder versions/>
Create Date: 2026-04-14
"""
from alembic import op
import sqlalchemy as sa

revision = "20260414_01"
down_revision = None  # ganti dengan revision ID migration sebelumnya
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.String(32), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.String(128), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_ticket_attachments_ticket_id", "ticket_attachments", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_attachments_ticket_id", "ticket_attachments")
    op.drop_table("ticket_attachments")
```

**PENTING**: Set `down_revision` = revision ID migration terakhir. Cek dengan:

```bash
ls app/database/migrations/versions/*.py
```

- [ ] **Step 3: Verify model importable**

Run: `python -c "from app.database.models import TicketAttachment; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/database/models.py app/database/migrations/versions/20260414_01_add_ticket_attachments.py
git commit -m "feat(db): add TicketAttachment model + alembic migration"
```

---

## Task 2: python-magic setup + requirements

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Cek requirements.txt**

Run: `grep -n "magic\|upload" requirements.txt`
Jika tidak ada `python-magic`, lanjut ke Step 2.

- [ ] **Step 2: Tambah python-magic platform markers**

Append ke `requirements.txt`:

```
# File upload MIME validation
python-magic; platform_system != "Windows"
python-magic-bin; platform_system == "Windows"
```

- [ ] **Step 3: Install (sesuai platform)**

```bash
# Windows:
pip install python-magic-bin
# Linux:
# pip install python-magic
```

- [ ] **Step 4: Verify**

Run: `python -c "import magic; print(magic.from_buffer(b'%PDF-1.4', mime=True))"`
Expected: `application/pdf`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore: add python-magic platform requirements for file upload"
```

---

## Task 3: UploadService

**Files:**
- Create: `app/web/services/upload_service.py`
- Test: `tests/test_web/test_services/test_upload_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_services/test_upload_service.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from app.web.services.upload_service import UploadService, UploadError

FAKE_PDF_BYTES = b"%PDF-1.4 fake"
FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\nFAKE"


def _make_service(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    return UploadService(redis=r, upload_root=tmp_path), r


def test_save_pending_pdf(tmp_path):
    svc, r = _make_service(tmp_path)
    with patch("app.web.services.upload_service.magic") as m:
        m.from_buffer.return_value = "application/pdf"
        meta = svc.save_pending(
            session_id="sess-1",
            filename="report.pdf",
            data=FAKE_PDF_BYTES,
        )
    assert meta["original_filename"] == "report.pdf"
    assert meta["mime_type"] == "application/pdf"
    assert Path(meta["stored_path"]).exists()
    pending = json.loads(r.get("web:pending_uploads:sess-1") or "[]")
    assert len(pending) == 1 and pending[0]["original_filename"] == "report.pdf"


def test_save_pending_rejects_invalid_extension(tmp_path):
    svc, _ = _make_service(tmp_path)
    with pytest.raises(UploadError, match="ekstensi"):
        svc.save_pending("sess-1", "virus.exe", b"MZ")


def test_save_pending_rejects_mime_mismatch(tmp_path):
    svc, _ = _make_service(tmp_path)
    with patch("app.web.services.upload_service.magic") as m:
        m.from_buffer.return_value = "application/x-msdownload"
        with pytest.raises(UploadError, match="MIME"):
            svc.save_pending("sess-1", "photo.png", b"MZ")


def test_save_pending_rejects_oversized(tmp_path):
    svc, _ = _make_service(tmp_path)
    big = b"x" * (11 * 1024 * 1024)
    with pytest.raises(UploadError, match="besar"):
        svc.save_pending("sess-1", "big.pdf", big)


def test_flush_pending_returns_and_clears(tmp_path):
    svc, r = _make_service(tmp_path)
    r.set("web:pending_uploads:sess-1", json.dumps([
        {"original_filename": "a.pdf", "stored_path": "/tmp/a.pdf",
         "mime_type": "application/pdf", "size_bytes": 100}
    ]).encode())
    result = svc.flush_pending("sess-1")
    assert len(result) == 1
    assert r.get("web:pending_uploads:sess-1") is None


def test_get_pending_returns_empty_list(tmp_path):
    svc, _ = _make_service(tmp_path)
    assert svc.get_pending("sess-no-uploads") == []
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_services/test_upload_service.py -v`
Expected: ImportError

- [ ] **Step 3: Implement UploadService**

```python
# app/web/services/upload_service.py
"""Validasi dan penyimpanan file upload pelapor."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import magic
except ImportError:  # pragma: no cover — platform fallback
    magic = None  # type: ignore[assignment]

MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIMES = {"application/pdf", "image/png", "image/jpeg"}


class UploadError(ValueError):
    """File upload ditolak karena validasi gagal."""


class UploadService:
    def __init__(self, redis: Any, upload_root: Path | str) -> None:
        self._redis = redis
        self._root = Path(upload_root)

    def save_pending(self, session_id: str, filename: str, data: bytes) -> dict:
        """Validasi, simpan ke disk, catat ke Redis pending. Return metadata."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UploadError(f"Ekstensi file tidak diizinkan: {ext}")
        if len(data) > MAX_SIZE_BYTES:
            raise UploadError("File terlalu besar (maks 10 MB).")
        if magic is None:
            raise UploadError("python-magic tidak terinstall di server ini.")
        detected = magic.from_buffer(data, mime=True)
        if detected not in ALLOWED_MIMES:
            raise UploadError(f"MIME type file tidak valid: {detected}")

        month_dir = self._root / datetime.utcnow().strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4()}{ext}"
        stored_path = month_dir / stored_name
        stored_path.write_bytes(data)

        meta = {
            "original_filename": filename,
            "stored_path": str(stored_path),
            "mime_type": detected,
            "size_bytes": len(data),
        }
        key = f"web:pending_uploads:{session_id}"
        existing = json.loads(self._redis.get(key) or b"[]")
        existing.append(meta)
        self._redis.setex(key, 3600, json.dumps(existing).encode())
        return meta

    def flush_pending(self, session_id: str) -> list[dict]:
        """Ambil + hapus pending uploads dari Redis. Return list metadata."""
        key = f"web:pending_uploads:{session_id}"
        raw = self._redis.get(key)
        if raw:
            self._redis.delete(key)
            return json.loads(raw)
        return []

    def get_pending(self, session_id: str) -> list[dict]:
        """Lihat pending uploads tanpa menghapus."""
        key = f"web:pending_uploads:{session_id}"
        return json.loads(self._redis.get(key) or b"[]")
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_upload_service.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/upload_service.py tests/test_web/test_services/test_upload_service.py
git commit -m "feat(web): UploadService with MIME validation and Redis pending"
```

---

## Task 4: ChatService

**Files:**
- Create: `app/web/services/chat_service.py`
- Test: `tests/test_web/test_services/test_chat_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_services/test_chat_service.py
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import fakeredis
import pytest

from app.web.services.chat_service import ChatMessage, ChatService

PENDING_META = {
    "original_filename": "a.pdf",
    "stored_path": "/tmp/a.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 100,
}


def _make_graph(requires_clarification=False, ticket_id="", clarification_msg=""):
    state = {
        "requires_clarification": requires_clarification,
        "clarification_message": clarification_msg,
        "ticket_id": ticket_id,
        "mitigation_recommendation": "Segera isolasi host.",
        "incident_type": "PHISHING",
        "severity": "HIGH",
        "escalation_level": "MEDIUM",
        "confidence_score": 0.9,
    }
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=state)
    return graph


def _make_orchestrator():
    from app.agents.state import IncidentState
    orch = MagicMock()
    orch.initialize_state.return_value = IncidentState(
        raw_input="x", sanitized_input="x", reporter_id="web:abc",
        reporter_name="Test", reporter_contact="", session_id="sess-1",
        timestamp_received="", intent="", requires_clarification=False,
        clarification_message="", incident_type="", severity="",
        confidence_score=0.0, classification_reasoning="",
        retrieved_chunks=[], mitigation_recommendation="", citations=[],
        rag_confidence=0.0, ticket_id="", ticket_status="",
        escalation_level="", notification_sent=False,
        notification_recipients=[], notification_timestamp="",
        processing_errors=[], agent_trace=[],
    )
    return orch


def _make_service(redis=None):
    if redis is None:
        redis = fakeredis.FakeStrictRedis(decode_responses=False)
    return ChatService(redis=redis)


def test_get_history_empty(tmp_path):
    svc = _make_service()
    assert svc.get_history("new-session") == []


def test_get_history_returns_stored(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    msgs = [{"role": "user", "content": "halo", "ts": "2026-01-01"}]
    r.setex("web:chat:sess-1", 86400, json.dumps(msgs).encode())
    svc = _make_service(r)
    assert svc.get_history("sess-1") == msgs


def test_handle_message_clarification(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    graph = _make_graph(requires_clarification=True, clarification_msg="Apa unit Anda?")
    orch = _make_orchestrator()
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="email aneh", graph=graph, orchestrator=orch,
    ))
    assert result["requires_clarification"] is True
    assert result["bot_text"] == "Apa unit Anda?"
    assert result["ticket_id"] is None
    history = svc.get_history("sess-1")
    assert len(history) == 2  # user + assistant


def test_handle_message_ticket_created(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    # seed pending upload
    r.setex("web:pending_uploads:sess-1", 3600, json.dumps([PENDING_META]).encode())
    graph = _make_graph(ticket_id="INC-99")
    orch = _make_orchestrator()

    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="laptop terinfeksi", graph=graph, orchestrator=orch,
        db=db,
    ))
    assert result["ticket_id"] == "INC-99"
    assert result["requires_clarification"] is False
    # pending upload flushed
    assert r.get("web:pending_uploads:sess-1") is None
    # TicketAttachment inserted
    db.add.assert_called_once()


def test_handle_message_timeout_returns_error(tmp_path):
    import asyncio as _asyncio
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    orch = _make_orchestrator()

    async def _slow(state):
        await _asyncio.sleep(60)
        return {}

    graph = MagicMock()
    graph.ainvoke = _slow
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="test", graph=graph, orchestrator=orch,
        timeout=0.01,
    ))
    assert result["error"] is True


def test_clear_history(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    r.setex("web:chat:sess-1", 86400, b"[{}]")
    svc = _make_service(r)
    svc.clear_history("sess-1")
    assert svc.get_history("sess-1") == []
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_services/test_chat_service.py -v`
Expected: ImportError

- [ ] **Step 3: Implement ChatService**

```python
# app/web/services/chat_service.py
"""Layanan chat pelapor: history Redis + pipeline invoke."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HISTORY_TTL = 86400  # 24h


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str
    ts: str


class ChatService:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(self, session_id: str) -> list[dict]:
        raw = self._redis.get(f"web:chat:{session_id}")
        if not raw:
            return []
        return json.loads(raw)

    def _save_history(self, session_id: str, history: list[dict]) -> None:
        self._redis.setex(
            f"web:chat:{session_id}", _HISTORY_TTL, json.dumps(history).encode()
        )

    def clear_history(self, session_id: str) -> None:
        self._redis.delete(f"web:chat:{session_id}")

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def handle_message(
        self,
        *,
        session_id: str,
        reporter_id: str,
        reporter_name: str,
        reporter_contact: str,
        text: str,
        graph: Any,
        orchestrator: Any,
        db: Any = None,
        timeout: float = 30.0,
    ) -> dict:
        """Invoke pipeline dan return dict hasil untuk template."""
        history = self.get_history(session_id)
        ts = datetime.now(timezone.utc).isoformat()
        history.append({"role": "user", "content": text, "ts": ts})

        # Multi-turn context: concat last 3 user messages
        user_msgs = [m["content"] for m in history if m["role"] == "user"]
        context_text = "\n".join(user_msgs[-3:])

        state = orchestrator.initialize_state(
            raw_input=context_text,
            reporter_id=reporter_id,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            session_id=session_id,
        )

        try:
            result = await asyncio.wait_for(graph.ainvoke(state), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Pipeline timeout session=%s", session_id[:8])
            self._save_history(session_id, history)
            return {"error": True, "trace_id": session_id[:8]}

        requires_clarification: bool = result.get("requires_clarification", False)
        ticket_id: Optional[str] = result.get("ticket_id") or None

        if requires_clarification:
            bot_text = result.get("clarification_message", "Mohon berikan informasi lebih lanjut.")
        elif ticket_id:
            bot_text = (
                f"Tiket insiden berhasil dibuat: **{ticket_id}**.\n\n"
                f"{result.get('mitigation_recommendation', '')}"
            ).strip()
            if db is not None:
                self._flush_pending_uploads(session_id, ticket_id, reporter_id, db)
        else:
            bot_text = result.get("mitigation_recommendation", "Respons tidak tersedia.")

        history.append({"role": "assistant", "content": bot_text, "ts": ts})
        self._save_history(session_id, history)

        return {
            "user_text": text,
            "bot_text": bot_text,
            "requires_clarification": requires_clarification,
            "ticket_id": ticket_id,
            "incident_type": result.get("incident_type", ""),
            "severity": result.get("severity", ""),
            "escalation_level": result.get("escalation_level", ""),
            "confidence_score": result.get("confidence_score", 0.0),
            "error": False,
        }

    def _flush_pending_uploads(
        self, session_id: str, ticket_id: str, uploaded_by: str, db: Any
    ) -> None:
        from app.database.models import TicketAttachment
        pending_raw = self._redis.get(f"web:pending_uploads:{session_id}")
        if not pending_raw:
            return
        self._redis.delete(f"web:pending_uploads:{session_id}")
        for meta in json.loads(pending_raw):
            att = TicketAttachment(
                ticket_id=ticket_id,
                original_filename=meta["original_filename"],
                stored_path=meta["stored_path"],
                mime_type=meta["mime_type"],
                size_bytes=meta["size_bytes"],
                uploaded_by=uploaded_by,
            )
            db.add(att)
        db.commit()
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_chat_service.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/chat_service.py tests/test_web/test_services/test_chat_service.py
git commit -m "feat(web): ChatService with Redis history and pipeline invoke"
```

---

## Task 5: get_reporter_session dependency + templates pelapor

**Files:**
- Modify: `app/web/dependencies.py`
- Create: `app/web/templates/pelapor/identitas.html`
- Create: `app/web/templates/pelapor/chat.html`
- Create: `app/web/templates/pelapor/_message.html`
- Create: `app/web/templates/pelapor/_tiket_card.html`
- Create: `app/web/templates/pelapor/_attachment_pill.html`
- Create: `app/web/templates/pelapor/_error_bubble.html`

- [ ] **Step 1: Add get_reporter_session to dependencies.py**

Read current `app/web/dependencies.py` first, then append:

```python
from typing import Optional


class _ReporterNotFound(Exception):
    """Pelapor belum isi identitas — redirect ke /lapor."""
    def __init__(self, location: str = "/lapor") -> None:
        self.location = location


def get_reporter_session(request: Request) -> dict:
    """Pastikan cookie sesi pelapor ada. Redirect ke /lapor jika belum."""
    session = request.session
    if not session.get("session_id") or not session.get("reporter_id"):
        raise _ReporterNotFound("/lapor")
    return {
        "session_id": session["session_id"],
        "reporter_id": session["reporter_id"],
        "reporter_name": session.get("reporter_name", ""),
        "reporter_contact": session.get("reporter_contact", ""),
        "reporter_unit": session.get("reporter_unit", ""),
    }
```

Add exception handler in `app/web/app.py` (same pattern as `_RedirectException`):

```python
from app.web.dependencies import _ReporterNotFound

@app.exception_handler(_ReporterNotFound)
async def _reporter_not_found_handler(request: Request, exc: _ReporterNotFound):
    return RedirectResponse(url=exc.location, status_code=303)
```

- [ ] **Step 2: Create identitas.html**

```html
{# app/web/templates/pelapor/identitas.html #}
{% extends "base.html" %}
{% block title %}Laporkan Insiden — Pusdatin Helpdesk{% endblock %}
{% block layout %}
<div style="display: grid; grid-template-columns: 280px 1fr; min-height: 100vh;">
  <aside style="background: #0f172a; color: #f8fafc; padding: 24px 16px;">
    <h2 style="font-size: 18px; margin-bottom: 8px;">Pusdatin CSIRT</h2>
    <p style="color: #64748b; font-size: 13px;">Sistem Helpdesk Keamanan Siber</p>
  </aside>
  <main style="padding: 48px 64px; background: #f8fafc; display: flex; align-items: center; justify-content: center;">
    <div style="width: 100%; max-width: 480px;">
      <h1 style="font-size: 28px; color: #0f172a; margin-bottom: 8px;">Laporkan Insiden</h1>
      <p style="color: #64748b; margin-bottom: 32px;">Isi identitas Anda sebelum mulai chat.</p>
      {% if error %}
      <div style="background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; padding: 12px; margin-bottom: 16px; color: #dc2626;">{{ error }}</div>
      {% endif %}
      <form method="post" action="/lapor">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div style="margin-bottom: 16px;">
          <label for="reporter_name" style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Nama Lengkap *</label>
          <input id="reporter_name" type="text" name="reporter_name" required class="form-control" placeholder="Nama Anda">
        </div>
        <div style="margin-bottom: 16px;">
          <label for="reporter_contact" style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Kontak (WhatsApp/Email)</label>
          <input id="reporter_contact" type="text" name="reporter_contact" class="form-control" placeholder="08xx atau email@kementan.go.id">
        </div>
        <div style="margin-bottom: 24px;">
          <label for="reporter_unit" style="display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px;">Unit/Divisi</label>
          <input id="reporter_unit" type="text" name="reporter_unit" class="form-control" placeholder="Contoh: Divisi IT Pusdatin">
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%; padding: 12px;">Mulai Laporkan →</button>
      </form>
    </div>
  </main>
</div>
{% endblock %}
```

- [ ] **Step 3: Create chat.html**

```html
{# app/web/templates/pelapor/chat.html #}
{% extends "base.html" %}
{% block title %}Chat Pelapor — Pusdatin Helpdesk{% endblock %}
{% block layout %}
<div style="display: grid; grid-template-columns: 280px 1fr; min-height: 100vh;">
  <aside style="background: #0f172a; color: #f8fafc; padding: 24px 16px; display: flex; flex-direction: column;">
    <h2 style="font-size: 18px; margin-bottom: 24px;">Pusdatin CSIRT</h2>
    <div style="background: #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
      <p style="font-size: 13px; color: #94a3b8; margin-bottom: 4px;">Pelapor</p>
      <p style="font-weight: 600;">{{ reporter.reporter_name }}</p>
      {% if reporter.reporter_unit %}<p style="font-size: 13px; color: #94a3b8;">{{ reporter.reporter_unit }}</p>{% endif %}
      {% if reporter.reporter_contact %}<p style="font-size: 12px; color: #64748b;">{{ reporter.reporter_contact }}</p>{% endif %}
    </div>
    <div style="margin-top: auto;">
      <form method="post" action="/lapor/chat/reset">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn" style="width: 100%; background: transparent; color: #64748b; border: 1px solid #334155; font-size: 13px;">Mulai Sesi Baru</button>
      </form>
    </div>
  </aside>
  <main style="display: flex; flex-direction: column; background: #f8fafc; height: 100vh;">
    <header style="padding: 16px 24px; border-bottom: 1px solid #e2e8f0; background: white;">
      <h1 style="font-size: 18px; color: #0f172a;">Asisten Keamanan Siber</h1>
      <p style="font-size: 13px; color: #64748b;">Ceritakan insiden yang Anda alami. Asisten akan membantu menganalisis dan membuat tiket.</p>
    </header>
    <div id="chat-log" style="flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px;">
      {% for msg in history %}
        {% if msg.role == "user" %}
        <div style="align-self: flex-end; max-width: 70%; background: #2563eb; color: white; padding: 12px 16px; border-radius: 12px 12px 4px 12px;">{{ msg.content }}</div>
        {% else %}
        <div style="align-self: flex-start; max-width: 70%; background: white; border: 1px solid #e2e8f0; padding: 12px 16px; border-radius: 12px 12px 12px 4px;">{{ msg.content }}</div>
        {% endif %}
      {% else %}
      <div style="text-align: center; color: #94a3b8; padding: 48px 0;">Sampaikan insiden keamanan yang Anda alami...</div>
      {% endfor %}
    </div>
    <div id="pending-uploads" style="padding: 0 24px; display: flex; gap: 8px; flex-wrap: wrap;"></div>
    <footer style="padding: 16px 24px; border-top: 1px solid #e2e8f0; background: white;">
      <form id="chat-form"
            hx-post="/lapor/chat/message"
            hx-target="#chat-log"
            hx-swap="beforeend"
            hx-on::after-request="this.reset()"
            hx-indicator="#send-indicator"
            style="display: flex; gap: 8px; align-items: flex-end;">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <textarea name="text" rows="2" required
                  placeholder="Ceritakan insiden yang Anda alami..."
                  style="flex: 1; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; resize: none; font-size: 14px;"></textarea>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <label title="Lampirkan file (PNG, JPG, PDF, max 10 MB)" style="cursor: pointer; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; color: #64748b; font-size: 18px;">
            📎
            <input type="file" accept=".png,.jpg,.jpeg,.pdf" style="display: none;"
                   hx-post="/lapor/chat/upload"
                   hx-target="#pending-uploads"
                   hx-swap="beforeend"
                   hx-encoding="multipart/form-data">
          </label>
          <button type="submit" class="btn btn-primary" style="padding: 8px 16px;">
            <span id="send-indicator" class="htmx-indicator" style="display: none;">⏳</span>
            Kirim
          </button>
        </div>
      </form>
    </footer>
  </main>
</div>
{% endblock %}
```

- [ ] **Step 4: Create HTMX fragment templates**

```html
{# app/web/templates/pelapor/_message.html #}
<div style="align-self: flex-end; max-width: 70%; background: #2563eb; color: white; padding: 12px 16px; border-radius: 12px 12px 4px 12px;">
  {{ user_text }}
</div>
<div style="align-self: flex-start; max-width: 70%; background: white; border: 1px solid #e2e8f0; padding: 12px 16px; border-radius: 12px 12px 12px 4px;">
  {{ bot_text }}
</div>
{% if ticket_id %}
  {% include "pelapor/_tiket_card.html" %}
{% endif %}
```

```html
{# app/web/templates/pelapor/_tiket_card.html #}
<div style="align-self: flex-start; max-width: 70%; background: #eff6ff; border: 2px solid #2563eb; border-radius: 12px; padding: 16px;">
  <p style="font-size: 12px; color: #2563eb; text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">Tiket Dibuat</p>
  <p style="font-family: monospace; font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">{{ ticket_id }}</p>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
    <div><span style="color: #64748b;">Jenis:</span> {{ incident_type }}</div>
    <div><span style="color: #64748b;">Severity:</span> {{ severity }}</div>
    <div><span style="color: #64748b;">Escalation:</span> {{ escalation_level }}</div>
    <div><span style="color: #64748b;">Confidence:</span> {{ "%.0f"|format(confidence_score * 100) }}%</div>
  </div>
  <a href="/lapor/tiket/{{ ticket_id }}" style="display: block; margin-top: 12px; font-size: 13px; color: #2563eb; text-decoration: none;">Lihat status tiket →</a>
</div>
```

```html
{# app/web/templates/pelapor/_attachment_pill.html #}
<span style="display: inline-flex; align-items: center; gap: 6px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 999px; padding: 4px 12px; font-size: 13px;">
  📎 {{ filename }} ({{ size_kb }} KB)
</span>
```

```html
{# app/web/templates/pelapor/_error_bubble.html #}
<div style="align-self: flex-start; max-width: 70%; background: #fee2e2; border: 1px solid #fca5a5; padding: 12px 16px; border-radius: 12px 12px 12px 4px; color: #dc2626; font-size: 14px;">
  Maaf, terjadi kesalahan saat menganalisis laporan Anda.
  {% if trace_id %}<br><small style="color: #94a3b8;">Trace: {{ trace_id }}</small>{% endif %}
</div>
```

- [ ] **Step 5: Commit**

```bash
git add app/web/dependencies.py app/web/templates/pelapor/
git commit -m "feat(web): reporter session dependency + chat/upload templates"
```

---

## Task 6: Pelapor routes

**Files:**
- Create: `app/web/routes/pelapor.py`
- Test: `tests/test_web/test_routes/test_pelapor.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_routes/test_pelapor.py
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database.models import Base
from app.web.dependencies import _ReporterNotFound, get_db_session
from app.web.routes.pelapor import router


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_db_session] = lambda: iter([db])

    @app.exception_handler(_ReporterNotFound)
    async def _h(request: Request, exc: _ReporterNotFound):
        return RedirectResponse(url=exc.location, status_code=303)

    app.include_router(router)
    return TestClient(app)


def test_get_identitas_form(client):
    r = client.get("/lapor")
    assert r.status_code == 200
    assert "Nama Lengkap" in r.text


def test_post_identitas_sets_session(client):
    r = client.post("/lapor", data={
        "reporter_name": "Budi",
        "reporter_contact": "budi@test.id",
        "reporter_unit": "IT",
        "csrf_token": "x",  # CSRF middleware not active in this unit test
    }, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/lapor/chat" in r.headers["location"]


def test_get_chat_redirects_without_session(client):
    r = client.get("/lapor/chat", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/lapor" in r.headers["location"]


def test_get_chat_renders_with_session(client):
    client.post("/lapor", data={
        "reporter_name": "Sari",
        "reporter_contact": "",
        "reporter_unit": "",
        "csrf_token": "x",
    })
    r = client.get("/lapor/chat")
    assert r.status_code == 200
    assert "Asisten Keamanan" in r.text


def test_send_message_returns_bubbles(client):
    # Setup session
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "", "reporter_unit": "", "csrf_token": "x"})
    r = fakeredis.FakeStrictRedis(decode_responses=False)

    mock_result = {
        "requires_clarification": False, "ticket_id": "INC-1",
        "mitigation_recommendation": "Isolasi host.",
        "incident_type": "PHISHING", "severity": "HIGH",
        "escalation_level": "MEDIUM", "confidence_score": 0.9,
    }
    with patch("app.web.routes.pelapor._redis_client", return_value=r), \
         patch("app.web.routes.pelapor._get_graph") as mock_graph_factory, \
         patch("app.web.routes.pelapor._get_orch") as mock_orch_factory:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        mock_graph_factory.return_value = mock_graph
        mock_orch_factory.return_value = MagicMock()
        r2 = client.post("/lapor/chat/message", data={"text": "laptop saya terinfeksi", "csrf_token": "x"})

    assert r2.status_code == 200
    assert "INC-1" in r2.text or "laptop saya terinfeksi" in r2.text


def test_reset_clears_session(client):
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "", "reporter_unit": "", "csrf_token": "x"})
    r = client.post("/lapor/chat/reset", data={"csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (302, 303)


def test_tiket_status_not_found(client):
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "", "reporter_unit": "", "csrf_token": "x"})
    r = client.get("/lapor/tiket/NOPE")
    assert r.status_code == 404
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_pelapor.py -v`
Expected: ImportError

- [ ] **Step 3: Implement pelapor routes**

```python
# app/web/routes/pelapor.py
"""Routes untuk alur pelapor: identitas → chat → status tiket."""
import logging
import uuid
from typing import Optional

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


def _redis_client():
    from app.web.services.auth_service import _redis_client as _rc
    return _rc()


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
def identitas_submit(
    request: Request,
    reporter_name: str = Form(...),
    reporter_contact: str = Form(""),
    reporter_unit: str = Form(""),
    db: Session = Depends(get_db_session),
):
    reporter_name = reporter_name.strip()
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
    request.session["reporter_contact"] = reporter_contact.strip()
    request.session["reporter_unit"] = reporter_unit.strip()
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
        return HTMLResponse(f'<p style="color: #dc2626; font-size: 13px;">{exc}</p>')

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
    return templates.TemplateResponse(
        "pelapor/_tiket_card.html",
        {
            "request": request,
            "ticket_id": ticket.ticket_id,
            "incident_type": ticket.incident_type,
            "severity": ticket.severity,
            "escalation_level": ticket.escalation_level or "—",
            "confidence_score": float(ticket.confidence_score or 0),
        },
    )
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_pelapor.py -v`
Expected: 7 PASS (test_send_message mungkin perlu mock adjustment — lihat Notes di bawah)

**Note:** `test_send_message_returns_bubbles` mungkin gagal jika `_get_graph` memanggil `_build_pipeline()` yang butuh Qdrant. Pastikan mock `_get_graph` terpatch dengan benar — patch `app.web.routes.pelapor._get_graph`, bukan `app.api.dependencies.get_helpdesk_graph`.

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/pelapor.py tests/test_web/test_routes/test_pelapor.py
git commit -m "feat(web): pelapor routes (identitas, chat, upload, reset, tiket status)"
```

---

## Task 7: Wire pelapor router + update exception handler

**Files:**
- Modify: `app/web/app.py`

- [ ] **Step 1: Update app.py**

```python
# Tambah import di bagian atas:
from app.web.dependencies import _ReporterNotFound
from app.web.routes.pelapor import router as pelapor_router

# Dalam register_web(), setelah exception handler _RedirectException, tambah:
@app.exception_handler(_ReporterNotFound)
async def _reporter_not_found_handler(request: Request, exc: _ReporterNotFound):
    return RedirectResponse(url=exc.location, status_code=303)

# Tambah router:
app.include_router(pelapor_router)
```

- [ ] **Step 2: Verify existing tests masih pass**

Run: `pytest tests/test_web/ -v`
Expected: semua PASS

- [ ] **Step 3: Commit**

```bash
git add app/web/app.py app/web/dependencies.py
git commit -m "chore(web): wire pelapor router + ReporterNotFound exception handler"
```

---

## Task 8: Integration test pelapor flow

**Files:**
- Create: `tests/test_web/test_integration/test_reporter_flow.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_web/test_integration/test_reporter_flow.py
"""End-to-end: isi identitas → chat → tiket terbentuk."""
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, IncidentTicket
from app.main import app as fastapi_app
from app.web.dependencies import get_db_session
import app.web.routes.pelapor as pelapor_mod


_PIPELINE_RESULT = {
    "requires_clarification": False,
    "ticket_id": "INC-WEB-1",
    "mitigation_recommendation": "Isolasi host segera.",
    "incident_type": "PHISHING",
    "severity": "HIGH",
    "escalation_level": "MEDIUM",
    "confidence_score": 0.88,
    "clarification_message": "",
    "processing_errors": [],
}


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    fastapi_app.dependency_overrides[get_db_session] = lambda: iter([db])

    r = fakeredis.FakeStrictRedis(decode_responses=False)
    monkeypatch.setattr(pelapor_mod, "_redis_client", lambda: r)

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_PIPELINE_RESULT)
    monkeypatch.setattr(pelapor_mod, "_get_graph", lambda db: mock_graph)
    monkeypatch.setattr(pelapor_mod, "_get_orch", lambda: MagicMock())

    yield TestClient(fastapi_app)

    fastapi_app.dependency_overrides = {}
    db.close()


def test_reporter_full_flow(client):
    # 1. GET identitas form
    r = client.get("/lapor")
    assert r.status_code == 200
    assert "Nama Lengkap" in r.text

    # 2. POST identitas → redirect ke chat
    r = client.post("/lapor", data={
        "reporter_name": "Sari Dewi",
        "reporter_contact": "sari@kementan.go.id",
        "reporter_unit": "Divisi IT",
        "csrf_token": "x",
    }, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/lapor/chat" in r.headers["location"]

    # 3. GET chat page
    r = client.get("/lapor/chat")
    assert r.status_code == 200
    assert "Asisten Keamanan" in r.text
    assert "Sari Dewi" in r.text

    # 4. POST message → fragment with tiket card
    r = client.post("/lapor/chat/message", data={
        "text": "Email phishing dari HR palsu, saya klik link-nya",
        "csrf_token": "x",
    })
    assert r.status_code == 200
    assert "INC-WEB-1" in r.text

    # 5. GET tiket status
    r = client.get("/lapor/tiket/INC-WEB-1")
    # Will 404 because ticket not in DB (pipeline mocked), that's OK —
    # in real run, TicketManagerAgent inserts it
    assert r.status_code in (200, 404)

    # 6. Reset session
    r = client.post("/lapor/chat/reset", data={"csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (302, 303)

    # 7. Chat now redirects to identitas
    r = client.get("/lapor/chat", follow_redirects=False)
    assert r.status_code in (302, 303)
```

- [ ] **Step 2: Run, verify PASS**

Run: `pytest tests/test_web/test_integration/test_reporter_flow.py -v`
Expected: PASS

- [ ] **Step 3: Run full suite**

Run: `pytest tests/test_web/ -v`
Expected: semua PASS

- [ ] **Step 4: Commit + tag**

```bash
git add tests/test_web/test_integration/test_reporter_flow.py
git commit -m "test(web): end-to-end reporter flow integration test"
git tag plan-c-complete
```

---

## Task 9: Manual smoke test checklist

**Files:** (none — verifikasi manual)

- [ ] **Step 1: Apply migration**

```bash
alembic upgrade head
```

Expected: `ticket_attachments` table ter-create.

- [ ] **Step 2: Start server**

```bash
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Browser flow**

1. Buka `http://localhost:8000/lapor` → form identitas
2. Isi nama, kontak, unit → Submit → redirect ke `/lapor/chat`
3. Ketik pesan "laptop saya terinfeksi virus" → Kirim → tunggu respons pipeline (5-15 detik)
4. Verify: bubble user biru, bubble asisten putih, tiket card muncul jika tiket terbentuk
5. Klik 📎 → pilih file PDF/PNG → pill upload muncul di bawah form
6. Kirim pesan berikutnya → attachment ter-link ke tiket
7. Klik "Mulai Sesi Baru" → redirect ke `/lapor`
8. (Opsional) Buka `/lapor/tiket/{ticket_id}` → info tiket tampil

- [ ] **Step 4: Verifikasi Redis**

```bash
redis-cli keys "web:*"
# Expected: web:chat:{session_id} ada, TTL ~24h
```

---

## Notes for the Executing Subagent

- **JANGAN sentuh `IncidentState`**. ChatService mengisi `raw_input` dari concat last-3 user messages — tidak extend schema.
- **`_get_graph(db)`** memanggil `get_helpdesk_graph(db)` dari `app/api/dependencies.py` yang membutuhkan Qdrant + OpenAI. Jika tidak tersedia di test environment, mock via `monkeypatch.setattr(pelapor_mod, "_get_graph", ...)`.
- **python-magic**: `magic.from_buffer(data, mime=True)` — bukan `magic.from_file()`. Jangan pakai Content-Type header dari browser (mudah dipalsukan).
- **CSRF**: Route pelapor sudah di-cover CSRFMiddleware dari Plan A. Form template sudah include `csrf_token` hidden field. Middleware tidak aktif di unit test route (tidak ada CSRFMiddleware terpasang di fixture), sehingga test bisa kirim form tanpa token valid.
- **slowapi decorator**: Gunakan `Form(...)` style, bukan `Annotated[str, Form()]` — diketahui incompatible dari Plan A.
- **`/lapor` tanpa trailing slash**: FastAPI default redirect 307 untuk trailing slash mismatch. Route didefinisikan sebagai `@router.get("")` (bukan `"/"`).
- **Upload test**: `test_pelapor.py::test_send_message_returns_bubbles` memerlukan patch `_redis_client`, `_get_graph`, `_get_orch` di module `app.web.routes.pelapor`. Pastikan patch target benar.
- **TicketAttachment FK**: Tidak pakai `ForeignKey` constraint agar SQLite (test) tidak komplain. Constraint logis, bukan DDL.
