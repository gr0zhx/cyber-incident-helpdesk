# Plan A — Web Interface Foundation & Auth

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bangun fondasi `app/web/` (FastAPI + Jinja + HTMX) dengan middleware keamanan lengkap dan admin auth yang siap pakai, sehingga admin bisa login/logout dan mengakses halaman terproteksi.

**Architecture:** Tambah route group baru di FastAPI existing (single app, in-process). SessionMiddleware dari Starlette untuk cookie signed, slowapi untuk rate limit, passlib[bcrypt] untuk password hashing, python-magic untuk MIME validation (future-ready untuk Plan C). Database table `admins` baru via Alembic migration.

**Tech Stack:** FastAPI · Starlette SessionMiddleware · Jinja2 · HTMX (vendored) · passlib[bcrypt] · slowapi · itsdangerous · Alembic · SQLAlchemy · pytest · fakeredis

**Spec reference:** `docs/superpowers/specs/2026-04-13-web-interface-design.md` Sections 2, 3 (admins table + Redis lockout), 5.1-5.2 (auth routes), 7 (error handling)

---

## File Structure

### Create

```
app/web/
├── __init__.py
├── app.py                       # create_web_router() + setup middleware/static
├── config.py                    # WebConfig (Pydantic BaseSettings)
├── dependencies.py              # get_current_admin, get_csrf_token, get_db passthrough
├── middleware/
│   ├── __init__.py
│   ├── session.py               # SessionMiddleware setup helper
│   ├── csrf.py                  # CSRFMiddleware
│   ├── security_headers.py      # SecurityHeadersMiddleware
│   └── rate_limit.py            # slowapi Limiter instance
├── services/
│   ├── __init__.py
│   └── auth_service.py          # AuthService: verify_password, login, lockout
├── routes/
│   ├── __init__.py
│   ├── landing.py               # GET /
│   └── admin_auth.py            # /admin/login, /admin/logout
├── templates/
│   ├── base.html
│   ├── _macros.html
│   ├── landing.html
│   ├── admin/
│   │   ├── login.html
│   │   └── inbox_stub.html      # placeholder, real implementation di Plan B
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
└── static/
    ├── css/style.css
    └── js/htmx.min.js           # vendored

app/database/migrations/versions/
└── 20260413_01_add_admins_table.py   # Alembic migration

scripts/
└── seed_admin.py                # CLI tool untuk buat admin pertama

tests/test_web/
├── __init__.py
├── conftest.py                  # fixtures: client, db_session, fake_redis, admin_user
├── test_services/
│   ├── __init__.py
│   └── test_auth_service.py
├── test_middleware/
│   ├── __init__.py
│   ├── test_csrf.py
│   └── test_security_headers.py
└── test_routes/
    ├── __init__.py
    ├── test_landing.py
    └── test_admin_auth.py
```

### Modify

- `app/database/models.py` — tambah class `Admin`
- `app/main.py` — mount web router + static + middleware
- `requirements.txt` — tambah deps baru
- `.gitignore` — tambah `.superpowers/`, `web_uploads/`

---

## Task 1: Tambah dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Tambah dependencies baru**

Edit `requirements.txt`, tambah di bagian akhir:

```
# Web interface (Plan A)
passlib[bcrypt]==1.7.4
itsdangerous==2.2.0
slowapi==0.1.9
python-multipart==0.0.20
python-magic; platform_system != "Windows"
python-magic-bin; platform_system == "Windows"
fakeredis==2.26.1
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```

Expected: semua package terinstall tanpa error. Verifikasi:
```bash
python -c "import passlib, slowapi, itsdangerous, magic; print('ok')"
```
Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: tambah passlib, slowapi, itsdangerous untuk web interface"
```

---

## Task 2: Struktur direktori `app/web/` + config

**Files:**
- Create: `app/web/__init__.py`
- Create: `app/web/config.py`
- Create: `app/web/middleware/__init__.py`
- Create: `app/web/services/__init__.py`
- Create: `app/web/routes/__init__.py`
- Create: `tests/test_web/__init__.py`
- Create: `tests/test_web/test_services/__init__.py`
- Create: `tests/test_web/test_middleware/__init__.py`
- Create: `tests/test_web/test_routes/__init__.py`

- [ ] **Step 1: Buat semua `__init__.py` kosong**

```bash
touch app/web/__init__.py
touch app/web/middleware/__init__.py
touch app/web/services/__init__.py
touch app/web/routes/__init__.py
touch tests/test_web/__init__.py
touch tests/test_web/test_services/__init__.py
touch tests/test_web/test_middleware/__init__.py
touch tests/test_web/test_routes/__init__.py
```

- [ ] **Step 2: Buat `app/web/config.py`**

```python
"""Konfigurasi khusus web interface."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class WebConfig(BaseSettings):
    """Config untuk web interface, load dari env vars."""

    session_secret: str = "change-me-in-prod-64-chars-minimum-aaaaaaaaaaaaaaaaaaaaaaaaaa"
    csrf_secret: str = "change-me-in-prod-csrf-64-chars-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
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


@lru_cache
def get_web_config() -> WebConfig:
    return WebConfig()
```

- [ ] **Step 3: Test bahwa config bisa di-load**

Run:
```bash
python -c "from app.web.config import get_web_config; c = get_web_config(); print(c.session_max_age)"
```
Expected output: `28800`

- [ ] **Step 4: Commit**

```bash
git add app/web/ tests/test_web/
git commit -m "feat(web): struktur direktori dan WebConfig"
```

---

## Task 3: Model `Admin` + migration Alembic

**Files:**
- Modify: `app/database/models.py`
- Create: `app/database/migrations/versions/20260413_01_add_admins_table.py`
- Create: `tests/test_web/test_database/__init__.py`
- Create: `tests/test_web/test_database/test_admin_model.py`

- [ ] **Step 1: Tambah class `Admin` ke `app/database/models.py`**

Tambah di akhir file `app/database/models.py` (setelah class `AuditLog`):

```python
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(128), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)
```

- [ ] **Step 2: Buat file test model**

Create `tests/test_web/test_database/__init__.py` (empty).

Create `tests/test_web/test_database/test_admin_model.py`:

```python
"""Test model Admin."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Admin, Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_admin_create(db_session):
    admin = Admin(
        username="testadmin",
        email="test@example.com",
        full_name="Test Admin",
        password_hash="$2b$12$dummyhashfortest",
    )
    db_session.add(admin)
    db_session.commit()

    loaded = db_session.query(Admin).filter_by(username="testadmin").first()
    assert loaded is not None
    assert loaded.email == "test@example.com"
    assert loaded.is_active is True
    assert loaded.last_login_at is None


