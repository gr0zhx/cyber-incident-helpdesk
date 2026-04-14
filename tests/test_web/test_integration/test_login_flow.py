"""Integration test: login flow end-to-end melalui TestClient."""
import pytest
from fastapi.testclient import TestClient
from passlib.hash import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Admin, Base
from app.main import app
from app.web.dependencies import get_db_session


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    admin = Admin(
        username="integ_admin",
        email="integ@test.com",
        full_name="Integration Admin",
        password_hash=bcrypt.using(rounds=4).hash("integpass123"),
        is_active=True,
    )
    session.add(admin)
    session.commit()

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = override
    yield session
    session.close()
    app.dependency_overrides = {}


@pytest.fixture
def fake_redis_patch(monkeypatch):
    import fakeredis
    r = fakeredis.FakeStrictRedis(decode_responses=True)
    import app.web.routes.admin_auth as mod
    monkeypatch.setattr(mod, "_redis_client", lambda: r)
    return r


def _extract_csrf(html: str) -> str:
    import re
    m = re.search(r'name="csrf[_-]token"\s+content="([^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "csrf token tidak ditemukan di HTML"
    return m.group(1)


def test_full_login_flow(test_db, fake_redis_patch):
    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 200

    r = client.get("/admin/inbox", follow_redirects=False)
    assert r.status_code == 303
    assert "/admin/login" in r.headers["location"]

    r = client.get("/admin/login")
    assert r.status_code == 200
    csrf = _extract_csrf(r.text)

    r = client.post(
        "/admin/login",
        data={"username": "integ_admin", "password": "integpass123",
              "csrf_token": csrf},
        headers={"X-CSRF-Token": csrf},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/inbox"

    r = client.get("/admin/inbox")
    assert r.status_code == 200
    assert "Inbox Tiket" in r.text
    assert "Pusdatin CSIRT" in r.text
