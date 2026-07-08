from datetime import datetime, timezone
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

    def override_db():
        yield db

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_current_admin] = lambda: admin
    app.dependency_overrides[get_db_session] = override_db
    app.include_router(router)
    return TestClient(app)


def test_report_page_renders(client):
    r = client.get("/admin/report", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin/inbox"


def test_report_generate_returns_pdf_download(client):
    r = client.post("/admin/report/generate",
                    data={"ticket_id": "INC-R1", "prepared_by": "Admin", "csrf_token": "x"})
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"
    assert r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers.get("content-disposition", "")
    assert ".pdf" in r.headers["content-disposition"]


def test_report_generate_missing_ticket_shows_error(client):
    r = client.post("/admin/report/generate",
                    data={"ticket_id": "NOPE", "prepared_by": "Admin", "csrf_token": "x"})
    assert r.status_code == 404
    assert "tidak ditemukan" in r.text.lower()