def test_admin_username_unique(db_session):
    a1 = Admin(username="dup", email="a@x.com", full_name="A", password_hash="h")
    a2 = Admin(username="dup", email="b@x.com", full_name="B", password_hash="h")
    db_session.add_all([a1, a2])
    with pytest.raises(Exception):
        db_session.commit()
```

- [ ] **Step 3: Run test untuk verifikasi fail (migration belum ada, tapi model in-memory harus jalan)**

Run:
```bash
pytest tests/test_web/test_database/test_admin_model.py -v
```
Expected: PASS (model SQLAlchemy sudah lengkap, test pakai SQLite in-memory).

- [ ] **Step 4: Buat Alembic migration**

Create `app/database/migrations/versions/20260413_01_add_admins_table.py`:

```python
"""add admins table

Revision ID: 20260413_01
Revises: f326b3b5253b
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa


revision = "20260413_01"
down_revision = "f326b3b5253b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_admins_username", "admins", ["username"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_admins_username", table_name="admins")
    op.drop_table("admins")
```

- [ ] **Step 5: Apply migration ke DB dev**

Run:
```bash
alembic -c app/database/migrations/alembic.ini upgrade head
```
Expected: `INFO [alembic.runtime.migration] Running upgrade f326b3b5253b -> 20260413_01`

Verifikasi tabel ada:
```bash
python -c "from sqlalchemy import create_engine, inspect; from app.config import get_settings; e = create_engine(get_settings().database_url); print('admins' in inspect(e).get_table_names())"
```
Expected: `True`

- [ ] **Step 6: Commit**

```bash
git add app/database/models.py app/database/migrations/versions/20260413_01_add_admins_table.py tests/test_web/test_database/
git commit -m "feat(db): tambah model Admin + migration"
```

---

## Task 4: Seed admin CLI script

**Files:**
- Create: `scripts/seed_admin.py`

- [ ] **Step 1: Buat `scripts/seed_admin.py`**

```python
"""CLI untuk buat admin user pertama.

Usage:
    python scripts/seed_admin.py
"""
from __future__ import annotations

import getpass
import sys
from datetime import datetime, timezone

from passlib.hash import bcrypt

from app.database.connection import _get_session_factory
from app.database.models import Admin


def main() -> int:
    print("=== Seed Admin User ===")
    username = input("Username: ").strip()
    if not username:
        print("Username wajib diisi.", file=sys.stderr)
        return 1

    email = input("Email: ").strip()
    full_name = input("Nama Lengkap: ").strip()
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Ulangi Password: ")

    if password != password2:
        print("Password tidak cocok.", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Password minimal 8 karakter.", file=sys.stderr)
        return 1

    session_factory = _get_session_factory()
    db = session_factory()
    try:
        existing = db.query(Admin).filter_by(username=username).first()
        if existing:
            print(f"Admin '{username}' sudah ada.", file=sys.stderr)
            return 1

        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=bcrypt.using(rounds=12).hash(password),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        print(f"OK — admin '{username}' berhasil dibuat.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test jalankan manual (opsional, bisa skip kalau tidak ada DB dev)**

```bash
python scripts/seed_admin.py
```

Input test values. Expected: `OK — admin 'xxx' berhasil dibuat.`

- [ ] **Step 3: Commit**

```bash
git add scripts/seed_admin.py
git commit -m "feat(web): CLI seed admin user"
```

---

## Task 5: AuthService — verify_password + bcrypt

**Files:**
- Create: `app/web/services/auth_service.py`
- Create: `tests/test_web/test_services/test_auth_service.py`

- [ ] **Step 1: Buat test untuk AuthService.verify_password**

Create `tests/test_web/test_services/test_auth_service.py`:

```python
"""Test AuthService."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from passlib.hash import bcrypt

from app.database.models import Admin
from app.web.services.auth_service import AuthService, AuthResult


@pytest.fixture
def admin_row():
    return Admin(
        id=1,
        username="admin1",
        email="admin1@test.com",
        full_name="Admin Satu",
        password_hash=bcrypt.using(rounds=4).hash("correctpass"),
        is_active=True,
    )


