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
