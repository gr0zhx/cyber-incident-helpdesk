"""Test SecurityHeadersMiddleware."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.web.middleware.security_headers import SecurityHeadersMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(app)


def test_sets_x_frame_options():
    client = _make_app()
    r = client.get("/ping")
    assert r.headers.get("x-frame-options") == "DENY"


def test_sets_content_type_options():
    client = _make_app()
    r = client.get("/ping")
    assert r.headers.get("x-content-type-options") == "nosniff"


def test_sets_referrer_policy():
    client = _make_app()
    r = client.get("/ping")
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_sets_csp():
    client = _make_app()
    r = client.get("/ping")
    csp = r.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