@pytest.fixture
def mock_db(admin_row):
    db = MagicMock()
    query = db.query.return_value
    filter_by = query.filter_by.return_value
    filter_by.first.return_value = admin_row
    return db


@pytest.fixture
def mock_redis():
    store = {}

    class FakeR:
        def get(self, key):
            return store.get(key)

        def setex(self, key, ttl, value):
            store[key] = value

        def incr(self, key):
            store[key] = str(int(store.get(key, 0)) + 1)
            return int(store[key])

        def expire(self, key, ttl):
            pass

        def delete(self, key):
            store.pop(key, None)

    return FakeR()


def test_verify_password_correct(mock_db, mock_redis):
    svc = AuthService(db=mock_db, redis_client=mock_redis)
    result = svc.authenticate("admin1", "correctpass", client_ip="127.0.0.1")
    assert result.success is True
    assert result.admin_id == 1
    assert result.error is None


def test_verify_password_wrong(mock_db, mock_redis):
    svc = AuthService(db=mock_db, redis_client=mock_redis)
    result = svc.authenticate("admin1", "wrongpass", client_ip="127.0.0.1")
    assert result.success is False
    assert result.error == "invalid_credentials"


def test_verify_user_not_found(mock_db, mock_redis):
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    svc = AuthService(db=mock_db, redis_client=mock_redis)
    result = svc.authenticate("nonexistent", "any", client_ip="127.0.0.1")
    assert result.success is False
    assert result.error == "invalid_credentials"


def test_verify_inactive_user(mock_db, mock_redis, admin_row):
    admin_row.is_active = False
    svc = AuthService(db=mock_db, redis_client=mock_redis)
    result = svc.authenticate("admin1", "correctpass", client_ip="127.0.0.1")
    assert result.success is False
    assert result.error == "account_disabled"


def test_lockout_after_5_failures(mock_db, mock_redis):
    svc = AuthService(db=mock_db, redis_client=mock_redis, lockout_threshold=5)
    for _ in range(5):
        svc.authenticate("admin1", "wrongpass", client_ip="127.0.0.1")
    result = svc.authenticate("admin1", "correctpass", client_ip="127.0.0.1")
    assert result.success is False
    assert result.error == "locked"
```

- [ ] **Step 2: Run test — expect FAIL (service belum ada)**

Run:
```bash
pytest tests/test_web/test_services/test_auth_service.py -v
```
Expected: FAIL dengan `ImportError: cannot import name 'AuthService' from 'app.web.services.auth_service'`

- [ ] **Step 3: Implement AuthService**

Create `app/web/services/auth_service.py`:

```python
"""AuthService — verifikasi password bcrypt + lockout counter via Redis."""
from __future__ import annotations

import logging
import time
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

        # Timing-safe: selalu jalankan bcrypt walau user tidak ditemukan
        if admin is None:
            bcrypt.using(rounds=4).hash("dummy")  # waste CPU agar waktu konsisten
            time.sleep(0.1)
            self._increment_failure(lockout_key)
            return AuthResult(success=False, error="invalid_credentials")

        if not bcrypt.verify(password, admin.password_hash):
            time.sleep(0.1)
            self._increment_failure(lockout_key)
            return AuthResult(success=False, error="invalid_credentials")

        if not admin.is_active:
            return AuthResult(success=False, error="account_disabled")

        # Sukses — reset counter + update last_login_at
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
```

- [ ] **Step 4: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_services/test_auth_service.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/web/services/auth_service.py tests/test_web/test_services/test_auth_service.py
git commit -m "feat(web): AuthService dengan bcrypt dan lockout counter"
```

---

## Task 6: Security Headers Middleware

**Files:**
- Create: `app/web/middleware/security_headers.py`
- Create: `tests/test_web/test_middleware/test_security_headers.py`

- [ ] **Step 1: Tulis test**

Create `tests/test_web/test_middleware/test_security_headers.py`:

```python
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
```

- [ ] **Step 2: Run test — expect FAIL**

Run:
```bash
pytest tests/test_web/test_middleware/test_security_headers.py -v
```
Expected: FAIL `ImportError`

- [ ] **Step 3: Implement middleware**

Create `app/web/middleware/security_headers.py`:

```python
"""SecurityHeadersMiddleware — set header keamanan di setiap response."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP_POLICY
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
```

- [ ] **Step 4: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_middleware/test_security_headers.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/web/middleware/security_headers.py tests/test_web/test_middleware/test_security_headers.py
git commit -m "feat(web): SecurityHeadersMiddleware"
```

---

## Task 7: CSRF Middleware

**Files:**
- Create: `app/web/middleware/csrf.py`
- Create: `tests/test_web/test_middleware/test_csrf.py`

- [ ] **Step 1: Tulis test**

Create `tests/test_web/test_middleware/test_csrf.py`:

```python
"""Test CSRFMiddleware — double-submit cookie."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.web.middleware.csrf import CSRFMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, secret="test-secret")
    app.add_middleware(SessionMiddleware, secret_key="session-secret")

    @app.get("/form")
    def form(request):
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
    client.get("/form")  # seed session
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
```

- [ ] **Step 2: Run test — expect FAIL**

Run:
```bash
pytest tests/test_web/test_middleware/test_csrf.py -v
```
Expected: FAIL `ImportError`

- [ ] **Step 3: Implement CSRFMiddleware**

Create `app/web/middleware/csrf.py`:

```python
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

        # Unsafe method — verify
        if session is None or SESSION_KEY not in session:
            return JSONResponse({"detail": "CSRF token missing"}, status_code=403)

        expected = session[SESSION_KEY]
        token = request.headers.get(HEADER_NAME)

        if not token:
            # Coba dari form data
            try:
                form = await request.form()
                token = form.get(FORM_FIELD)
            except Exception:
                token = None

        if not token or not secrets.compare_digest(str(token), expected):
            return JSONResponse({"detail": "CSRF token invalid"}, status_code=403)

        return await call_next(request)
```

- [ ] **Step 4: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_middleware/test_csrf.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/web/middleware/csrf.py tests/test_web/test_middleware/test_csrf.py
git commit -m "feat(web): CSRFMiddleware double-submit cookie"
```

---

## Task 8: Rate Limit Helper (slowapi)

**Files:**
- Create: `app/web/middleware/rate_limit.py`

- [ ] **Step 1: Buat Limiter instance**

Create `app/web/middleware/rate_limit.py`:

```python
"""Rate limit helper — wrapping slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- [ ] **Step 2: Verifikasi import jalan**

