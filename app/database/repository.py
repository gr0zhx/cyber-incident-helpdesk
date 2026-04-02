from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import AuditLog, IncidentTicket


def generate_ticket_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"TICKET-{year}-"
    count = (
        db.query(func.count(IncidentTicket.ticket_id))
        .filter(IncidentTicket.ticket_id.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_ticket(self, ticket_data: dict) -> IncidentTicket:
        if "ticket_id" not in ticket_data or not ticket_data["ticket_id"]:
            ticket_data["ticket_id"] = generate_ticket_id(self.db)
        ticket_data.setdefault("status", "PENDING_REVIEW")
        ticket = IncidentTicket(**ticket_data)
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_ticket_by_id(self, ticket_id: str) -> Optional[IncidentTicket]:
        return (
            self.db.query(IncidentTicket)
            .filter(IncidentTicket.ticket_id == ticket_id)
            .first()
        )

    def get_tickets_by_reporter(self, reporter_id: str) -> list[IncidentTicket]:
        return (
            self.db.query(IncidentTicket)
            .filter(IncidentTicket.reporter_id == reporter_id)
            .order_by(IncidentTicket.created_at.desc())
            .all()
        )

    def update_ticket_status(self, ticket_id: str, status: str) -> Optional[IncidentTicket]:
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket is None:
            return None
        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def check_duplicate(
        self, reporter_id: str, description: str, hours: int = 24
    ) -> Optional[IncidentTicket]:
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        candidates = (
            self.db.query(IncidentTicket)
            .filter(
                IncidentTicket.reporter_id == reporter_id,
                IncidentTicket.created_at >= cutoff,
            )
            .all()
        )
        desc_lower = description.lower()
        for ticket in candidates:
            if ticket.description_raw.lower() == desc_lower:
                return ticket
        return None


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log_event(self, event_data: dict) -> AuditLog:
        log = AuditLog(**event_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_events_by_session(self, session_id: str) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.session_id == session_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )
