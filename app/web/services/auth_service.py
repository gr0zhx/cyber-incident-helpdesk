"""AuthService — verifikasi password bcrypt + lockout counter via Redis."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.database.models import Admin

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    success: bool
    admin_id: Optional[int] = None
    username: Optional[str] = None
    error: Optional[str] = None  # "invalid_credentials" | "account_disabled" | "locked"


_DUMMY_HASH = bcrypt.using(rounds=12).hash("dummy-password-for-timing-defense")


class AuthService:
    """Authenticate admin via username/password dengan lockout counter."""

    def __init__(
        self,
        db: Session,
        redis_client: Any,
        lockout_threshold: int = 5,
        lockout_window: int = 15 * 60,
    ) -> None:
        self._db = db
        self._redis = redis_client
        self._lockout_threshold = lockout_threshold
        self._lockout_window = lockout_window

    def authenticate(self, username: str, password: str, client_ip: str) -> AuthResult:
        """Verifikasi kredensial, return AuthResult dengan status detail."""
        lockout_key = f"admin:lockout:{username}"
        fail_count = int(self._redis.get(lockout_key) or 0)
        if fail_count >= self._lockout_threshold:
            logger.warning("Login locked untuk %s dari IP %s", username, client_ip)
            return AuthResult(success=False, error="locked")

        admin = self._db.query(Admin).filter_by(username=username).first()

        if admin is None or not admin.is_active:
            # Verify against a real bcrypt(rounds=12) hash agar timing konsisten
            # dengan path valid-user (mitigasi username enumeration).
            # Akun disabled sengaja dikembalikan sebagai invalid_credentials agar
            # attacker tidak bisa membedakan "user tidak ada", "password salah",
            # atau "akun dinonaktifkan".
            bcrypt.verify(password, _DUMMY_HASH)
            self._increment_failure(lockout_key)
            return AuthResult(success=False, error="invalid_credentials")

        if not bcrypt.verify(password, admin.password_hash):
            self._increment_failure(lockout_key)
            return AuthResult(success=False, error="invalid_credentials")

        self._redis.delete(lockout_key)
        admin.last_login_at = datetime.now(timezone.utc)
        self._db.commit()
        return AuthResult(
            success=True,
            admin_id=admin.id,
            username=admin.username,
        )

    def _increment_failure(self, lockout_key: str) -> None:
        count = self._redis.incr(lockout_key)
        if count == 1:
            self._redis.expire(lockout_key, self._lockout_window)