Run:
```bash
python -c "from app.web.middleware.rate_limit import limiter; print(limiter)"
```
Expected: prints a `Limiter` instance

- [ ] **Step 3: Commit**

```bash
git add app/web/middleware/rate_limit.py
git commit -m "feat(web): slowapi Limiter helper"
```

---

## Task 9: Dependencies — get_current_admin

**Files:**
- Create: `app/web/dependencies.py`
- Create: `tests/test_web/test_dependencies.py`

- [ ] **Step 1: Tulis test**

Create `tests/test_web/test_dependencies.py`:

```python
"""Test get_current_admin dependency."""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.database.models import Admin
from app.web.dependencies import get_current_admin


@pytest.fixture
def admin_row():
    return Admin(
        id=1, username="admin1", email="a@x.com", full_name="A",
        password_hash="h", is_active=True,
    )


def _make_app(admin_row, is_active=True):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="k")

    def override_db():
        db = MagicMock()
        q = db.query.return_value.filter_by.return_value
        if admin_row is None:
            q.first.return_value = None
        else:
            admin_row.is_active = is_active
            q.first.return_value = admin_row
        return db

    app.dependency_overrides = {}

    @app.get("/login")
    def login(request):
        request.session["admin_id"] = 1
        return {"ok": True}

    @app.get("/protected")
    def protected(admin: Admin = Depends(get_current_admin)):
        return {"username": admin.username}

    from app.web.dependencies import get_db_session
    app.dependency_overrides[get_db_session] = override_db
    return TestClient(app)


def test_protected_without_session_redirects(admin_row):
    client = _make_app(admin_row)
    r = client.get("/protected", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
    assert "/admin/login" in r.headers["location"]


def test_protected_with_valid_session(admin_row):
    client = _make_app(admin_row)
    client.get("/login")
    r = client.get("/protected")
    assert r.status_code == 200
    assert r.json() == {"username": "admin1"}


def test_protected_with_inactive_admin(admin_row):
    client = _make_app(admin_row, is_active=False)
    client.get("/login")
    r = client.get("/protected", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
```

- [ ] **Step 2: Run test — expect FAIL**

Run:
```bash
pytest tests/test_web/test_dependencies.py -v
```
Expected: FAIL `ImportError`

- [ ] **Step 3: Implement dependencies**

Create `app/web/dependencies.py`:

```python
"""FastAPI dependencies untuk web interface."""
from __future__ import annotations

from typing import Generator

from fastapi import Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database.connection import get_db as _get_db
from app.database.models import Admin


class _RedirectException(Exception):
    def __init__(self, location: str) -> None:
        self.location = location


def get_db_session() -> Generator[Session, None, None]:
    """Wrapper get_db agar bisa di-override di test."""
    yield from _get_db()


def get_current_admin(request: Request) -> Admin:
    """Load admin dari session cookie.

    Raises RedirectResponse (via exception handler) kalau tidak ada/invalid.
    """
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise _RedirectException(f"/admin/login?next={request.url.path}")

    # Ambil DB session secara manual (bukan via Depends, agar bisa dipanggil
    # dari dependency lain yang sudah punya db)
    db_gen = get_db_session()
    db = next(db_gen)
    try:
        admin = db.query(Admin).filter_by(id=admin_id).first()
        if admin is None or not admin.is_active:
            request.session.clear()
            raise _RedirectException("/admin/login")
        return admin
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def get_csrf_token(request: Request) -> str:
    return request.session.get("csrf_token", "")
```

- [ ] **Step 4: Daftarkan exception handler untuk `_RedirectException`**

Ini akan ditambahkan nanti di Task 13 saat wire-up `app/main.py`. Untuk test, buat exception handler lokal. Update test file:

Edit `tests/test_web/test_dependencies.py`, tambah setelah `app.add_middleware(...)`:

```python
    from starlette.requests import Request
    from app.web.dependencies import _RedirectException

    @app.exception_handler(_RedirectException)
    async def _redir_handler(request: Request, exc: _RedirectException):
        return RedirectResponse(url=exc.location, status_code=303)
```

- [ ] **Step 5: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_dependencies.py -v
```
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add app/web/dependencies.py tests/test_web/test_dependencies.py
git commit -m "feat(web): get_current_admin dependency + redirect exception"
```

---

## Task 10: Base template + CSS + HTMX vendored

