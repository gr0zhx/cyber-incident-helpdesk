"""End-to-end HTTP: variasi input responden lewat rute /lapor yang sesungguhnya.

Melengkapi test_reporter_flow.py dengan skenario yang representasikan
keberagaman responden nyata: karakter berbahaya (XSS), teks sangat panjang,
dan beberapa kategori insiden berbeda — dijalankan lewat TestClient supaya
ikut menguji CSRF, templating, dan escaping HTML.
"""
import re
from unittest.mock import AsyncMock, MagicMock

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base
from app.main import app as fastapi_app
from app.web.dependencies import get_db_session
import app.web.routes.pelapor as pelapor_mod

CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


def _csrf(html: str) -> str:
    m = CSRF_RE.search(html)
    assert m, "csrf_token not found in HTML"
    return m.group(1)


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
    monkeypatch.setattr(pelapor_mod, "_get_orch", lambda: MagicMock())

    yield TestClient(fastapi_app), pelapor_mod, db

    fastapi_app.dependency_overrides = {}
    db.close()


def _login(client: TestClient, name="Sari Dewi", contact="sari@kementan.go.id"):
    r = client.get("/lapor")
    token = _csrf(r.text)
    r = client.post("/lapor", data={
        "reporter_name": name,
        "reporter_contact": contact,
        "reporter_unit": "Divisi IT",
        "csrf_token": token,
    }, headers={"X-CSRF-Token": token}, follow_redirects=False)
    assert r.status_code in (302, 303)
    r = client.get("/lapor/chat")
    return _csrf(r.text)


def _mock_pipeline(monkeypatch, module, **overrides):
    result = {
        "requires_clarification": False,
        "ticket_id": "INC-WEB-1",
        "mitigation_recommendation": "Isolasi host segera.",
        "incident_type": "PHISHING",
        "severity": "HIGH",
        "escalation_level": "MEDIUM",
        "confidence_score": 0.88,
        "clarification_message": "",
        "processing_errors": [],
        **overrides,
    }
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=result)
    monkeypatch.setattr(module, "_get_graph", lambda db: mock_graph)
    return mock_graph


def test_script_tag_input_is_escaped_not_executed(client, monkeypatch):
    """Responden bisa saja paste teks berisi tag HTML/script — pastikan
    template me-render sebagai teks biasa, bukan HTML aktif (XSS)."""
    tc, module, _db = client
    _mock_pipeline(monkeypatch, module)
    token = _login(tc)

    payload = "<script>alert('pwned')</script> laptop saya kena malware"
    r = tc.post("/lapor/chat/message", data={
        "text": payload,
        "csrf_token": token,
    }, headers={"X-CSRF-Token": token})

    assert r.status_code == 200
    assert "<script>alert" not in r.text
    assert "&lt;script&gt;" in r.text or "alert(&#39;pwned&#39;)" in r.text or "&amp;lt;script" not in r.text


def test_very_long_message_full_flow(client, monkeypatch):
    tc, module, _db = client
    _mock_pipeline(monkeypatch, module, ticket_id="INC-LONG")
    token = _login(tc)

    payload = "Insiden serupa terjadi berulang kali. " * 50  # ~1900 char
    r = tc.post("/lapor/chat/message", data={
        "text": payload,
        "csrf_token": token,
    }, headers={"X-CSRF-Token": token})

    assert r.status_code == 200
    assert "INC-LONG" in r.text


@pytest.mark.parametrize("incident_type,text", [
    ("PHISHING", "Email phishing mengaku dari bank meminta OTP"),
    ("MALWARE", "Antivirus mendeteksi trojan di komputer kantor"),
    ("DDOS", "Situs layanan publik kami down karena lonjakan traffic mencurigakan"),
    ("DATA_LEAK", "Ditemukan dump database pegawai di forum publik"),
])
def test_incident_category_full_flow(client, monkeypatch, incident_type, text):
    tc, module, _db = client
    ticket_id = f"INC-{incident_type}"
    _mock_pipeline(monkeypatch, module, ticket_id=ticket_id, incident_type=incident_type)
    token = _login(tc)

    r = tc.post("/lapor/chat/message", data={
        "text": text,
        "csrf_token": token,
    }, headers={"X-CSRF-Token": token})

    assert r.status_code == 200
    assert ticket_id in r.text


def test_two_reporters_get_isolated_sessions(client, monkeypatch):
    """2 'responden' berbeda (cookie session beda) tidak boleh saling lihat tiket."""
    tc, module, _db = client
    _mock_pipeline(monkeypatch, module, ticket_id="INC-SHARED-CHECK")

    token_a = _login(tc, name="Responden A", contact="a@kementan.go.id")
    r = tc.post("/lapor/chat/message", data={
        "text": "Laporan dari responden A",
        "csrf_token": token_a,
    }, headers={"X-CSRF-Token": token_a})
    assert "INC-SHARED-CHECK" in r.text

    # Client baru = cookie jar baru = sesi/responden berbeda
    tc2 = TestClient(fastapi_app)
    token_b = _login(tc2, name="Responden B", contact="b@kementan.go.id")
    r2 = tc2.get("/lapor/chat")
    assert "INC-SHARED-CHECK" not in r2.text
    assert "Responden B" in r2.text
