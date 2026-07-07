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
    assert "Pusdatin CSIRT" not in r.text
    assert "INC-0" in r.text


def test_inbox_filter_by_status(client):
    r = client.get("/admin/inbox/table?status=RESOLVED")
    assert r.status_code == 200
    assert "Tidak ada tiket" in r.text


def test_inbox_filter_by_date_range_excludes_out_of_range(client):
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    r = client.get(f"/admin/inbox/table?date_from={tomorrow}")
    assert r.status_code == 200
    assert "Tidak ada tiket" in r.text


def test_inbox_stats_reflect_date_filter(client):
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    r = client.get(f"/admin/inbox/stats?date_from={tomorrow}")
    assert r.status_code == 200
    assert "Total Tiket" in r.text


def test_ticket_detail_renders(client):
    r = client.get("/admin/tiket/INC-0")
    assert r.status_code == 200
    assert "INC-0" in r.text
    assert "Update Status" in r.text


def test_ticket_detail_404(client):
    r = client.get("/admin/tiket/NOPE")
    assert r.status_code == 404