**Files:**
- Create: `app/web/templates/base.html`
- Create: `app/web/templates/_macros.html`
- Create: `app/web/static/css/style.css`
- Create: `app/web/static/js/htmx.min.js`

- [ ] **Step 1: Download HTMX dan simpan sebagai static file**

```bash
curl -L https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o app/web/static/js/htmx.min.js
```

Verifikasi:
```bash
wc -l app/web/static/js/htmx.min.js
```
Expected: jumlah line > 0 (biasanya ~1 line karena minified).

- [ ] **Step 2: Buat `base.html`**

Create `app/web/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="csrf-token" content="{{ csrf_token | default('') }}">
  <title>{% block title %}Pusdatin Helpdesk{% endblock %}</title>
  <link rel="stylesheet" href="/web/static/css/style.css">
  <script src="/web/static/js/htmx.min.js" defer></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      document.body.addEventListener("htmx:configRequest", function(evt) {
        var token = document.querySelector('meta[name="csrf-token"]').content;
        if (token) evt.detail.headers["X-CSRF-Token"] = token;
      });
    });
  </script>
</head>
<body>
  <div class="app-shell">
    {% block layout %}{% endblock %}
  </div>
</body>
</html>
```

- [ ] **Step 3: Buat `_macros.html`**

Create `app/web/templates/_macros.html`:

```html
{% macro csrf_input(token) %}
  <input type="hidden" name="csrf_token" value="{{ token }}">
{% endmacro %}

{% macro badge(text, variant='default') %}
  <span class="badge badge-{{ variant }}">{{ text }}</span>
{% endmacro %}

{% macro flash(messages) %}
  {% if messages %}
    <div class="flash-container">
      {% for msg in messages %}
        <div class="flash flash-{{ msg.level }}">{{ msg.text }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endmacro %}
```

- [ ] **Step 4: Buat `style.css` minimal (tema modern minimalist biru)**

Create `app/web/static/css/style.css`:

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, "Segoe UI", Inter, sans-serif;
  background: #f8fafc;
  color: #0f172a;
  font-size: 14px;
  line-height: 1.5;
}

.app-shell {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: #0f172a;
  color: #fff;
  padding: 20px;
}

.sidebar .logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  margin-bottom: 28px;
}

.sidebar .logo-dot {
  width: 28px; height: 28px;
  background: #2563eb;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}

.sidebar .nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 13px;
  text-decoration: none;
  margin-bottom: 3px;
}

.sidebar .nav-item.active { background: #1e293b; color: #fff; }

.main {
  padding: 24px;
  background: #f8fafc;
}

.topbar {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  padding: 14px 24px;
  display: flex; justify-content: space-between; align-items: center;
}

.btn {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  text-decoration: none;
}

.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-outline { background: transparent; color: #2563eb; border: 1px solid #2563eb; }

.form-input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
}

.form-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.form-group { margin-bottom: 14px; }

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
}

.flash { padding: 10px 14px; border-radius: 6px; margin-bottom: 10px; font-size: 13px; }
.flash-error { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.flash-success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }

.badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  font-weight: 600;
}

.badge-default { background: #f1f5f9; color: #475569; }
```

- [ ] **Step 5: Commit**

```bash
git add app/web/templates/base.html app/web/templates/_macros.html app/web/static/
git commit -m "feat(web): base template + CSS tema minimalist biru + HTMX vendored"
```

---

## Task 11: Landing page

**Files:**
- Create: `app/web/routes/landing.py`
- Create: `app/web/templates/landing.html`
- Create: `tests/test_web/test_routes/test_landing.py`

- [ ] **Step 1: Tulis test**

Create `tests/test_web/test_routes/test_landing.py`:

```python
"""Test landing page."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.web.routes.landing import router as landing_router


def _make_client():
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")
    app.include_router(landing_router)

    from fastapi.staticfiles import StaticFiles
    # static mount optional for test — template references resolve at render
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
```

- [ ] **Step 2: Run test — expect FAIL**

Run:
```bash
pytest tests/test_web/test_routes/test_landing.py -v
```
Expected: FAIL `ImportError`

- [ ] **Step 3: Implement landing route**

Create `app/web/routes/landing.py`:

```python
"""Landing page routes."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "landing.html",
        {"request": request, "csrf_token": request.session.get("csrf_token", "")},
    )
```

- [ ] **Step 4: Buat `landing.html`**

Create `app/web/templates/landing.html`:

```html
{% extends "base.html" %}
{% block title %}Pusdatin Helpdesk — Beranda{% endblock %}

{% block layout %}
<aside class="sidebar">
  <div class="logo">
    <div class="logo-dot">P</div>
    <span>Pusdatin</span>
  </div>
  <div style="font-size: 10px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px; margin-bottom: 10px;">Statistik Publik</div>
  <div style="margin-bottom: 14px;">
    <div style="font-size: 20px; font-weight: 700;">—</div>
    <div style="font-size: 11px; color: #94a3b8;">Total Tiket</div>
  </div>
</aside>

<main class="main" style="display: flex; align-items: center; justify-content: center;">
  <div style="max-width: 520px; text-align: center;">
    <h1 style="font-size: 28px; margin-bottom: 10px;">Helpdesk Keamanan Siber</h1>
    <p style="color: #64748b; margin-bottom: 24px;">
      Pra-triase insiden otomatis · Kementerian Pertanian
    </p>
    <div style="display: flex; gap: 12px; justify-content: center;">
      <a class="btn btn-primary" href="/lapor">Lapor Insiden →</a>
      <a class="btn btn-outline" href="/admin/login">Admin Login</a>
    </div>
  </div>
