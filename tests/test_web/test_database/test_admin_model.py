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
