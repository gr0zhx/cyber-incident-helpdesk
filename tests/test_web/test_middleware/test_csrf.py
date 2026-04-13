"""Test CSRFMiddleware — double-submit cookie."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.web.middleware.csrf import CSRFMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, secret="test-secret")
    app.add_middleware(SessionMiddleware, secret_key="session-secret")

    @app.get("/form")
    def form(request: Request):
        return {"csrf": request.session.get("csrf_token", "")}

    @app.post("/submit")
    def submit():
        return {"ok": True}

    return TestClient(app)


def test_get_sets_csrf_token_in_session():
    client = _make_app()
    r = client.get("/form")
    assert r.status_code == 200
    assert r.json()["csrf"] != ""


def test_post_without_token_rejected():
    client = _make_app()
    client.get("/form")
    r = client.post("/submit")
    assert r.status_code == 403


def test_post_with_wrong_token_rejected():
    client = _make_app()
    client.get("/form")
    r = client.post("/submit", headers={"X-CSRF-Token": "wrong"})
    assert r.status_code == 403


def test_post_with_valid_token_passes():
    client = _make_app()
    r1 = client.get("/form")
    token = r1.json()["csrf"]
    r2 = client.post("/submit", headers={"X-CSRF-Token": token})
    assert r2.status_code == 200
