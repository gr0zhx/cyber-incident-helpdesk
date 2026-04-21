"""Konfigurasi khusus web interface."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

_DEV_SESSION_SECRET = "change-me-in-prod-64-chars-minimum-aaaaaaaaaaaaaaaaaaaaaaaaaa"
_DEV_CSRF_SECRET = "change-me-in-prod-csrf-64-chars-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


class WebConfig(BaseSettings):
    """Config untuk web interface, load dari env vars."""

    session_secret: str = _DEV_SESSION_SECRET
    csrf_secret: str = _DEV_CSRF_SECRET
    session_max_age: int = 60 * 60 * 8  # 8 jam
    cookie_secure: bool = False  # True di production (HTTPS only)
    upload_dir: Path = Path("./web_uploads")
    upload_max_bytes: int = 10 * 1024 * 1024  # 10 MB
    login_rate_limit: str = "5/minute"
    login_lockout_threshold: int = 5
    login_lockout_window_seconds: int = 15 * 60
    csrf_strict: bool = True  # set ke False di dev untuk bypass

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "WEB_"
        extra = "ignore"


@lru_cache
def get_web_config() -> WebConfig:
    config = WebConfig()
    # Fail-closed: jangan izinkan default secret bocor ke production.
    if config.cookie_secure and (
        config.session_secret == _DEV_SESSION_SECRET
        or config.csrf_secret == _DEV_CSRF_SECRET
    ):
        raise RuntimeError(
            "Default session/csrf secret terdeteksi sementara cookie_secure=True. "
            "Set WEB_SESSION_SECRET dan WEB_CSRF_SECRET via env var."
        )
    return config
