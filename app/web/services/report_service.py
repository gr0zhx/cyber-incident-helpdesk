"""Wrap report_generator untuk download laporan insiden dari web dashboard."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.dashboard.pdf_report_generator import generate_report_filename, generate_report_pdf
from app.database.models import IncidentTicket


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate(self, ticket_id: str, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> tuple[bytes, str]:
        """Generate laporan PDF (formulir resmi Kementan) untuk satu tiket. Return (pdf_bytes, filename)."""
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
            "reporter_contact": ticket.reporter_contact,
            "reporter_department": ticket.reporter_department,
            "assigned_to": ticket.assigned_to,
            "description_sanitized": ticket.description_sanitized,
            "mitigation_recommendation": ticket.mitigation_recommendation,
            "confidence_score": float(ticket.confidence_score or 0),
            # Bagian A / B
            "media_pelaporan": ticket.media_pelaporan,
            "incident_time": ticket.incident_time,
            "affected_asset": ticket.affected_asset,
            # Bagian C
            "cia_confidentiality": ticket.cia_confidentiality,
            "cia_integrity": ticket.cia_integrity,
            "cia_availability": ticket.cia_availability,
            # Bagian D
            "containment_action": ticket.containment_action,
            "recovery_action": ticket.recovery_action,
            # Timestamps
            "created_at": str(ticket.created_at) if ticket.created_at else None,
            "updated_at": str(ticket.updated_at) if ticket.updated_at else None,
            "reviewed_at": str(ticket.reviewed_at) if ticket.reviewed_at else None,
            "resolved_at": str(ticket.resolved_at) if ticket.resolved_at else None,
            "closed_at": str(ticket.closed_at) if ticket.closed_at else None,
        }
        pdf_bytes = generate_report_pdf(ticket_dict, prepared_by=prepared_by)
        filename = generate_report_filename(ticket_dict)
        return pdf_bytes, filename
