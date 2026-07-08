"""End-to-end: login → inbox → open ticket → update status → notify."""
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
import app.web.routes.admin_auth as admin_auth_mod
from app.web.dependencies import get_db_session


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
    monkeypatch.setattr(admin_auth_mod, "_redis_client", lambda: r)

    yield TestClient(fastapi_app)

    fastapi_app.dependency_overrides = {}
    db.close()


def _csrf(html: str) -> str:
    m = CSRF_RE.search(html)
    assert m, "csrf token not found in HTML"
    return m.group(1)


def test_admin_full_workflow(client):
    r = client.get("/admin/login")
    assert r.status_code == 200
    token = _csrf(r.text)

    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "password123", "csrf_token": token},
        headers={"X-CSRF-Token": token},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert "/admin/inbox" in r.headers["location"]

    r = client.get("/admin/inbox")
    assert r.status_code == 200
    assert "INC-42" in r.text

    r = client.get("/admin/inbox/table?status=PENDING_REVIEW")
    assert r.status_code == 200
    assert "INC-42" in r.text

    r = client.get("/admin/tiket/INC-42")
    assert r.status_code == 200
    assert "PENDING_REVIEW" in r.text
    detail_token = _csrf(r.text)

    r = client.post(
        "/admin/tiket/INC-42/status",
        data={"status": "IN_PROGRESS", "csrf_token": detail_token},
        headers={"X-CSRF-Token": detail_token},
    )
    assert r.status_code == 200
    assert "IN_PROGRESS" in r.text

    r = client.get("/admin/tiket/INC-42")
    assert "IN_PROGRESS" in r.text

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
