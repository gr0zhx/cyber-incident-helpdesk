"""FastAPI dependencies untuk web interface."""
from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db as _get_db
from app.database.models import Admin


class _RedirectException(Exception):
    def __init__(self, location: str) -> None:
        self.location = location


def get_db_session() -> Generator[Session, None, None]:
    """Wrapper get_db agar bisa di-override di test."""
    yield from _get_db()


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db_session),
) -> Admin:
    """Load admin dari session cookie.

    Raises _RedirectException (ditangkap exception handler) kalau tidak ada/invalid.
    """
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise _RedirectException(f"/admin/login?next={request.url.path}")

    admin = db.query(Admin).filter_by(id=admin_id).first()
    if admin is None or not admin.is_active:
        request.session.clear()
        raise _RedirectException("/admin/login")
    return admin


def get_csrf_token(request: Request) -> str:
    return request.session.get("csrf_token", "")
