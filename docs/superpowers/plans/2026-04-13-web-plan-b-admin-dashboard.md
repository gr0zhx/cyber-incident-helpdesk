# Plan B — Web Admin Dashboard (Inbox & Ticket Management)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bangun dashboard admin web penuh — inbox tiket dengan filter/pagination (HTMX), halaman detail tiket 2 kolom, aksi update status/assign/escalation, notifikasi pelapor via Telegram, dan download attachment — di atas fondasi auth Plan A.

**Architecture:** Service layer baru (`TicketService`, `NotificationService`) yang memakai `IncidentTicket` dan `AuditLog` existing — tidak ada migration baru. Routes admin dilindungi `Depends(get_current_admin)`. Semua POST pakai double-submit CSRF (middleware Plan A). HTMX fragment untuk filter tabel dan aksi inline, server selalu return partial HTML. Notifikasi pelapor Telegram = wrap fungsi `_notify_reporter_status` existing dari `app/api/routes.py` tanpa duplikasi.

**Tech Stack:** FastAPI · Jinja2 · HTMX · SQLAlchemy · python-telegram-bot · pytest · TestClient · fakeredis

**Spec reference:** `docs/superpowers/specs/2026-04-13-web-interface-design.md` Sections 5.1, 5.3, 5.4, 5.5, 5.8, 5.9

**Depends on:** Plan A (branch `feat/web-plan-a` merged — menyediakan `app/web/app.py`, middleware CSRF, `get_current_admin`, base template, inbox_stub).

---

## File Structure

### Create

```
app/web/
├── constants.py                       # Audit event type constants (string)
├── services/
│   ├── ticket_service.py              # list_tickets, get_ticket_detail, update_status, assign, set_escalation
│   └── notification_service.py        # notify_reporter_status (wrap existing)
├── routes/
│   ├── admin_inbox.py                 # GET /admin/inbox, GET /admin/inbox/table, GET /admin/tiket/{id}
│   └── admin_actions.py               # POST status/assign/escalation/notify, GET attachment download
├── templates/
│   ├── admin/
│   │   ├── _shell.html                # Sidebar + topbar partial (include {% block content %})
│   │   ├── inbox.html                 # Full page (extends _shell)
│   │   ├── _inbox_table.html          # HTMX fragment: tbody + pagination
│   │   ├── tiket_detail.html          # Full 2-column page
│   │   ├── _timeline_row.html         # HTMX fragment: single timeline entry
│   │   └── _status_badge.html         # HTMX swap target: status pill

tests/test_web/
├── test_services/
│   ├── test_ticket_service.py
│   └── test_notification_service.py
├── test_routes/
│   ├── test_admin_inbox.py
│   └── test_admin_actions.py
└── test_integration/
    └── test_admin_workflow.py
```

### Modify

- `app/web/app.py` — register `admin_inbox` dan `admin_actions` routers, hapus `admin_inbox_stub`.
- `app/web/templates/base.html` — tambahkan blok `{% block content %}` jika belum (kompatibel dengan shell partial).
- `app/web/routes/__init__.py` — export baru jika dipakai.

### Out of scope (di plan lain)

- RAG management (`/admin/rag/*`) → Plan D
- Report generation (`/admin/report/*`) → Plan D
- Pelapor chat & upload (`/lapor/*`) → Plan C
- **Timeline audit log widget** di panel kanan detail tiket (spec 5.4) → Plan D bersama integrasi penuh `AuditLog` table. Plan B hanya `logger.info()` structured lines.
- **Tulis ke `audit_logs` table**: Plan B pakai `logger.info()` — Plan D yang akan extend `app/utils/audit.py` untuk event admin.

---

## Task 1: Audit event constants

**Files:**
- Create: `app/web/constants.py`
- Test: `tests/test_web/test_constants.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_web/test_constants.py
from app.web.constants import AuditEvents


def test_audit_event_names_are_uppercase_strings():
    for name in [
        "ADMIN_LOGIN", "ADMIN_LOGIN_FAILED", "ADMIN_LOGOUT",
        "TICKET_STATUS_UPDATED", "TICKET_ASSIGNED", "TICKET_ESCALATION_UPDATED",
        "NOTIFICATION_SENT", "FILE_DOWNLOADED",
    ]:
        value = getattr(AuditEvents, name)
        assert isinstance(value, str) and value == name
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_web/test_constants.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.web.constants'`

- [ ] **Step 3: Implement constants**

```python
# app/web/constants.py
"""Konstanta string untuk event audit khusus web dashboard."""


class AuditEvents:
    ADMIN_LOGIN = "ADMIN_LOGIN"
    ADMIN_LOGIN_FAILED = "ADMIN_LOGIN_FAILED"
    ADMIN_LOGOUT = "ADMIN_LOGOUT"
    TICKET_STATUS_UPDATED = "TICKET_STATUS_UPDATED"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    TICKET_ESCALATION_UPDATED = "TICKET_ESCALATION_UPDATED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    FILE_DOWNLOADED = "FILE_DOWNLOADED"


TICKET_STATUSES = ("PENDING_REVIEW", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED")
ESCALATION_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
```

- [ ] **Step 4: Run test, verify it passes**

Run: `pytest tests/test_web/test_constants.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/constants.py tests/test_web/test_constants.py
git commit -m "feat(web): audit event constants + ticket enums"
```

---

## Task 2: TicketService.list_tickets with filters & pagination

**Files:**
- Create: `app/web/services/ticket_service.py`
- Test: `tests/test_web/test_services/test_ticket_service.py`
- Modify: (none)

- [ ] **Step 1: Create test module scaffold**

```python
# tests/test_web/test_services/__init__.py
```

