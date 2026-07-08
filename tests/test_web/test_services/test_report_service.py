from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, IncidentTicket
from app.web.services.report_service import ReportService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(IncidentTicket(
        ticket_id="INC-R1",
        reporter_id="tg:1",
        reporter_name="Budi",
        incident_type="PHISHING",
        severity="HIGH",
        description_raw="x",
        description_sanitized="Phishing email",
        status="RESOLVED",
        mitigation_recommendation="Isolasi host.",
    ))
    session.commit()
    yield session
    session.close()


def test_generate_returns_pdf_bytes(db):
    svc = ReportService(db)
    pdf_bytes, filename = svc.generate("INC-R1")
    assert pdf_bytes[:5] == b"%PDF-"
    assert filename.endswith(".pdf")


def test_generate_raises_for_missing_ticket(db):
    svc = ReportService(db)
    with pytest.raises(LookupError):
        svc.generate("NOPE")
