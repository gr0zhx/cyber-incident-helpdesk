import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.database.repository import AuditRepository, TicketRepository, generate_ticket_id

# Use in-memory SQLite for unit tests (no PostgreSQL required)
SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture
def db():
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def _minimal_ticket(overrides: dict | None = None) -> dict:
    data = {
        "reporter_id": "user_001",
        "incident_type": "phishing",
        "severity": "Tinggi",
        "description_raw": "Saya menerima email mencurigakan yang meminta password.",
        "description_sanitized": "Saya menerima email mencurigakan yang meminta password.",
    }
    if overrides:
        data.update(overrides)
    return data


def test_create_ticket(db):
    repo = TicketRepository(db)
    ticket = repo.create_ticket(_minimal_ticket())

    assert ticket.ticket_id.startswith("TICKET-")
    assert ticket.status == "PENDING_REVIEW"
    assert ticket.reporter_id == "user_001"


def test_get_ticket_by_id(db):
    repo = TicketRepository(db)
    created = repo.create_ticket(_minimal_ticket())

    fetched = repo.get_ticket_by_id(created.ticket_id)
    assert fetched is not None
    assert fetched.ticket_id == created.ticket_id

    assert repo.get_ticket_by_id("TICKET-9999-0000") is None


def test_generate_ticket_id_format(db):
    from datetime import datetime, timezone

    ticket_id = generate_ticket_id(db)
    year = datetime.now(timezone.utc).year

    assert ticket_id.startswith(f"TICKET-{year}-")
    parts = ticket_id.split("-")
    assert len(parts) == 3
    assert parts[2].isdigit() and len(parts[2]) == 4


def test_generate_ticket_id_increments(db):
    repo = TicketRepository(db)
    t1 = repo.create_ticket(_minimal_ticket())
    t2 = repo.create_ticket(_minimal_ticket({"reporter_id": "user_002"}))

    seq1 = int(t1.ticket_id.split("-")[2])
    seq2 = int(t2.ticket_id.split("-")[2])
    assert seq2 == seq1 + 1


def test_check_duplicate(db):
    repo = TicketRepository(db)
    description = "Saya menerima email mencurigakan yang meminta password."
    repo.create_ticket(_minimal_ticket())

    duplicate = repo.check_duplicate("user_001", description)
    assert duplicate is not None

    no_dup = repo.check_duplicate("user_001", "Ini laporan berbeda sama sekali.")
    assert no_dup is None

    no_dup_other = repo.check_duplicate("user_999", description)
    assert no_dup_other is None


def test_update_ticket_status(db):
    repo = TicketRepository(db)
    ticket = repo.create_ticket(_minimal_ticket())
    assert ticket.status == "PENDING_REVIEW"

    updated = repo.update_ticket_status(ticket.ticket_id, "IN_PROGRESS")
    assert updated.status == "IN_PROGRESS"

    assert repo.update_ticket_status("TICKET-9999-0000", "CLOSED") is None


def test_audit_log_event(db):
    repo = AuditRepository(db)
    log = repo.log_event(
        {
            "event_type": "classification",
            "session_id": "sess_abc",
            "agent_name": "identifier",
            "action": "classify_incident",
        }
    )
    assert log.log_id is not None
    assert log.event_type == "classification"


def test_audit_get_events_by_session(db):
    repo = AuditRepository(db)
    repo.log_event({"event_type": "start", "session_id": "sess_xyz", "action": "begin"})
    repo.log_event({"event_type": "end", "session_id": "sess_xyz", "action": "finish"})
    repo.log_event({"event_type": "other", "session_id": "sess_other", "action": "x"})

    events = repo.get_events_by_session("sess_xyz")
    assert len(events) == 2
    assert all(e.session_id == "sess_xyz" for e in events)
