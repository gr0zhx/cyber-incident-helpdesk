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

    def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
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


def test_attachment_download_streams_file(client, tmp_path, monkeypatch):
    c, db = client
    # Titik file DI DALAM UPLOAD_ROOT agar lolos path traversal guard.
    from app.web.routes import admin_actions as aa
    monkeypatch.setattr(aa, "UPLOAD_ROOT", str(tmp_path.resolve()))
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


def test_attachment_download_path_traversal_blocked(client):
    c, db = client
    ticket = db.query(IncidentTicket).filter_by(ticket_id="INC-A").one()
    ticket.evidence_files = [{"filename": "../../etc/passwd", "path": "/etc/passwd", "size_kb": 1}]
    db.commit()
    r = c.get("/admin/tiket/INC-A/attachment/0")
    assert r.status_code in (400, 404)
