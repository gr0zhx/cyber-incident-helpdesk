"""Ticket Manager Agent — merangkai IncidentState menjadi tiket dan menyimpan ke database."""
import logging
from typing import Optional

from app.database.repository import TicketRepository

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["raw_input", "sanitized_input", "reporter_id", "incident_type", "severity"]

ESCALATION_MAP = {
    "Kritis": "Segera",
    "Tinggi": "Mendesak",
    "Sedang": "Standar",
    "Rendah": "Rutin",
    "Informasional": "Rutin",
}


class TicketManagerAgent:
    def __init__(self, ticket_repository: TicketRepository) -> None:
        self.repo = ticket_repository

    async def create_ticket(self, incident_state: dict) -> dict:
        """Buat tiket dari IncidentState.

        Selalu mengembalikan dict — tidak pernah raise.
        Return fields: ticket_id, ticket_status, escalation_level, is_duplicate (opsional), error (opsional).
        """
        # 1. Validasi field wajib
        missing = [f for f in REQUIRED_FIELDS if not incident_state.get(f)]
        if missing:
            logger.error("Field wajib tidak ada di incident_state: %s", missing)
            return {
                "ticket_id": "",
                "ticket_status": "ERROR",
                "escalation_level": "",
                "error": f"Field wajib tidak ada: {', '.join(missing)}",
            }

        severity = incident_state["severity"]
        escalation_level = ESCALATION_MAP.get(severity, "Standar")
        reporter_id = incident_state["reporter_id"]
        raw_input = incident_state["raw_input"]

        # 2. Cek duplikat
        try:
            duplicate = self.repo.check_duplicate(reporter_id, raw_input)
        except Exception as exc:
            logger.warning("Gagal cek duplikat: %s — lanjut buat tiket baru.", exc)
            duplicate = None

        if duplicate is not None:
            logger.info("Tiket duplikat ditemukan: %s", duplicate.ticket_id)
            return {
                "ticket_id": duplicate.ticket_id,
                "ticket_status": duplicate.status,
                "escalation_level": duplicate.escalation_level or escalation_level,
                "is_duplicate": True,
            }

        # 3. Bangun data tiket dari IncidentState
        ticket_data: dict = {
            "reporter_id": reporter_id,
            "reporter_name": incident_state.get("reporter_name", ""),
            "reporter_contact": incident_state.get("reporter_contact", ""),
            "incident_type": incident_state["incident_type"],
            "severity": severity,
            "confidence_score": incident_state.get("confidence_score"),
            "description_raw": raw_input,
            "description_sanitized": incident_state["sanitized_input"],
            "mitigation_recommendation": incident_state.get("mitigation_recommendation", ""),
            "citations": incident_state.get("citations", []),
            "rag_confidence": incident_state.get("rag_confidence"),
            "escalation_level": escalation_level,
            "classification_reasoning": incident_state.get("classification_reasoning", ""),
            "agent_trace": incident_state.get("agent_trace", []),
            "status": "PENDING_REVIEW",
            "created_by": "SYSTEM",
        }

        # 4. Simpan ke database
        try:
            ticket = self.repo.create_ticket(ticket_data)
            logger.info("Tiket dibuat: %s (eskalasi: %s)", ticket.ticket_id, ticket.escalation_level)
            return {
                "ticket_id": ticket.ticket_id,
                "ticket_status": ticket.status,
                "escalation_level": ticket.escalation_level,
                "is_duplicate": False,
            }
        except Exception as exc:
            logger.exception("Gagal menyimpan tiket ke database: %s", exc)
            return {
                "ticket_id": "",
                "ticket_status": "ERROR",
                "escalation_level": escalation_level,
                "error": f"Gagal menyimpan tiket: {type(exc).__name__}",
            }