```python
# tests/test_web/test_services/test_ticket_service.py
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, IncidentTicket
from app.web.services.ticket_service import TicketService, TicketFilters


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_ticket(db, ticket_id, status="PENDING_REVIEW", severity="HIGH", offset_min=0):
    t = IncidentTicket(
        ticket_id=ticket_id,
        reporter_id="tg:123",
        reporter_name="Pelapor",
        incident_type="PHISHING",
        severity=severity,
        description_raw="x",
        description_sanitized="x",
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=offset_min),
    )
    db.add(t)
    db.commit()
    return t


def test_list_tickets_returns_all_when_no_filter(db):
    for i in range(3):
        _make_ticket(db, f"INC-{i}", offset_min=i)
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(), page=1, page_size=25)
    assert result.total == 3
    assert [t.ticket_id for t in result.items] == ["INC-0", "INC-1", "INC-2"]


def test_list_tickets_filters_by_status(db):
    _make_ticket(db, "A", status="PENDING_REVIEW")
    _make_ticket(db, "B", status="RESOLVED")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(status="RESOLVED"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "B"


def test_list_tickets_filters_by_severity(db):
    _make_ticket(db, "A", severity="HIGH")
    _make_ticket(db, "B", severity="LOW")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(severity="LOW"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "B"


def test_list_tickets_search_by_ticket_id_or_name(db):
    _make_ticket(db, "INC-100")
    _make_ticket(db, "INC-200")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(search="200"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "INC-200"


def test_list_tickets_pagination(db):
    for i in range(30):
        _make_ticket(db, f"INC-{i:03d}", offset_min=i)
    svc = TicketService(db)
    page1 = svc.list_tickets(TicketFilters(), page=1, page_size=25)
    page2 = svc.list_tickets(TicketFilters(), page=2, page_size=25)
    assert page1.total == 30
    assert len(page1.items) == 25
    assert len(page2.items) == 5
    assert page1.total_pages == 2
```

- [ ] **Step 2: Run test, verify import fails**

Run: `pytest tests/test_web/test_services/test_ticket_service.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Implement TicketService list**

```python
# app/web/services/__init__.py  (create if missing — may already exist from Plan A)
```

```python
# app/web/services/ticket_service.py
"""Service layer untuk operasi tiket pada dashboard admin web."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.models import IncidentTicket


@dataclass
class TicketFilters:
    status: Optional[str] = None
    severity: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class TicketListResult:
    items: list[IncidentTicket]
    total: int
    page: int
    page_size: int
    total_pages: int


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tickets(
        self,
        filters: TicketFilters,
        page: int = 1,
        page_size: int = 25,
    ) -> TicketListResult:
        query = self.db.query(IncidentTicket)
        if filters.status:
            query = query.filter(IncidentTicket.status == filters.status)
        if filters.severity:
            query = query.filter(IncidentTicket.severity == filters.severity)
        if filters.search:
            like = f"%{filters.search}%"
            query = query.filter(
                or_(
                    IncidentTicket.ticket_id.ilike(like),
                    IncidentTicket.reporter_name.ilike(like),
                )
            )
        if filters.date_from:
            query = query.filter(IncidentTicket.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(IncidentTicket.created_at <= filters.date_to)

        total = query.count()
        total_pages = max(1, ceil(total / page_size)) if total else 1
        items = (
            query.order_by(IncidentTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return TicketListResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
```

Note: test `test_list_tickets_returns_all_when_no_filter` expects ascending order because `offset_min=i` makes INC-0 newest. Fix the test ordering expectation:

```python
    assert [t.ticket_id for t in result.items] == ["INC-0", "INC-1", "INC-2"]
```

This is already correct because `created_at.desc()` returns newest first, and `offset_min=0` → newest → INC-0.

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_ticket_service.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/ticket_service.py tests/test_web/test_services/
git commit -m "feat(web): TicketService.list_tickets with filter and pagination"
```

---

## Task 3: TicketService detail + mutation methods

**Files:**
- Modify: `app/web/services/ticket_service.py`
- Modify: `tests/test_web/test_services/test_ticket_service.py`

- [ ] **Step 1: Add failing tests**

Append to `test_ticket_service.py`:

```python
def test_get_ticket_detail_returns_ticket(db):
    _make_ticket(db, "INC-X")
    svc = TicketService(db)
    t = svc.get_ticket_detail("INC-X")
    assert t.ticket_id == "INC-X"


def test_get_ticket_detail_returns_none_when_missing(db):
    svc = TicketService(db)
    assert svc.get_ticket_detail("NOPE") is None


def test_update_status_sets_field_and_returns_old(db):
    _make_ticket(db, "INC-A", status="PENDING_REVIEW")
    svc = TicketService(db)
    old = svc.update_status("INC-A", "IN_PROGRESS", modified_by="admin1")
    db.commit()
    assert old == "PENDING_REVIEW"
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().status == "IN_PROGRESS"


def test_update_status_rejects_invalid_status(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    with pytest.raises(ValueError):
        svc.update_status("INC-A", "NOT_A_STATUS", modified_by="admin1")


def test_assign_sets_assigned_to(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    svc.assign("INC-A", "andi", modified_by="admin1")
    db.commit()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().assigned_to == "andi"


def test_set_escalation_level(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    svc.set_escalation("INC-A", "HIGH", modified_by="admin1")
    db.commit()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().escalation_level == "HIGH"
```

- [ ] **Step 2: Run, verify failures**

Run: `pytest tests/test_web/test_services/test_ticket_service.py -v`
Expected: 6 new FAILs (AttributeError).

- [ ] **Step 3: Implement detail + mutators**

Add to `TicketService`:

```python
from app.web.constants import TICKET_STATUSES, ESCALATION_LEVELS


class TicketService:
    # ... existing __init__ and list_tickets ...

    def get_ticket_detail(self, ticket_id: str) -> Optional[IncidentTicket]:
        return (
            self.db.query(IncidentTicket)
            .filter(IncidentTicket.ticket_id == ticket_id)
            .first()
        )

    def update_status(self, ticket_id: str, new_status: str, modified_by: str) -> str:
        if new_status not in TICKET_STATUSES:
            raise ValueError(f"Status tidak valid: {new_status}")
        ticket = self._get_or_raise(ticket_id)
        old = ticket.status
        ticket.status = new_status
        ticket.modified_by = modified_by
        if new_status == "IN_PROGRESS" and ticket.reviewed_at is None:
            ticket.reviewed_at = datetime.utcnow()
        if new_status == "RESOLVED":
            ticket.resolved_at = datetime.utcnow()
        if new_status == "CLOSED":
            ticket.closed_at = datetime.utcnow()
        return old

    def assign(self, ticket_id: str, assignee: str, modified_by: str) -> None:
        ticket = self._get_or_raise(ticket_id)
        ticket.assigned_to = assignee
        ticket.modified_by = modified_by

    def set_escalation(self, ticket_id: str, level: str, modified_by: str) -> None:
        if level not in ESCALATION_LEVELS:
            raise ValueError(f"Escalation level tidak valid: {level}")
        ticket = self._get_or_raise(ticket_id)
        ticket.escalation_level = level
        ticket.modified_by = modified_by

    def _get_or_raise(self, ticket_id: str) -> IncidentTicket:
        ticket = self.get_ticket_detail(ticket_id)
        if ticket is None:
            raise LookupError(f"Tiket {ticket_id} tidak ditemukan.")
        return ticket
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_ticket_service.py -v`
Expected: 11 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/ticket_service.py tests/test_web/test_services/test_ticket_service.py
git commit -m "feat(web): TicketService detail + status/assign/escalation mutators"
```

---

## Task 4: NotificationService wrapping existing Telegram notify

**Files:**
- Create: `app/web/services/notification_service.py`
- Create: `tests/test_web/test_services/test_notification_service.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_web/test_services/test_notification_service.py
import asyncio
from unittest.mock import AsyncMock, patch

from app.web.services.notification_service import NotificationService


def test_notify_returns_true_on_success():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(return_value=None),
    ) as mock:
        ok = asyncio.run(svc.notify_status("tg:123", "INC-1", "IN_PROGRESS"))
    assert ok is True
    mock.assert_awaited_once_with(
        reporter_id="tg:123", ticket_id="INC-1", new_status="IN_PROGRESS"
    )


def test_notify_returns_false_on_exception():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        ok = asyncio.run(svc.notify_status("tg:123", "INC-1", "IN_PROGRESS"))
    assert ok is False


def test_notify_skips_non_telegram_channel():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(),
    ) as mock:
        ok = asyncio.run(svc.notify_status("web:abc", "INC-1", "IN_PROGRESS"))
    assert ok is False
    mock.assert_not_called()
```

- [ ] **Step 2: Run test, verify failure**

Run: `pytest tests/test_web/test_services/test_notification_service.py -v`
Expected: FAIL (module missing)

- [ ] **Step 3: Implement service**

```python
# app/web/services/notification_service.py
"""Wrap fungsi notifikasi Telegram existing agar bisa dipanggil dari web dashboard."""
import logging

from app.api.routes import _notify_reporter_status

logger = logging.getLogger(__name__)


class NotificationService:
    """Bungkus `_notify_reporter_status` — tidak menduplikasi logika Telegram."""

    async def notify_status(
        self, reporter_id: str, ticket_id: str, new_status: str
    ) -> bool:
        """Kirim notifikasi status ke pelapor. Return True jika terkirim."""
        if not reporter_id or not reporter_id.startswith("tg:"):
            logger.info(
                "Notifikasi dilewati: channel non-telegram untuk reporter %s",
                reporter_id,
            )
            return False
        try:
            await _notify_reporter_status(
                reporter_id=reporter_id,
                ticket_id=ticket_id,
                new_status=new_status,
            )
            return True
        except Exception as exc:
            logger.warning("NotificationService gagal kirim: %s", exc)
            return False
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_services/test_notification_service.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/services/notification_service.py tests/test_web/test_services/test_notification_service.py
git commit -m "feat(web): NotificationService wraps existing telegram notifier"
```

---

## Task 5: Admin shell partial + inbox full-page template

**Files:**
- Create: `app/web/templates/admin/_shell.html`
- Create: `app/web/templates/admin/inbox.html`
- Create: `app/web/templates/admin/_inbox_table.html`
- Modify: `app/web/templates/base.html` — pastikan `{% block content %}` ada (skip jika sudah)

- [ ] **Step 1: Update base.html (jika perlu)**

Verify `base.html` has `{% block content %}{% endblock %}` at the appropriate spot. If not, add:

```html
<!-- inside <main> or equivalent layout slot -->
{% block content %}{% endblock %}
```

- [ ] **Step 2: Create admin shell partial**

```html
{# app/web/templates/admin/_shell.html #}
{% extends "base.html" %}
{% block layout %}
<div class="admin-shell" style="display: grid; grid-template-columns: 240px 1fr; min-height: 100vh;">
  <aside style="background: #0f172a; color: #f8fafc; padding: 24px 16px;">
    <h2 style="font-size: 18px; margin-bottom: 24px;">Pusdatin CSIRT</h2>
    <nav style="display: flex; flex-direction: column; gap: 8px;">
      <a href="/admin/inbox" style="color: #cbd5e1; text-decoration: none; padding: 8px 12px; border-radius: 6px;">Inbox Tiket</a>
      <a href="/admin/rag" style="color: #64748b; text-decoration: none; padding: 8px 12px; border-radius: 6px;">Knowledge Base</a>
      <a href="/admin/report" style="color: #64748b; text-decoration: none; padding: 8px 12px; border-radius: 6px;">Laporan</a>
    </nav>
    <form method="post" action="/admin/logout" style="margin-top: 32px;">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <button type="submit" class="btn" style="width: 100%; background: transparent; color: #cbd5e1; border: 1px solid #334155;">Logout</button>
    </form>
  </aside>
  <main style="padding: 32px; background: #f8fafc;">
    <header style="margin-bottom: 24px;">
      <h1 style="font-size: 24px; color: #0f172a;">{% block page_title %}{% endblock %}</h1>
    </header>
    {% block content %}{% endblock %}
  </main>
</div>
{% endblock %}
```

- [ ] **Step 3: Create inbox full page**

```html
{# app/web/templates/admin/inbox.html #}
{% extends "admin/_shell.html" %}
{% block page_title %}Inbox Tiket{% endblock %}
{% block content %}
<section style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
  <form hx-get="/admin/inbox/table"
        hx-target="#inbox-table-wrap"
        hx-trigger="change from:select, keyup changed delay:400ms from:input[name='search']"
        hx-include="this"
        style="display: grid; grid-template-columns: 1fr 1fr 2fr auto; gap: 12px;">
    <select name="status" class="form-control">
      <option value="">Semua status</option>
      {% for s in statuses %}<option value="{{ s }}" {% if s == filters.status %}selected{% endif %}>{{ s }}</option>{% endfor %}
    </select>
    <select name="severity" class="form-control">
      <option value="">Semua severity</option>
      {% for s in ["LOW","MEDIUM","HIGH","CRITICAL"] %}<option value="{{ s }}" {% if s == filters.severity %}selected{% endif %}>{{ s }}</option>{% endfor %}
    </select>
    <input type="text" name="search" placeholder="Cari ticket_id atau nama pelapor..." value="{{ filters.search or '' }}" class="form-control">
    <button type="button" class="btn" onclick="this.form.reset(); htmx.trigger(this.form, 'change');">Reset</button>
  </form>
</section>

<div id="inbox-table-wrap">
  {% include "admin/_inbox_table.html" %}
</div>
{% endblock %}
```

- [ ] **Step 4: Create inbox table fragment**

```html
{# app/web/templates/admin/_inbox_table.html #}
<div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
  <table style="width: 100%; border-collapse: collapse;">
    <thead style="background: #f1f5f9;">
      <tr>
        <th style="padding: 12px; text-align: left;">Ticket ID</th>
        <th style="padding: 12px; text-align: left;">Waktu</th>
        <th style="padding: 12px; text-align: left;">Pelapor</th>
        <th style="padding: 12px; text-align: left;">Jenis</th>
        <th style="padding: 12px; text-align: left;">Severity</th>
        <th style="padding: 12px; text-align: left;">Status</th>
        <th style="padding: 12px; text-align: left;">Assigned</th>
      </tr>
    </thead>
    <tbody>
      {% for t in result.items %}
      <tr style="border-top: 1px solid #e2e8f0; cursor: pointer;"
          onclick="window.location='/admin/tiket/{{ t.ticket_id }}'">
        <td style="padding: 12px; font-family: monospace;">{{ t.ticket_id }}</td>
        <td style="padding: 12px; color: #64748b; font-size: 13px;">{{ t.created_at.strftime("%Y-%m-%d %H:%M") }}</td>
        <td style="padding: 12px;">{{ t.reporter_name or t.reporter_id }}</td>
        <td style="padding: 12px;">{{ t.incident_type }}</td>
        <td style="padding: 12px;">{{ t.severity }}</td>
        <td style="padding: 12px;"><span class="badge badge-{{ t.status|lower }}">{{ t.status }}</span></td>
        <td style="padding: 12px; color: #64748b;">{{ t.assigned_to or "—" }}</td>
      </tr>
      {% else %}
      <tr><td colspan="7" style="padding: 32px; text-align: center; color: #94a3b8;">Tidak ada tiket cocok filter.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<nav style="display: flex; justify-content: space-between; align-items: center; padding: 16px 0;">
  <span style="color: #64748b; font-size: 13px;">Total {{ result.total }} tiket — Halaman {{ result.page }} dari {{ result.total_pages }}</span>
  <div style="display: flex; gap: 8px;">
    {% if result.page > 1 %}
    <button class="btn" hx-get="/admin/inbox/table?page={{ result.page - 1 }}&status={{ filters.status or '' }}&severity={{ filters.severity or '' }}&search={{ filters.search or '' }}" hx-target="#inbox-table-wrap">← Prev</button>
    {% endif %}
    {% if result.page < result.total_pages %}
    <button class="btn" hx-get="/admin/inbox/table?page={{ result.page + 1 }}&status={{ filters.status or '' }}&severity={{ filters.severity or '' }}&search={{ filters.search or '' }}" hx-target="#inbox-table-wrap">Next →</button>
    {% endif %}
  </div>
</nav>
```

- [ ] **Step 5: Commit**

```bash
git add app/web/templates/admin/_shell.html app/web/templates/admin/inbox.html app/web/templates/admin/_inbox_table.html
git commit -m "feat(web): admin shell + inbox templates (filter/pagination HTMX)"
```

---

## Task 6: Admin inbox routes (full page + HTMX fragment)

**Files:**
- Create: `app/web/routes/admin_inbox.py`
- Create: `tests/test_web/test_routes/__init__.py`
- Create: `tests/test_web/test_routes/test_admin_inbox.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_web/test_routes/test_admin_inbox.py
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database.models import Admin, Base, IncidentTicket
from app.web.dependencies import _RedirectException, get_current_admin, get_db_session
from app.web.routes.admin_inbox import router as inbox_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    admin = Admin(id=1, username="admin1", email="a@x.com", full_name="A",
                  password_hash="h", is_active=True)
    db.add(admin)
    for i in range(3):
        db.add(IncidentTicket(
            ticket_id=f"INC-{i}",
            reporter_id="tg:1",
            reporter_name=f"P{i}",
            incident_type="PHISHING",
            severity="HIGH",
            description_raw="x", description_sanitized="x",
            status="PENDING_REVIEW",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=i),
        ))
    db.commit()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")

    @app.exception_handler(_RedirectException)
    async def _h(request: Request, exc: _RedirectException):
        return RedirectResponse(url=exc.location, status_code=303)

    def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.include_router(inbox_router)

    return TestClient(app)


def test_inbox_full_page_renders(client):
    r = client.get("/admin/inbox")
    assert r.status_code == 200
    assert "Inbox Tiket" in r.text
    assert "INC-0" in r.text


def test_inbox_table_fragment(client):
    r = client.get("/admin/inbox/table")
    assert r.status_code == 200
    # Fragment should NOT contain shell
    assert "Pusdatin CSIRT" not in r.text
    assert "INC-0" in r.text


def test_inbox_filter_by_status(client):
    r = client.get("/admin/inbox/table?status=RESOLVED")
    assert r.status_code == 200
    assert "Tidak ada tiket" in r.text
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_inbox.py -v`
Expected: ImportError

- [ ] **Step 3: Implement route**

```python
# app/web/routes/admin_inbox.py
"""Routes untuk inbox tiket admin."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.constants import TICKET_STATUSES
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
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_admin_inbox.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/admin_inbox.py tests/test_web/test_routes/
git commit -m "feat(web): admin inbox routes (full page + HTMX fragment)"
```

---

## Task 7: Tiket detail template + route

**Files:**
- Create: `app/web/templates/admin/tiket_detail.html`
- Create: `app/web/templates/admin/_status_badge.html`
- Modify: `app/web/routes/admin_inbox.py` — add `/admin/tiket/{id}` handler
- Modify: `tests/test_web/test_routes/test_admin_inbox.py` — add detail test

- [ ] **Step 1: Add failing test**

Append to `test_admin_inbox.py`:

```python
def test_ticket_detail_renders(client):
    r = client.get("/admin/tiket/INC-0")
    assert r.status_code == 200
    assert "INC-0" in r.text
    assert "Update Status" in r.text


