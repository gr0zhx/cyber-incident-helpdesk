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

    def update_ticket(self, ticket_id: str, updates: dict) -> Optional[IncidentTicket]:
        """Update beberapa field tiket sekaligus (untuk admin dashboard).

        Field yang bisa diupdate: status, assigned_to, modified_by.
        Field timestamp reviewed_at/resolved_at/closed_at diisi otomatis.
        """
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket is None:
            return None

        now = datetime.now(timezone.utc)
        allowed_fields = {"status", "assigned_to", "modified_by", "escalation_level"}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(ticket, field, value)

        # Set timestamp berdasarkan status
        new_status = updates.get("status", ticket.status)
        if new_status == "IN_PROGRESS" and ticket.reviewed_at is None:
            ticket.reviewed_at = now
        elif new_status == "RESOLVED" and ticket.resolved_at is None:
            ticket.resolved_at = now
        elif new_status == "CLOSED" and ticket.closed_at is None:
            ticket.closed_at = now

        ticket.updated_at = now
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_all_tickets(self, limit: int = 200) -> list[IncidentTicket]:
        """Ambil semua tiket terbaru (untuk dashboard admin)."""
        return (
            self.db.query(IncidentTicket)
            .order_by(IncidentTicket.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_stats(self) -> dict:
        """Statistik ringkasan tiket untuk dashboard."""
        from sqlalchemy import case

        total = self.db.query(func.count(IncidentTicket.ticket_id)).scalar() or 0
        by_status = (
            self.db.query(IncidentTicket.status, func.count(IncidentTicket.ticket_id))
            .group_by(IncidentTicket.status)
            .all()
        )
        by_severity = (
            self.db.query(IncidentTicket.severity, func.count(IncidentTicket.ticket_id))
            .group_by(IncidentTicket.severity)
            .all()
        )
        by_type = (
            self.db.query(IncidentTicket.incident_type, func.count(IncidentTicket.ticket_id))
            .group_by(IncidentTicket.incident_type)
            .all()
        )
        return {
            "total": total,
            "by_status": {s: c for s, c in by_status},
            "by_severity": {s: c for s, c in by_severity},
            "by_type": {t: c for t, c in by_type},
        }

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
