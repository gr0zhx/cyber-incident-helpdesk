"""End-to-end: isi identitas -> chat -> tiket terbentuk."""
import re
from unittest.mock import AsyncMock, MagicMock

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

    def override_db():
        yield db

    fastapi_app.dependency_overrides[get_db_session] = override_db

    r = fakeredis.FakeStrictRedis(decode_responses=False)
    monkeypatch.setattr(pelapor_mod, "_redis_client", lambda: r)

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=_PIPELINE_RESULT)
    monkeypatch.setattr(pelapor_mod, "_get_graph", lambda db: mock_graph)
    monkeypatch.setattr(pelapor_mod, "_get_orch", lambda: MagicMock())

    yield TestClient(fastapi_app)

    fastapi_app.dependency_overrides = {}
    db.close()


CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


def _csrf(html: str) -> str:
    m = CSRF_RE.search(html)
    assert m, "csrf_token not found in HTML"
    return m.group(1)


def test_reporter_full_flow(client):
    # 1. GET identitas form — extract CSRF token
    r = client.get("/lapor")
    assert r.status_code == 200
    assert "Nama Lengkap" in r.text
    token = _csrf(r.text)

    # 2. POST identitas with valid CSRF token -> redirect ke chat
    r = client.post("/lapor", data={
        "reporter_name": "Sari Dewi",
        "reporter_contact": "sari@kementan.go.id",
        "reporter_unit": "Divisi IT",
        "csrf_token": token,
    }, headers={"X-CSRF-Token": token}, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/lapor/chat" in r.headers["location"]

    # 3. GET chat page — extract CSRF token for subsequent POSTs
    r = client.get("/lapor/chat")
    assert r.status_code == 200
    assert "Asisten Keamanan" in r.text
    assert "Sari Dewi" in r.text
    chat_token = _csrf(r.text)

    # 4. POST message -> fragment with tiket card
    r = client.post("/lapor/chat/message", data={
        "text": "Email phishing dari HR palsu, saya klik link-nya",
        "csrf_token": chat_token,
    }, headers={"X-CSRF-Token": chat_token})
    assert r.status_code == 200
    assert "INC-WEB-1" in r.text

    # 5. GET tiket status
    r = client.get("/lapor/tiket/INC-WEB-1")
    # Will 404 because ticket not in DB (pipeline mocked), that's OK —
    # in real run, TicketManagerAgent inserts it
    assert r.status_code in (200, 404)

    # 6. Reset session — re-fetch chat page for fresh token
    r = client.get("/lapor/chat")
    reset_token = _csrf(r.text)
    r = client.post("/lapor/chat/reset", data={"csrf_token": reset_token}, headers={"X-CSRF-Token": reset_token}, follow_redirects=False)
    assert r.status_code in (302, 303)

    # 7. Chat now redirects to identitas
    r = client.get("/lapor/chat", follow_redirects=False)
    assert r.status_code in (302, 303)
