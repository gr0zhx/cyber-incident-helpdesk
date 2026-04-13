"""Stub route untuk /admin/inbox — implementasi lengkap di Plan B."""
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.models import Admin
from app.web.dependencies import get_current_admin

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin")


@router.get("/inbox", response_class=HTMLResponse)
def inbox_stub(
    request: Request,
    admin: Admin = Depends(get_current_admin),
) -> HTMLResponse:
    return templates.TemplateResponse(
        "admin/inbox_stub.html",
        {
            "request": request,
            "admin": admin,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )
