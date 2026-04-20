"""Admin authentication routes: login, logout."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
import redis
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.web.dependencies import get_db_session
from app.web.middleware.rate_limit import limiter
from app.web.services.auth_service import AuthService

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin", tags=["admin-auth"])


@router.get("", include_in_schema=False)
def admin_root():
    return RedirectResponse(url="/admin/inbox", status_code=302)


def _redis_client():
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(url, decode_responses=True)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> HTMLResponse:
    next_path = request.query_params.get("next", "/admin/inbox")
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "csrf_token": request.session.get("csrf_token", ""),
            "next": next_path,
            "error": None,
        },
    )


@router.post("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_session),
):
    redis_client = _redis_client()
    svc = AuthService(db=db, redis_client=redis_client)
    result = svc.authenticate(
        username=username,
        password=password,
        client_ip=request.client.host if request.client else "unknown",
    )

    if not result.success:
        error_map = {
            "invalid_credentials": "Username atau password tidak valid.",
            "account_disabled": "Akun dinonaktifkan.",
            "locked": "Terlalu banyak percobaan gagal. Coba lagi nanti.",
        }
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "csrf_token": request.session.get("csrf_token", ""),
                "next": "/admin/inbox",
                "error": error_map.get(result.error, "Login gagal."),
            },
            status_code=200,
        )

    request.session["admin_id"] = result.admin_id
    request.session["username"] = result.username
    request.session["csrf_token"] = secrets.token_urlsafe(32)

    next_path = request.query_params.get("next", "/admin/inbox")
    if not next_path.startswith("/admin/"):
        next_path = "/admin/inbox"
    return RedirectResponse(url=next_path, status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
