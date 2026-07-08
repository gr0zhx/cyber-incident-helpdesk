import json
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
from app.database.models import IncidentTicket
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
    assert "alert=session_invalid" in r.headers["location"]


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


def test_get_identitas_form_track_mode(client):
    r = client.get("/lapor?mode=track")
    assert r.status_code == 200
    assert "Lacak Tiket Anda" in r.text


def test_track_ticket_success_redirects_to_ticket_home(client):
    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0010",
            reporter_id="web:abc",
            reporter_name="Sari",
            reporter_contact="sari@test.id",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    r = client.post("/lapor/track", data={
        "ticket_id": "TICKET-2026-0010",
        "reporter_contact": "sari@test.id",
        "csrf_token": "x",
    }, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers["location"] == "/lapor/tiket-saya"


def test_track_ticket_accepts_plus62_format(client):
    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0012",
            reporter_id="web:abc",
            reporter_name="Sari",
            reporter_contact="081234567890",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    r = client.post("/lapor/track", data={
        "ticket_id": "TICKET-2026-0012",
        "reporter_contact": "+6281234567890",
        "csrf_token": "x",
    }, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers["location"] == "/lapor/tiket-saya"


def test_track_ticket_rejects_mismatched_contact(client):
    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0011",
            reporter_id="web:abc",
            reporter_name="Sari",
            reporter_contact="sari@test.id",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    r = client.post("/lapor/track", data={
        "ticket_id": "TICKET-2026-0011",
        "reporter_contact": "oranglain@test.id",
        "csrf_token": "x",
    })
    assert r.status_code == 200
    assert "Kontak verifikasi tidak cocok" in r.text


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


def test_restore_reporter_access_rebuilds_session(client):
    access_token = "a" * 64

    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0001",
            reporter_id="web:abc",
            reporter_access_token=access_token,
            reporter_name="A",
            reporter_contact="a@test.id",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    r = client.get(f"/lapor/akses/{access_token}", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers["location"] == f"/lapor/akses/{access_token}/riwayat"


def test_reporter_ticket_history_page(client):
    access_token = "b" * 64

    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0002",
            reporter_id="web:abc",
            reporter_access_token=access_token,
            reporter_name="A",
            reporter_contact="a@test.id",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    r = client.get(f"/lapor/akses/{access_token}/riwayat")
    assert r.status_code == 200
    assert "Daftar Tiket Anda" in r.text
    assert "TICKET-2026-0002" in r.text


def test_track_session_ticket_home_uses_tracked_ticket_session(client):
    db = next(client.app.dependency_overrides[get_db_session]())
    db.add(
        IncidentTicket(
            ticket_id="TICKET-2026-0020",
            reporter_id="web:track-1",
            reporter_name="Sari",
            reporter_contact="sari@test.id",
            reporter_department="IT",
            incident_type="Phishing",
            severity="Tinggi",
            description_raw="x",
            description_sanitized="x",
        )
    )
    db.commit()

    client.post("/lapor/track", data={
        "ticket_id": "TICKET-2026-0020",
        "reporter_contact": "sari@test.id",
        "csrf_token": "x",
    })
    r = client.get("/lapor/tiket-saya")
    assert r.status_code == 200
    assert "TICKET-2026-0020" in r.text
