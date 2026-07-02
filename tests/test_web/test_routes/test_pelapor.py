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
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    import app.web.routes.pelapor as pelapor_mod
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    monkeypatch.setattr(pelapor_mod, "_redis_client", lambda: r)
    monkeypatch.setattr(pelapor_mod, "_get_graph", lambda db: MagicMock())
    monkeypatch.setattr(pelapor_mod, "_get_orch", lambda: MagicMock())

    def override_db():
        yield db

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")
    app.dependency_overrides[get_db_session] = override_db

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


def test_post_identitas_requires_unit(client):
    r = client.post("/lapor", data={
        "reporter_name": "Budi",
        "reporter_contact": "budi@test.id",
        "reporter_unit": "",
        "csrf_token": "x",
    })
    assert r.status_code == 200
    assert "Unit / Divisi tidak boleh kosong." in r.text


def test_post_identitas_requires_contact(client):
    r = client.post("/lapor", data={
        "reporter_name": "Budi",
        "reporter_contact": "",
        "reporter_unit": "IT",
        "csrf_token": "x",
    })
    assert r.status_code == 200
    assert "Kontak tidak boleh kosong." in r.text


def test_get_chat_renders_with_session(client):
    client.post("/lapor", data={
        "reporter_name": "Sari",
        "reporter_contact": "sari@test.id",
        "reporter_unit": "IT",
        "csrf_token": "x",
    })
    r = client.get("/lapor/chat")
    assert r.status_code == 200
    assert "Asisten Keamanan" in r.text


def test_send_message_returns_bubbles(client, monkeypatch):
    # Setup session
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "a@test.id", "reporter_unit": "IT", "csrf_token": "x"})

    import app.web.routes.pelapor as pelapor_mod
    mock_result = {
        "requires_clarification": False, "ticket_id": "INC-1",
        "mitigation_recommendation": "Isolasi host.",
        "incident_type": "PHISHING", "severity": "HIGH",
        "escalation_level": "MEDIUM", "confidence_score": 0.9,
    }
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=mock_result)
    monkeypatch.setattr(pelapor_mod, "_get_graph", lambda db: mock_graph)
    monkeypatch.setattr(pelapor_mod, "_get_orch", lambda: MagicMock())

    r2 = client.post("/lapor/chat/message", data={"text": "laptop saya terinfeksi", "csrf_token": "x"})

    assert r2.status_code == 200
    assert "INC-1" in r2.text or "laptop saya terinfeksi" in r2.text


def test_reset_clears_session(client):
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "a@test.id", "reporter_unit": "IT", "csrf_token": "x"})
    r = client.post("/lapor/chat/reset", data={"csrf_token": "x"}, follow_redirects=False)
    assert r.status_code in (302, 303)


def test_tiket_status_not_found(client):
    client.post("/lapor", data={"reporter_name": "A", "reporter_contact": "a@test.id", "reporter_unit": "IT", "csrf_token": "x"})
    r = client.get("/lapor/tiket/NOPE")
    assert r.status_code == 404
