"""Test admin auth routes (login, logout)."""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from passlib.hash import bcrypt
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.database.models import Admin
from app.web.dependencies import _RedirectException, get_db_session
from app.web.middleware.csrf import CSRFMiddleware
from app.web.middleware.rate_limit import limiter
from app.web.routes.admin_auth import router as auth_router


@pytest.fixture
def admin_row():
    return Admin(
        id=1, username="admin1", email="a@x.com", full_name="Admin",
        password_hash=bcrypt.using(rounds=4).hash("pass1234"),
        is_active=True,
    )


@pytest.fixture
def fake_redis():
    store = {}

    class R:
        def get(self, k):
            return store.get(k)

        def setex(self, k, t, v):
            store[k] = v

        def incr(self, k):
            store[k] = str(int(store.get(k, 0)) + 1)
            return int(store[k])

        def expire(self, k, t):
            pass

        def delete(self, k):
            store.pop(k, None)

    return R()


def _make_client(admin_row, fake_redis, monkeypatch):
    app = FastAPI()
    app.state.limiter = limiter
    app.add_middleware(CSRFMiddleware, secret="csrf-secret",
                       exempt_paths=("/admin/login",))
    app.add_middleware(SessionMiddleware, secret_key="session-secret")

    @app.exception_handler(_RedirectException)
    async def _h(request, exc):
        return RedirectResponse(url=exc.location, status_code=303)

    def override_db():
        db = MagicMock()
        q = db.query.return_value.filter_by.return_value
        q.first.return_value = admin_row
        db.commit = MagicMock()
        yield db

    app.dependency_overrides[get_db_session] = override_db

    import app.web.routes.admin_auth as mod
    monkeypatch.setattr(mod, "_redis_client", lambda: fake_redis)

    app.include_router(auth_router)
    return TestClient(app)


def test_login_get_renders_form(admin_row, fake_redis, monkeypatch):
    client = _make_client(admin_row, fake_redis, monkeypatch)
    r = client.get("/admin/login")
    assert r.status_code == 200
    assert "Username" in r.text
    assert "Password" in r.text


def test_login_post_correct_credentials(admin_row, fake_redis, monkeypatch):
    client = _make_client(admin_row, fake_redis, monkeypatch)
    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "pass1234"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/inbox"


def test_login_post_wrong_password(admin_row, fake_redis, monkeypatch):
    client = _make_client(admin_row, fake_redis, monkeypatch)
    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "wrong"},
    )
    assert r.status_code == 200
    assert "tidak valid" in r.text.lower() or "invalid" in r.text.lower()
