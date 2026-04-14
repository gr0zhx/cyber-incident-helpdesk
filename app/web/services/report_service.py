"""Wrap report_generator untuk download laporan insiden dari web dashboard."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.dashboard.report_generator import generate_report_filename, generate_report_html
from app.database.models import IncidentTicket


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate(self, ticket_id: str, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> tuple[str, str]:
        """Generate laporan HTML untuk satu tiket. Return (html_string, filename)."""
        ticket = self.db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
        if ticket is None:
            raise LookupError(f"Tiket {ticket_id} tidak ditemukan.")
        ticket_dict = {
            "ticket_id": ticket.ticket_id,
            "incident_type": ticket.incident_type,
            "severity": ticket.severity,
            "status": ticket.status,
            "escalation_level": ticket.escalation_level,
            "reporter_name": ticket.reporter_name,
            "reporter_id": ticket.reporter_id,
            "assigned_to": ticket.assigned_to,
            "description_sanitized": ticket.description_sanitized,
            "mitigation_recommendation": ticket.mitigation_recommendation,
            "confidence_score": float(ticket.confidence_score or 0),
            "created_at": str(ticket.created_at) if ticket.created_at else None,
            "updated_at": str(ticket.updated_at) if ticket.updated_at else None,
            "reviewed_at": str(ticket.reviewed_at) if ticket.reviewed_at else None,
            "resolved_at": str(ticket.resolved_at) if ticket.resolved_at else None,
        }
        html = generate_report_html(ticket_dict, prepared_by=prepared_by)
        filename = generate_report_filename(ticket_dict)
        return html, filename
