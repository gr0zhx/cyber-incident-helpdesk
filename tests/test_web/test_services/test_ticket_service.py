from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, IncidentTicket
from app.web.services.ticket_service import TicketFilters, TicketService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_ticket(db, ticket_id, status="PENDING_REVIEW", severity="HIGH", offset_min=0):
    t = IncidentTicket(
        ticket_id=ticket_id,
        reporter_id="tg:123",
        reporter_name="Pelapor",
        incident_type="PHISHING",
        severity=severity,
        description_raw="x",
        description_sanitized="x",
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=offset_min),
    )
    db.add(t)
    db.commit()
    return t


def test_list_tickets_returns_all_when_no_filter(db):
    for i in range(3):
        _make_ticket(db, f"INC-{i}", offset_min=i)
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(), page=1, page_size=25)
    assert result.total == 3
    # offset_min=0 → newest, so INC-0 first
    assert [t.ticket_id for t in result.items] == ["INC-0", "INC-1", "INC-2"]


def test_list_tickets_filters_by_status(db):
    _make_ticket(db, "A", status="PENDING_REVIEW")
    _make_ticket(db, "B", status="RESOLVED")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(status="RESOLVED"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "B"


def test_list_tickets_filters_by_severity(db):
    _make_ticket(db, "A", severity="HIGH")
    _make_ticket(db, "B", severity="LOW")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(severity="LOW"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "B"


def test_list_tickets_search_by_ticket_id_or_name(db):
    _make_ticket(db, "INC-100")
    _make_ticket(db, "INC-200")
    svc = TicketService(db)
    result = svc.list_tickets(TicketFilters(search="200"), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "INC-200"


def test_list_tickets_filters_by_date_range(db):
    _make_ticket(db, "OLD", offset_min=60 * 24 * 10)  # 10 hari lalu
    _make_ticket(db, "NEW", offset_min=0)
    svc = TicketService(db)
    date_from = datetime.now(timezone.utc) - timedelta(days=1)
    result = svc.list_tickets(TicketFilters(date_from=date_from), page=1, page_size=25)
    assert result.total == 1 and result.items[0].ticket_id == "NEW"


def test_list_tickets_status_counts_respect_date_range(db):
    _make_ticket(db, "OLD", status="RESOLVED", offset_min=60 * 24 * 10)
    _make_ticket(db, "NEW", status="RESOLVED", offset_min=0)
    svc = TicketService(db)
    date_from = datetime.now(timezone.utc) - timedelta(days=1)
    result = svc.list_tickets(TicketFilters(date_from=date_from), page=1, page_size=25)
    assert result.resolved_count == 1


def test_list_tickets_pagination(db):
    for i in range(30):
        _make_ticket(db, f"INC-{i:03d}", offset_min=i)
    svc = TicketService(db)
    page1 = svc.list_tickets(TicketFilters(), page=1, page_size=25)
    page2 = svc.list_tickets(TicketFilters(), page=2, page_size=25)
    assert page1.total == 30
    assert len(page1.items) == 25
    assert len(page2.items) == 5
    assert page1.total_pages == 2


def test_get_ticket_detail_returns_ticket(db):
    _make_ticket(db, "INC-X")
    svc = TicketService(db)
    t = svc.get_ticket_detail("INC-X")
    assert t.ticket_id == "INC-X"


def test_get_ticket_detail_returns_none_when_missing(db):
    svc = TicketService(db)
    assert svc.get_ticket_detail("NOPE") is None


def test_update_status_sets_field_and_returns_old(db):
    _make_ticket(db, "INC-A", status="PENDING_REVIEW")
    svc = TicketService(db)
    old = svc.update_status("INC-A", "IN_PROGRESS", modified_by="admin1")
    db.commit()
    assert old == "PENDING_REVIEW"
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().status == "IN_PROGRESS"


def test_update_status_rejects_invalid_status(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    with pytest.raises(ValueError):
        svc.update_status("INC-A", "NOT_A_STATUS", modified_by="admin1")


def test_assign_sets_assigned_to(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    svc.assign("INC-A", "andi", modified_by="admin1")
    db.commit()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().assigned_to == "andi"


def test_set_escalation_level(db):
    _make_ticket(db, "INC-A")
    svc = TicketService(db)
    svc.set_escalation("INC-A", "HIGH", modified_by="admin1")
    db.commit()
    assert db.query(IncidentTicket).filter_by(ticket_id="INC-A").one().escalation_level == "HIGH"