</main>
{% endblock %}
```

- [ ] **Step 5: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_routes/test_landing.py -v
```
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add app/web/routes/landing.py app/web/templates/landing.html tests/test_web/test_routes/test_landing.py
git commit -m "feat(web): landing page dengan CTA pelapor & admin"
```

---

## Task 12: Admin login routes

**Files:**
- Create: `app/web/routes/admin_auth.py`
- Create: `app/web/templates/admin/login.html`
- Create: `app/web/templates/admin/inbox_stub.html`
- Create: `tests/test_web/test_routes/test_admin_auth.py`

- [ ] **Step 1: Tulis test**

Create `tests/test_web/test_routes/test_admin_auth.py`:

```python
"""Test admin auth routes (login, logout)."""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from passlib.hash import bcrypt
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.database.models import Admin
from app.web.dependencies import get_db_session, _RedirectException
from app.web.middleware.csrf import CSRFMiddleware
from app.web.middleware.rate_limit import limiter
from app.web.routes.admin_auth import router as auth_router


@pytest.fixture
def admin_row():
    return Admin(
        id=1, username="admin1", email="a@x.com", full_name="Admin",
        password_hash=bcrypt.using(rounds=4).hash("pass1234"),
        is_active=True,
    )


def _make_client(admin_row, fake_redis):
    from starlette.responses import RedirectResponse

    app = FastAPI()
    app.state.limiter = limiter
    app.add_middleware(CSRFMiddleware, secret="csrf-secret",
                       exempt_paths=("/admin/login",))
    app.add_middleware(SessionMiddleware, secret_key="session-secret")

    @app.exception_handler(_RedirectException)
    async def _h(request, exc):
        return RedirectResponse(url=exc.location, status_code=303)

    def override_db():
        db = MagicMock()
        q = db.query.return_value.filter_by.return_value
        q.first.return_value = admin_row
        db.commit = MagicMock()
        return db

    app.dependency_overrides[get_db_session] = override_db

    # override redis client used in admin_auth
    import app.web.routes.admin_auth as mod
    mod._redis_client = lambda: fake_redis

    app.include_router(auth_router)
    return TestClient(app)


@pytest.fixture
def fake_redis():
    store = {}

    class R:
        def get(self, k): return store.get(k)
        def setex(self, k, t, v): store[k] = v
        def incr(self, k):
            store[k] = str(int(store.get(k, 0)) + 1); return int(store[k])
        def expire(self, k, t): pass
        def delete(self, k): store.pop(k, None)
    return R()


def test_login_get_renders_form(admin_row, fake_redis):
    client = _make_client(admin_row, fake_redis)
    r = client.get("/admin/login")
    assert r.status_code == 200
    assert "Username" in r.text
    assert "Password" in r.text


def test_login_post_correct_credentials(admin_row, fake_redis):
    client = _make_client(admin_row, fake_redis)
    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "pass1234"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/inbox"


def test_login_post_wrong_password(admin_row, fake_redis):
    client = _make_client(admin_row, fake_redis)
    r = client.post(
        "/admin/login",
        data={"username": "admin1", "password": "wrong"},
    )
    assert r.status_code == 200
    assert "tidak valid" in r.text.lower() or "invalid" in r.text.lower()
