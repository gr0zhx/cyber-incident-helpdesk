"""Test landing page."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.web.routes.landing import router as landing_router


def _make_client():
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")
    app.include_router(landing_router)
    return TestClient(app)


def test_landing_returns_200():
    client = _make_client()
    r = client.get("/")
    assert r.status_code == 200


def test_landing_has_cta_buttons():
    client = _make_client()
    r = client.get("/")
    body = r.text
    assert "Lapor Insiden" in body
    assert "Admin Login" in body
