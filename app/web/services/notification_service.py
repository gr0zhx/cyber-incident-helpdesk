"""Wrap fungsi notifikasi existing agar bisa dipanggil dari web dashboard."""
import logging
import os

from app.api.routes import _notify_reporter_status

logger = logging.getLogger(__name__)


class NotificationService:
    """Bungkus notifikasi Telegram dan fallback tautan aman untuk pelapor web."""

    @staticmethod
    def build_reporter_status_link(access_token: str) -> str:
        public_base = (os.getenv("PUBLIC_BASE_URL", "") or "").rstrip("/")
        path = f"/lapor/akses/{access_token}"
        return f"{public_base}{path}" if public_base else path

    async def notify_status(
        self,
        reporter_id: str,
        ticket_id: str,
        new_status: str,
        reporter_access_token: str = "",
    ) -> dict:
        """Kirim notifikasi status ke pelapor atau sediakan tautan aman."""
        if not reporter_id or not reporter_id.startswith("tg:"):
            if reporter_id.startswith("web:") and reporter_access_token:
                return {
                    "ok": True,
                    "channel": "web_inbox",
                    "link": self.build_reporter_status_link(reporter_access_token),
                }
            logger.info("Notifikasi dilewati: channel non-telegram untuk reporter %s", reporter_id)
            return {"ok": False, "channel": "unsupported"}

        try:
            await _notify_reporter_status(
                reporter_id=reporter_id,
                ticket_id=ticket_id,
                new_status=new_status,
            )
            return {"ok": True, "channel": "telegram"}
        except Exception as exc:
            logger.warning("NotificationService gagal kirim: %s", exc)
            return {"ok": False, "channel": "telegram"}
