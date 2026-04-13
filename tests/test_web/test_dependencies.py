"""Test get_current_admin dependency."""
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database.models import Admin
from app.web import dependencies as deps_module
from app.web.dependencies import _RedirectException, get_current_admin


@pytest.fixture
def admin_row():
    return Admin(
        id=1, username="admin1", email="a@x.com", full_name="A",
        password_hash="h", is_active=True,
    )


def _make_app(monkeypatch, admin_row, is_active=True):
    if admin_row is not None:
        admin_row.is_active = is_active

    def fake_get_db_session():
        db = MagicMock()
        q = db.query.return_value.filter_by.return_value
        q.first.return_value = admin_row
        yield db

    monkeypatch.setattr(deps_module, "get_db_session", fake_get_db_session)

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")

    @app.exception_handler(_RedirectException)
    async def _redir_handler(request: Request, exc: _RedirectException):
        return RedirectResponse(url=exc.location, status_code=303)

    @app.get("/login")
    def login(request: Request):
        request.session["admin_id"] = 1
        return {"ok": True}

    @app.get("/protected")
    def protected(admin: Admin = Depends(get_current_admin)):
        return {"username": admin.username}

    return TestClient(app)


def test_protected_without_session_redirects(monkeypatch, admin_row):
    client = _make_app(monkeypatch, admin_row)
    r = client.get("/protected", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
    assert "/admin/login" in r.headers["location"]


def test_protected_with_valid_session(monkeypatch, admin_row):
    client = _make_app(monkeypatch, admin_row)
    client.get("/login")
    r = client.get("/protected")
    assert r.status_code == 200
    assert r.json() == {"username": "admin1"}


def test_protected_with_inactive_admin(monkeypatch, admin_row):
    client = _make_app(monkeypatch, admin_row, is_active=False)
    client.get("/login")
    r = client.get("/protected", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
