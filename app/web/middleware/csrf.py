"""CSRFMiddleware — double-submit cookie.

Strategi:
- GET/HEAD/OPTIONS: generate token kalau belum ada di session.
- POST/PATCH/PUT/DELETE: verify header X-CSRF-Token atau form field
  `csrf_token` cocok dengan token di session.
"""
from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
SESSION_KEY = "csrf_token"
HEADER_NAME = "X-CSRF-Token"
FORM_FIELD = "csrf_token"


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str, exempt_paths: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self._secret = secret
        self._exempt = exempt_paths

    async def dispatch(self, request: Request, call_next) -> Response:
        if any(request.url.path.startswith(p) for p in self._exempt):
            return await call_next(request)

        session = request.session if "session" in request.scope else None

        if request.method in SAFE_METHODS:
            if session is not None and SESSION_KEY not in session:
                session[SESSION_KEY] = secrets.token_urlsafe(32)
            return await call_next(request)

        if session is None or SESSION_KEY not in session:
            return JSONResponse({"detail": "CSRF token missing"}, status_code=403)

        expected = session[SESSION_KEY]
        token = request.headers.get(HEADER_NAME)

        if not token:
            try:
                form = await request.form()
                token = form.get(FORM_FIELD)
            except Exception:
                token = None

        if not token or not secrets.compare_digest(str(token), expected):
            return JSONResponse({"detail": "CSRF token invalid"}, status_code=403)

        return await call_next(request)