```

- [ ] **Step 2: Run test — expect FAIL**

Run:
```bash
pytest tests/test_web/test_routes/test_admin_auth.py -v
```
Expected: FAIL `ImportError`

- [ ] **Step 3: Implement admin_auth router**

Create `app/web/routes/admin_auth.py`:

```python
"""Admin authentication routes: login, logout."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Annotated

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
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db_session)],
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

    # Sukses — set session
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
```

- [ ] **Step 4: Buat template `admin/login.html`**

Create `app/web/templates/admin/login.html`:

```html
{% extends "base.html" %}
{% block title %}Admin Login — Pusdatin Helpdesk{% endblock %}

{% block layout %}
<div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; min-height: 100vh;">
  <div class="card" style="width: 360px;">
    <div style="text-align: center; margin-bottom: 20px;">
      <div style="width: 40px; height: 40px; background: #2563eb; border-radius: 8px; margin: 0 auto 12px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 600;">P</div>
      <h2 style="font-size: 18px;">Admin Login</h2>
      <p style="color: #64748b; font-size: 12px;">Pusdatin Helpdesk CSIRT</p>
    </div>

    {% if error %}
      <div class="flash flash-error">{{ error }}</div>
    {% endif %}

    <form method="post" action="/admin/login?next={{ next }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input class="form-input" type="text" name="username" required autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input class="form-input" type="password" name="password" required>
      </div>
      <button type="submit" class="btn btn-primary" style="width: 100%;">Masuk</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Buat template stub `admin/inbox_stub.html`**

Create `app/web/templates/admin/inbox_stub.html`:

```html
{% extends "base.html" %}
{% block title %}Inbox — Admin{% endblock %}

{% block layout %}
<aside class="sidebar">
  <div class="logo"><div class="logo-dot">P</div><span>Pusdatin CSIRT</span></div>
  <a class="nav-item active">📥 Inbox</a>
  <a class="nav-item">🎫 Tiket</a>
</aside>

<main class="main">
  <div class="topbar">
    <h2 style="font-size: 16px;">Inbox Tiket</h2>
    <form method="post" action="/admin/logout">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <button type="submit" class="btn btn-outline">Logout</button>
    </form>
  </div>
  <div class="card" style="margin-top: 20px;">
    <p>Halo, <strong>{{ admin.full_name }}</strong> — halaman inbox akan diimplementasikan di Plan B.</p>
  </div>
</main>
{% endblock %}
```

- [ ] **Step 6: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_routes/test_admin_auth.py -v
```
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add app/web/routes/admin_auth.py app/web/templates/admin/ tests/test_web/test_routes/test_admin_auth.py
git commit -m "feat(web): admin login/logout routes + template"
```

---

## Task 13: Wire-up di `app/main.py`

**Files:**
- Modify: `app/main.py`
- Create: `app/web/app.py`
- Create: `app/web/routes/admin_inbox_stub.py`

- [ ] **Step 1: Buat stub route `/admin/inbox`**

Create `app/web/routes/admin_inbox_stub.py`:

```python
"""Stub route untuk /admin/inbox — implementasi lengkap di Plan B."""
from pathlib import Path
from typing import Annotated

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
    admin: Annotated[Admin, Depends(get_current_admin)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        "admin/inbox_stub.html",
        {
            "request": request,
            "admin": admin,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )
```

- [ ] **Step 2: Buat `app/web/app.py` — setup helper**

Create `app/web/app.py`:

```python
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
from app.web.routes.admin_auth import router as admin_auth_router
from app.web.routes.admin_inbox_stub import router as admin_inbox_router
from app.web.routes.landing import router as landing_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def register_web(app: FastAPI) -> None:
    """Register middleware, static mount, routes, dan exception handler."""
    config = get_web_config()

    # Middleware — urutan: security headers (outer) → CSRF → session (inner)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CSRFMiddleware,
        secret=config.csrf_secret,
        exempt_paths=("/api/",),  # REST API existing pakai auth sendiri
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.session_secret,
        max_age=config.session_max_age,
        same_site="lax",
        https_only=config.cookie_secure,
    )

    # Rate limit
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Redirect exception (untuk get_current_admin)
    @app.exception_handler(_RedirectException)
    async def _redirect_handler(request: Request, exc: _RedirectException):
        return RedirectResponse(url=exc.location, status_code=303)

    # Static files
    app.mount(
        "/web/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="web_static",
    )

    # Routes
    app.include_router(landing_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_inbox_router)
```

- [ ] **Step 3: Update `app/main.py`**

Edit `app/main.py` — tambahkan import dan panggil `register_web(app)`:

```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.utils.logger import configure_logging
from app.web.app import register_web


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Helpdesk Keamanan Siber Pusdatin",
    description="Sistem helpdesk multi-agent untuk pra-triase insiden keamanan siber",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
register_web(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "helpdesk-api"}
```

Catatan: route `@app.get("/")` dihapus karena sekarang ditangani `landing_router`.

- [ ] **Step 4: Jalankan server dan verifikasi manual**

Run:
```bash
uvicorn app.main:app --reload --port 8000
```

Buka browser ke `http://localhost:8000/` — Expected: landing page muncul dengan dua tombol CTA.

Klik "Admin Login" → Expected: form login muncul.

Coba akses `http://localhost:8000/admin/inbox` tanpa login → Expected: redirect ke `/admin/login?next=/admin/inbox`.

- [ ] **Step 5: Run full test suite web**

Run:
```bash
pytest tests/test_web/ -v
```
Expected: semua test pass.

- [ ] **Step 6: Commit**

```bash
git add app/web/app.py app/web/routes/admin_inbox_stub.py app/main.py
git commit -m "feat(web): wire-up middleware, static, dan routes di main app"
```

---

## Task 14: Integration test end-to-end login flow

**Files:**
- Create: `tests/test_web/test_integration/__init__.py`
- Create: `tests/test_web/test_integration/test_login_flow.py`

- [ ] **Step 1: Tulis integration test dengan TestClient penuh**

Create `tests/test_web/test_integration/__init__.py` (empty).

Create `tests/test_web/test_integration/test_login_flow.py`:

```python
"""Integration test: login flow end-to-end melalui TestClient."""
import pytest
from fastapi.testclient import TestClient
from passlib.hash import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Admin, Base
from app.main import app
from app.web.dependencies import get_db_session


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    admin = Admin(
        username="integ_admin",
        email="integ@test.com",
        full_name="Integration Admin",
        password_hash=bcrypt.using(rounds=4).hash("integpass123"),
        is_active=True,
    )
    session.add(admin)
    session.commit()

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = override
    yield session
    session.close()
    app.dependency_overrides = {}


@pytest.fixture
def fake_redis_patch(monkeypatch):
    import fakeredis
    r = fakeredis.FakeStrictRedis(decode_responses=True)
    import app.web.routes.admin_auth as mod
    monkeypatch.setattr(mod, "_redis_client", lambda: r)
    return r


def test_full_login_flow(test_db, fake_redis_patch):
    client = TestClient(app)

    # 1. Landing page accessible
    r = client.get("/")
    assert r.status_code == 200

    # 2. Protected page redirects ke login
    r = client.get("/admin/inbox", follow_redirects=False)
    assert r.status_code == 303
    assert "/admin/login" in r.headers["location"]

    # 3. Login dengan kredensial benar
    r = client.post(
        "/admin/login",
        data={"username": "integ_admin", "password": "integpass123"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/inbox"

    # 4. Setelah login, inbox accessible
    r = client.get("/admin/inbox")
    assert r.status_code == 200
    assert "Integration Admin" in r.text

    # 5. Logout
    # (perlu CSRF token dari session, skip untuk simplicity atau ambil dari cookie)
```

- [ ] **Step 2: Run test — expect PASS**

Run:
```bash
pytest tests/test_web/test_integration/test_login_flow.py -v
```
Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_web/test_integration/
git commit -m "test(web): integration test login flow end-to-end"
```

---

## Task 15: Error templates + .gitignore

**Files:**
- Create: `app/web/templates/errors/403.html`
- Create: `app/web/templates/errors/404.html`
- Create: `app/web/templates/errors/500.html`
- Modify: `.gitignore`

- [ ] **Step 1: Buat template error 403**

Create `app/web/templates/errors/403.html`:

```html
{% extends "base.html" %}
{% block title %}403 — Forbidden{% endblock %}
{% block layout %}
<div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; min-height: 100vh;">
  <div style="text-align: center;">
    <h1 style="font-size: 48px; color: #dc2626;">403</h1>
    <p style="color: #64748b;">Akses ditolak.</p>
    <a class="btn btn-primary" href="/">Kembali ke Beranda</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Buat template error 404**

Create `app/web/templates/errors/404.html`:

```html
{% extends "base.html" %}
{% block title %}404 — Not Found{% endblock %}
{% block layout %}
<div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; min-height: 100vh;">
  <div style="text-align: center;">
    <h1 style="font-size: 48px; color: #64748b;">404</h1>
    <p style="color: #64748b;">Halaman tidak ditemukan.</p>
    <a class="btn btn-primary" href="/">Kembali ke Beranda</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Buat template error 500**

Create `app/web/templates/errors/500.html`:

```html
{% extends "base.html" %}
{% block title %}500 — Server Error{% endblock %}
{% block layout %}
<div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; min-height: 100vh;">
  <div style="text-align: center;">
    <h1 style="font-size: 48px; color: #dc2626;">500</h1>
    <p style="color: #64748b;">Terjadi kesalahan server.</p>
    {% if trace_id %}
      <p style="color: #94a3b8; font-size: 11px;">Trace ID: {{ trace_id }}</p>
    {% endif %}
    <a class="btn btn-primary" href="/">Kembali ke Beranda</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Update `.gitignore`**

Edit `.gitignore`, tambahkan di akhir file (jika belum ada):

```
# Web interface
web_uploads/
.superpowers/
```

- [ ] **Step 5: Commit**

```bash
git add app/web/templates/errors/ .gitignore
git commit -m "feat(web): error templates + gitignore uploads"
```

---

## Task 16: Manual verification & final smoke test

- [ ] **Step 1: Jalankan full test suite web**

Run:
```bash
pytest tests/test_web/ -v
```
Expected: semua test pass, coverage ≥ 70% untuk module web.

- [ ] **Step 2: Seed admin user test**

Run (interaktif):
```bash
python scripts/seed_admin.py
```
Input: username `admintest`, password `test1234`, dll. Expected: `OK — admin 'admintest' berhasil dibuat.`

- [ ] **Step 3: Start server**

Run:
```bash
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 4: Manual checklist di browser**

Buka `http://localhost:8000/` dan verifikasi:

- [ ] Landing page tampil dengan 2 CTA (Lapor Insiden, Admin Login)
- [ ] Styling biru minimalist terlihat benar (sidebar gelap, button biru)
- [ ] Klik "Admin Login" → form login muncul
- [ ] Submit password salah → error "Username atau password tidak valid."
- [ ] Submit 5x password salah → error "Terlalu banyak percobaan gagal"
- [ ] Submit password benar → redirect ke `/admin/inbox`
- [ ] `/admin/inbox` tampil dengan sapaan "Halo, admintest"
- [ ] Klik Logout → redirect ke landing page
- [ ] Akses `/admin/inbox` tanpa login → redirect ke `/admin/login?next=/admin/inbox`
- [ ] DevTools Network tab: response headers include `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: ...`
- [ ] Akses `/admin/login` 6x cepat → rate limit 429 muncul

- [ ] **Step 5: Commit final (tag Plan A complete)**

```bash
git tag -a plan-a-complete -m "Plan A — Foundation & Auth selesai"
```

---

## Definition of Done

- ✅ Semua test di `tests/test_web/` pass
- ✅ Admin bisa login via browser dengan kredensial dari `seed_admin.py`
- ✅ Session cookie HttpOnly, SameSite=Lax, signed
- ✅ Security headers aktif di semua response (verifikasi di DevTools)
- ✅ CSRF protection aktif untuk POST (kecuali login yang exempt)
- ✅ Rate limit login 5/menit aktif
- ✅ Lockout counter di Redis bekerja (5x gagal = locked)
- ✅ Landing page, login page, dan stub inbox render dengan styling biru minimalist
- ✅ Unprotected access ke `/admin/*` redirect ke login

## Out of Scope (Plan Berikutnya)

- **Plan B**: Inbox nyata (filter, tabel, detail tiket, update status, notify Telegram, attachment download)
- **Plan C**: Chat pelapor + upload file + integrasi `helpdesk_graph.ainvoke`
- **Plan D**: RAG management + Report generation + polish visual