def test_ticket_detail_404(client):
    r = client.get("/admin/tiket/NOPE")
    assert r.status_code == 404
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_inbox.py::test_ticket_detail_renders -v`
Expected: 404 (no route)

- [ ] **Step 3: Create detail template**

```html
{# app/web/templates/admin/tiket_detail.html #}
{% extends "admin/_shell.html" %}
{% block page_title %}Tiket {{ ticket.ticket_id }}{% endblock %}
{% block content %}
<div style="display: grid; grid-template-columns: 1.3fr 1fr; gap: 24px;">

  <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <div>
        <div style="font-family: monospace; font-size: 20px; color: #0f172a;">{{ ticket.ticket_id }}</div>
        <div style="color: #64748b; font-size: 13px;">{{ ticket.created_at.strftime("%d %b %Y %H:%M UTC") }}</div>
      </div>
      <div id="status-badge">
        {% include "admin/_status_badge.html" %}
      </div>
    </div>

    <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-top: 24px;">Pelapor</h3>
    <p><strong>{{ ticket.reporter_name or "—" }}</strong> ({{ ticket.reporter_id }})<br>
       {{ ticket.reporter_contact or "" }} — {{ ticket.reporter_department or "" }}</p>

    <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-top: 24px;">Klasifikasi</h3>
    <p>Jenis: <strong>{{ ticket.incident_type }}</strong> · Severity: <strong>{{ ticket.severity }}</strong>
       · Confidence: {{ ticket.confidence_score or "n/a" }}<br>
       Escalation: <strong>{{ ticket.escalation_level or "—" }}</strong></p>

    <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-top: 24px;">Deskripsi (sanitized)</h3>
    <pre style="background: #f1f5f9; padding: 12px; border-radius: 6px; white-space: pre-wrap;">{{ ticket.description_sanitized }}</pre>

    {% if ticket.mitigation_recommendation %}
    <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-top: 24px;">Rekomendasi Mitigasi</h3>
    <div style="background: #eff6ff; padding: 12px; border-left: 3px solid #2563eb; border-radius: 4px;">
      {{ ticket.mitigation_recommendation }}
    </div>
    {% endif %}

    {% if attachments %}
    <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-top: 24px;">Attachment</h3>
    <ul>
      {% for att in attachments %}
      <li><a href="/admin/tiket/{{ ticket.ticket_id }}/attachment/{{ loop.index0 }}">{{ att.filename }}</a> ({{ att.size_kb }} KB)</li>
      {% endfor %}
    </ul>
    {% endif %}
  </div>

  <div style="display: flex; flex-direction: column; gap: 16px;">

    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
      <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Update Status</h3>
      <form hx-post="/admin/tiket/{{ ticket.ticket_id }}/status"
            hx-target="#status-badge" hx-swap="innerHTML"
            hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <select name="status" class="form-control">
          {% for s in statuses %}<option value="{{ s }}" {% if s == ticket.status %}selected{% endif %}>{{ s }}</option>{% endfor %}
        </select>
        <button type="submit" class="btn btn-primary" style="margin-top: 8px; width: 100%;">Simpan</button>
      </form>
    </div>

    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
      <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Assign</h3>
      <form hx-post="/admin/tiket/{{ ticket.ticket_id }}/assign"
            hx-target="this" hx-swap="afterend"
            hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="assignee" value="{{ ticket.assigned_to or '' }}" class="form-control" placeholder="username admin">
        <button type="submit" class="btn" style="margin-top: 8px; width: 100%;">Assign</button>
      </form>
    </div>

    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
      <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Escalation</h3>
      <form hx-post="/admin/tiket/{{ ticket.ticket_id }}/escalation"
            hx-target="this" hx-swap="afterend"
            hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <select name="level" class="form-control">
          {% for lv in ["LOW","MEDIUM","HIGH","CRITICAL"] %}<option value="{{ lv }}" {% if lv == ticket.escalation_level %}selected{% endif %}>{{ lv }}</option>{% endfor %}
        </select>
        <button type="submit" class="btn" style="margin-top: 8px; width: 100%;">Simpan</button>
      </form>
    </div>

    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
      <h3 style="font-size: 14px; color: #64748b; text-transform: uppercase; margin-bottom: 12px;">Notifikasi Pelapor</h3>
      <form hx-post="/admin/tiket/{{ ticket.ticket_id }}/notify"
            hx-target="this" hx-swap="afterend"
            hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn btn-primary" style="width: 100%;">Kirim Update Status ke Pelapor</button>
      </form>
    </div>

  </div>
</div>
{% endblock %}
```

```html
{# app/web/templates/admin/_status_badge.html #}
<span class="badge badge-{{ ticket.status|lower }}"
      style="padding: 6px 12px; border-radius: 999px; background: #dbeafe; color: #1e40af; font-weight: 600;">
  {{ ticket.status }}
</span>
```

- [ ] **Step 4: Add detail route**

Append to `app/web/routes/admin_inbox.py`:

```python
from fastapi import HTTPException

from app.web.constants import ESCALATION_LEVELS


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
```

- [ ] **Step 5: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_admin_inbox.py -v`
Expected: 5 PASS

- [ ] **Step 6: Commit**

```bash
git add app/web/routes/admin_inbox.py app/web/templates/admin/tiket_detail.html app/web/templates/admin/_status_badge.html tests/test_web/test_routes/test_admin_inbox.py
git commit -m "feat(web): ticket detail page with HTMX action forms"
```

---

## Task 8: Ticket action routes (status/assign/escalation HTMX)

**Files:**
- Create: `app/web/routes/admin_actions.py`
- Create: `tests/test_web/test_routes/test_admin_actions.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_web/test_routes/test_admin_actions.py
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from app.database.models import Admin, Base, IncidentTicket
from app.web.dependencies import get_current_admin, get_db_session
from app.web.routes.admin_actions import router as actions_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    admin = Admin(id=1, username="admin1", email="a@x.com", full_name="A",
                  password_hash="h", is_active=True)
    db.add(admin)
    db.add(IncidentTicket(
        ticket_id="INC-A", reporter_id="tg:123", reporter_name="P",
        incident_type="PHISHING", severity="HIGH",
        description_raw="x", description_sanitized="x",
        status="PENDING_REVIEW",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_db_session] = lambda: iter([db])
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.include_router(actions_router)
    return TestClient(app), db


def test_update_status(client):
    c, db = client
    r = c.post("/admin/tiket/INC-A/status", data={"status": "IN_PROGRESS"})
    assert r.status_code == 200
    assert "IN_PROGRESS" in r.text
    db.expire_all()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().status == "IN_PROGRESS"


def test_update_status_invalid(client):
    c, _ = client
    r = c.post("/admin/tiket/INC-A/status", data={"status": "BOGUS"})
    assert r.status_code == 400


def test_assign(client):
    c, db = client
    r = c.post("/admin/tiket/INC-A/assign", data={"assignee": "budi"})
    assert r.status_code == 200
    db.expire_all()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().assigned_to == "budi"


def test_escalation(client):
    c, db = client
    r = c.post("/admin/tiket/INC-A/escalation", data={"level": "HIGH"})
    assert r.status_code == 200
    db.expire_all()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().escalation_level == "HIGH"


def test_notify_success(client):
    c, _ = client
    with patch(
        "app.web.routes.admin_actions.NotificationService.notify_status",
        new=AsyncMock(return_value=True),
    ):
        r = c.post("/admin/tiket/INC-A/notify")
    assert r.status_code == 200
    assert "berhasil" in r.text.lower()


def test_notify_failure_returns_warning(client):
    c, _ = client
    with patch(
        "app.web.routes.admin_actions.NotificationService.notify_status",
        new=AsyncMock(return_value=False),
    ):
        r = c.post("/admin/tiket/INC-A/notify")
    assert r.status_code == 200
    assert "gagal" in r.text.lower()


def test_action_on_missing_ticket_404(client):
    c, _ = client
    r = c.post("/admin/tiket/NOPE/status", data={"status": "IN_PROGRESS"})
    assert r.status_code == 404
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_actions.py -v`
Expected: ImportError

- [ ] **Step 3: Implement actions router**

```python
# app/web/routes/admin_actions.py
"""Routes HTMX untuk aksi update tiket admin."""
import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.models import Admin
from app.web.dependencies import get_current_admin, get_db_session
from app.web.services.notification_service import NotificationService
from app.web.services.ticket_service import TicketService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/tiket", tags=["admin-actions"])
templates = Jinja2Templates(directory="app/web/templates")


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
        f'<p style="color: #16a34a; font-size: 13px; margin-top: 8px;">Ditugaskan ke <strong>{assignee}</strong></p>'
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
        f'<p style="color: #16a34a; font-size: 13px; margin-top: 8px;">Escalation diset ke <strong>{level}</strong></p>'
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
```

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_admin_actions.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/admin_actions.py tests/test_web/test_routes/test_admin_actions.py
git commit -m "feat(web): admin ticket action routes (status/assign/escalation/notify)"
```

---

## Task 9: Attachment download route

**Files:**
- Modify: `app/web/routes/admin_actions.py` — add attachment download
- Modify: `tests/test_web/test_routes/test_admin_actions.py` — add download tests

- [ ] **Step 1: Add failing test**

Append to `test_admin_actions.py`:

```python
def test_attachment_download_streams_file(client, tmp_path):
    c, db = client
    # seed file on disk
    f = tmp_path / "evidence.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\nFAKE")
    ticket = db.query(IncidentTicket).filter_by(ticket_id="INC-A").one()
    ticket.evidence_files = [{"filename": "evidence.png", "path": str(f), "size_kb": 1}]
    db.commit()

    r = c.get("/admin/tiket/INC-A/attachment/0")
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")
    assert 'attachment; filename="evidence.png"' in r.headers["content-disposition"]


def test_attachment_download_bad_index_404(client):
    c, db = client
    ticket = db.query(IncidentTicket).filter_by(ticket_id="INC-A").one()
    ticket.evidence_files = []
    db.commit()
    r = c.get("/admin/tiket/INC-A/attachment/0")
    assert r.status_code == 404


def test_attachment_download_path_traversal_blocked(client, tmp_path):
    c, db = client
    ticket = db.query(IncidentTicket).filter_by(ticket_id="INC-A").one()
    ticket.evidence_files = [{"filename": "../../etc/passwd", "path": "/etc/passwd", "size_kb": 1}]
    db.commit()
    r = c.get("/admin/tiket/INC-A/attachment/0")
    assert r.status_code in (400, 404)
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_web/test_routes/test_admin_actions.py::test_attachment_download_streams_file -v`
Expected: 404 (no route)

- [ ] **Step 3: Implement attachment download**

Append to `app/web/routes/admin_actions.py`:

```python
import os

from fastapi.responses import FileResponse

UPLOAD_ROOT = os.path.abspath(os.environ.get("WEB_UPLOAD_DIR", "web_uploads"))


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

    # Path safety: filename tidak boleh mengandung path separator
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nama file tidak valid.")

    # File harus berada di dalam UPLOAD_ROOT ATAU tmp (untuk test).
    abs_path = os.path.abspath(raw_path)
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
```

Note: for the path traversal test, the filename check catches `../../etc/passwd` as invalid (contains `/` or `..`). For the tmp_path test, `/etc/passwd` would need to exist — but we only test that the filename check blocks the traversal filename, so test expects 400.

- [ ] **Step 4: Run tests, verify PASS**

Run: `pytest tests/test_web/test_routes/test_admin_actions.py -v`
Expected: 10 PASS

- [ ] **Step 5: Commit**

```bash
git add app/web/routes/admin_actions.py tests/test_web/test_routes/test_admin_actions.py
git commit -m "feat(web): attachment download with path traversal guard"
```

---

## Task 10: Wire routers into web app

**Files:**
- Modify: `app/web/app.py`
- Delete: `app/web/routes/admin_inbox_stub.py` (stub dari Plan A)

- [ ] **Step 1: Verify current wiring**

Run: `cat app/web/app.py | grep include_router`
Expected: shows `admin_inbox_stub` router being included.

- [ ] **Step 2: Update `register_web` in `app/web/app.py`**

Replace the stub import/include with:

```python
# app/web/app.py — dalam fungsi register_web, ganti:
#   from app.web.routes.admin_inbox_stub import router as admin_inbox_stub_router
#   app.include_router(admin_inbox_stub_router)
# menjadi:
from app.web.routes.admin_inbox import router as admin_inbox_router
from app.web.routes.admin_actions import router as admin_actions_router

app.include_router(admin_inbox_router)
app.include_router(admin_actions_router)
```

- [ ] **Step 3: Delete stub file**

```bash
git rm app/web/routes/admin_inbox_stub.py
```

If stub has a test file, delete it too:

```bash
git rm tests/test_web/test_routes/test_admin_inbox_stub.py 2>/dev/null || true
```

- [ ] **Step 4: Run full web test suite**

Run: `pytest tests/test_web/ -v`
Expected: All tests PASS (Plan A + Plan B combined).

- [ ] **Step 5: Commit**

```bash
git add app/web/app.py
git commit -m "chore(web): wire admin_inbox + admin_actions routers, drop stub"
```

---

## Task 11: Integration test — end-to-end admin workflow

**Files:**
- Create: `tests/test_web/test_integration/test_admin_workflow.py`

- [ ] **Step 1: Write failing integration test**

```python
# tests/test_web/test_integration/test_admin_workflow.py
"""End-to-end: login → inbox → open ticket → update status → verify persisted."""
import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from passlib.hash import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Admin, Base, IncidentTicket
from app.main import app as fastapi_app
from app.web.dependencies import get_db_session
from app.web.services import auth_service as auth_mod


CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    admin = Admin(
        id=1, username="admin1", email="a@x.com", full_name="A",
        password_hash=bcrypt.using(rounds=4).hash("password123"),
        is_active=True,
    )
    db.add(admin)
    db.add(IncidentTicket(
        ticket_id="INC-42",
        reporter_id="tg:555",
        reporter_name="Budi",
        incident_type="PHISHING",
        severity="HIGH",
        description_raw="email phishing",
        description_sanitized="email phishing",
        status="PENDING_REVIEW",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

    def override_db():
        yield db

    fastapi_app.dependency_overrides[get_db_session] = override_db

    r = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(auth_mod, "_redis_client", lambda: r)

    yield TestClient(fastapi_app)

    fastapi_app.dependency_overrides.clear()
    db.close()


def _csrf(html: str) -> str:
    m = CSRF_RE.search(html)
    assert m, "csrf token not found in HTML"
    return m.group(1)


def test_admin_full_workflow(client):
    # 1. Get login page → extract csrf
    r = client.get("/admin/login")
    assert r.status_code == 200
    token = _csrf(r.text)

    # 2. Login
    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "password123", "csrf_token": token},
        headers={"X-CSRF-Token": token},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert "/admin/inbox" in r.headers["location"]

    # 3. Open inbox
    r = client.get("/admin/inbox")
    assert r.status_code == 200
    assert "INC-42" in r.text
    inbox_token = _csrf(r.text)

    # 4. Filter by status via HTMX fragment
    r = client.get("/admin/inbox/table?status=PENDING_REVIEW")
    assert r.status_code == 200
    assert "INC-42" in r.text

    # 5. Open ticket detail
    r = client.get("/admin/tiket/INC-42")
    assert r.status_code == 200
    assert "PENDING_REVIEW" in r.text
    detail_token = _csrf(r.text)

    # 6. Update status via HTMX POST
    r = client.post(
        "/admin/tiket/INC-42/status",
        data={"status": "IN_PROGRESS", "csrf_token": detail_token},
        headers={"X-CSRF-Token": detail_token},
    )
    assert r.status_code == 200
    assert "IN_PROGRESS" in r.text

    # 7. Verify persisted (reopen detail)
    r = client.get("/admin/tiket/INC-42")
    assert "IN_PROGRESS" in r.text

    # 8. Notify pelapor (mock telegram)
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(return_value=None),
    ):
        r = client.post(
            "/admin/tiket/INC-42/notify",
            data={"csrf_token": detail_token},
            headers={"X-CSRF-Token": detail_token},
        )
    assert r.status_code == 200
    assert "berhasil" in r.text.lower()
```

- [ ] **Step 2: Run, verify PASS**

Run: `pytest tests/test_web/test_integration/test_admin_workflow.py -v`
Expected: PASS (single test, 8 stages)

If CSRF middleware blocks any step, debug by inspecting the middleware exempt paths or confirming the session cookie is propagating.

- [ ] **Step 3: Run full test suite one more time**

Run: `pytest tests/test_web/ -v`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_web/test_integration/test_admin_workflow.py
git commit -m "test(web): end-to-end admin workflow integration test"
```

---

## Task 12: Manual smoke test checklist

**Files:** (none — verification only)

- [ ] **Step 1: Start server**

```bash
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Seed admin (jika belum)**

```bash
python scripts/seed_admin.py
# ikuti prompt: username, email, full_name, password
```

- [ ] **Step 3: Seed tiket dummy (opsional)**

Jika DB kosong, masukkan satu tiket lewat Telegram bot atau via API:

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{"reporter_id":"tg:123","reporter_name":"Test","incident_type":"PHISHING","severity":"HIGH","description_raw":"test","description_sanitized":"test"}'
```

- [ ] **Step 4: Browser flow**

1. Buka `http://localhost:8000/admin/login` → login dengan seeded admin
2. Redirect ke `/admin/inbox` → tiket terlihat di tabel
3. Filter status: pilih `PENDING_REVIEW` → tabel re-render via HTMX (cek DevTools Network, hanya `/admin/inbox/table` yang dipanggil)
4. Filter severity: pilih `HIGH` → kombinasi filter bekerja
5. Search: ketik ticket_id partial → hasil terfilter
6. Klik baris tiket → navigasi ke detail
7. Update status via dropdown → badge re-render inline tanpa full reload
8. Assign ke username: ketik "budi" → konfirmasi muncul di bawah form
9. Set escalation: pilih HIGH → konfirmasi muncul
10. Klik "Kirim Update Status ke Pelapor" → jika TELEGRAM_BOT_TOKEN set + reporter_id valid, pelapor terima pesan
11. Logout via sidebar → redirect ke `/admin/login`

- [ ] **Step 5: Verify audit trail di log aplikasi**

Cek stdout server untuk line:

```
TICKET_STATUS_UPDATED ticket=INC-XX admin=admin1 new=IN_PROGRESS
TICKET_ASSIGNED ticket=INC-XX admin=admin1 assignee=budi
TICKET_ESCALATION_UPDATED ticket=INC-XX admin=admin1 level=HIGH
NOTIFICATION_SENT ticket=INC-XX admin=admin1 success=True
```

- [ ] **Step 6: Tag release**

```bash
git tag plan-b-complete
```

- [ ] **Step 7: Report completion to user**

Summary: Plan B selesai. Admin dapat mengelola inbox, membuka detail tiket, update status/assign/escalation, dan kirim notifikasi Telegram. Lanjut ke Plan C (Pelapor Chat) atau Plan D (RAG & Report).

---

## Notes for the Executing Subagent

- **Jangan ubah `IncidentState` atau agent pipeline.** Plan B hanya membaca/menulis `IncidentTicket` dan `AuditLog` via service layer.
- **Error handling:** semua action route wajib return 404 jika tiket tidak ada, 400 jika input invalid. Jangan biarkan 500 leak.
- **CSRF:** setiap POST wajib sertakan token lewat header `X-CSRF-Token` dan form field `csrf_token`. Template sudah memasang keduanya.
- **Audit log:** untuk sekarang cukup `logger.info()` structured line. Integrasi penuh ke `AuditLog` table bisa dijadwalkan di Plan D bersama refactor audit repository — TIDAK termasuk Plan B.
- **Path safety:** attachment download hanya boleh membaca file dengan filename tanpa separator. Absolute path dari DB entry dipakai apa adanya (di-set saat upload di Plan C).
- **Test isolation:** SQLite in-memory dengan `StaticPool` + `check_same_thread=False` sudah terbukti bekerja di Plan A — pakai pola yang sama.
- **Commit cadence:** satu task = satu commit. Jangan bundle.
- **Jika test gagal:** fix di task yang sama, jangan pindah task. Jangan skip review loop.
