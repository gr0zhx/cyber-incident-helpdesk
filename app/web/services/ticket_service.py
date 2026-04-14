"""Service layer untuk operasi tiket pada dashboard admin web."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.models import IncidentTicket
from app.web.constants import ESCALATION_LEVELS, TICKET_STATUSES


@dataclass
class TicketFilters:
    status: Optional[str] = None
    severity: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class TicketListResult:
    items: list[IncidentTicket]
    total: int
    page: int
    page_size: int
    total_pages: int


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tickets(
        self,
        filters: TicketFilters,
        page: int = 1,
        page_size: int = 25,
    ) -> TicketListResult:
        query = self.db.query(IncidentTicket)
        if filters.status:
            query = query.filter(IncidentTicket.status == filters.status)
        if filters.severity:
            query = query.filter(IncidentTicket.severity == filters.severity)
        if filters.search:
            like = f"%{filters.search}%"
            query = query.filter(
                or_(
                    IncidentTicket.ticket_id.ilike(like),
                    IncidentTicket.reporter_name.ilike(like),
                )
            )
        if filters.date_from:
            query = query.filter(IncidentTicket.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(IncidentTicket.created_at <= filters.date_to)

        total = query.count()
        total_pages = max(1, ceil(total / page_size)) if total else 1
        items = (
            query.order_by(IncidentTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return TicketListResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_ticket_detail(self, ticket_id: str) -> Optional[IncidentTicket]:
        return (
            self.db.query(IncidentTicket)
            .filter(IncidentTicket.ticket_id == ticket_id)
            .first()
        )

    def update_status(self, ticket_id: str, new_status: str, modified_by: str) -> str:
        if new_status not in TICKET_STATUSES:
            raise ValueError(f"Status tidak valid: {new_status}")
        ticket = self._get_or_raise(ticket_id)
        old = ticket.status
        ticket.status = new_status
        ticket.modified_by = modified_by
        if new_status == "IN_PROGRESS" and ticket.reviewed_at is None:
            ticket.reviewed_at = datetime.utcnow()
        if new_status == "RESOLVED":
            ticket.resolved_at = datetime.utcnow()
        if new_status == "CLOSED":
            ticket.closed_at = datetime.utcnow()
        return old

    def assign(self, ticket_id: str, assignee: str, modified_by: str) -> None:
        ticket = self._get_or_raise(ticket_id)
        ticket.assigned_to = assignee
        ticket.modified_by = modified_by

    def set_escalation(self, ticket_id: str, level: str, modified_by: str) -> None:
        if level not in ESCALATION_LEVELS:
            raise ValueError(f"Escalation level tidak valid: {level}")
        ticket = self._get_or_raise(ticket_id)
        ticket.escalation_level = level
        ticket.modified_by = modified_by

    def _get_or_raise(self, ticket_id: str) -> IncidentTicket:
        ticket = self.get_ticket_detail(ticket_id)
        if ticket is None:
            raise LookupError(f"Tiket {ticket_id} tidak ditemukan.")
        return ticket
