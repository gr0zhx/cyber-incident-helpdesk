"""Notifier Agent — format dan kirim notifikasi ke CSIRT dan pelapor via Telegram."""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app.telegram.templates import format_csirt_alert, format_reporter_confirmation

logger = logging.getLogger(__name__)

# Severity yang memerlukan eskalasi ke channel prioritas / manager
HIGH_PRIORITY_SEVERITIES = {"Kritis", "Tinggi"}

def _get_csirt_recipients(severity: str) -> list[str]:
    """Tentukan daftar penerima CSIRT berdasarkan severity."""
    recipients = []
    csirt_id = os.getenv("CSIRT_CHAT_ID", "")
    if csirt_id:
        recipients.append(csirt_id)

    if severity in HIGH_PRIORITY_SEVERITIES:
        manager_id = os.getenv("CSIRT_MANAGER_CHAT_ID", "")
        if manager_id and manager_id not in recipients:
            recipients.append(manager_id)

    return recipients


class NotifierAgent:
    def __init__(self, telegram_client=None) -> None:
        # telegram_client: python-telegram-bot Bot instance atau None (mode log)
        self.telegram = telegram_client

    async def send_notifications(self, incident_state: dict) -> dict:
        """Format dan kirim notifikasi.

        Jika telegram_client is None, pesan hanya di-log (untuk testing / dev).
        Selalu mengembalikan dict — tidak pernah raise.
        """
        csirt_message = self._format_csirt_notification(incident_state)
        reporter_message = self._format_reporter_confirmation(incident_state)

        severity = incident_state.get("severity", "Sedang")
        csirt_recipients = _get_csirt_recipients(severity)
        timestamp = datetime.now(timezone.utc).isoformat()

        if self.telegram is None:
            # Mode log — digunakan saat testing atau tidak ada bot token
            logger.info("[NOTIFIER] Notifikasi CSIRT:\n%s", csirt_message)
            logger.info("[NOTIFIER] Konfirmasi pelapor:\n%s", reporter_message)
            return {
                "notification_sent": True,
                "notification_recipients": csirt_recipients,
                "notification_timestamp": timestamp,
            }

        # Kirim via Telegram
        sent = False
        try:
            for chat_id in csirt_recipients:
                await self.telegram.send_message(chat_id=chat_id, text=csirt_message)

            reporter_id = incident_state.get("reporter_id", "")
            if reporter_id:
                await self.telegram.send_message(chat_id=reporter_id, text=reporter_message)

            sent = True
        except Exception as exc:
            logger.error("Gagal mengirim notifikasi Telegram: %s", exc)

        return {
            "notification_sent": sent,
            "notification_recipients": csirt_recipients,
            "notification_timestamp": timestamp,
        }

    def _format_csirt_notification(self, state: dict) -> str:
        return format_csirt_alert(
            ticket_id=state.get("ticket_id", "TICKET-UNKNOWN"),
            incident_type=state.get("incident_type", "Tidak diketahui"),
            severity=state.get("severity", "Sedang"),
            reporter_name=state.get("reporter_name", ""),
            timestamp=state.get("timestamp_received", datetime.now(timezone.utc).isoformat()),
            description_short=state.get("sanitized_input", state.get("raw_input", "")),
            mitigation_short=state.get("mitigation_recommendation", ""),
        )

    def _format_reporter_confirmation(self, state: dict) -> str:
        return format_reporter_confirmation(
            ticket_id=state.get("ticket_id", "TICKET-UNKNOWN"),
            incident_type=state.get("incident_type", "Tidak diketahui"),
            severity=state.get("severity", "Sedang"),
            confidence=state.get("confidence_score", 0.0),
            mitigation_steps=state.get("mitigation_recommendation", ""),
        )
