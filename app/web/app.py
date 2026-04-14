"""Helper untuk integrasi web routes ke FastAPI app utama."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.web.config import get_web_config
from app.web.dependencies import _RedirectException
from app.web.middleware.csrf import CSRFMiddleware
from app.web.middleware.rate_limit import limiter
from app.web.middleware.security_headers import SecurityHeadersMiddleware
from app.web.routes.admin_actions import router as admin_actions_router
from app.web.routes.admin_auth import router as admin_auth_router
from app.web.routes.admin_inbox import router as admin_inbox_router
from app.web.routes.landing import router as landing_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def register_web(app: FastAPI) -> None:
    """Register middleware, static mount, routes, dan exception handler."""
    config = get_web_config()

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CSRFMiddleware,
        secret=config.csrf_secret,
        exempt_paths=("/api/",),
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        max_age=config.session_max_age,
        same_site="lax",
        https_only=config.cookie_secure,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(_RedirectException)
    async def _redirect_handler(request: Request, exc: _RedirectException):
        return RedirectResponse(url=exc.location, status_code=303)

    app.mount(
        "/web/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="web_static",
    )

    app.include_router(landing_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_inbox_router)
    app.include_router(admin_actions_router)
