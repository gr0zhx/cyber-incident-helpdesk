"""Wrap fungsi notifikasi Telegram existing agar bisa dipanggil dari web dashboard."""
import logging

from app.api.routes import _notify_reporter_status

logger = logging.getLogger(__name__)


class NotificationService:
    """Bungkus `_notify_reporter_status` — tidak menduplikasi logika Telegram."""

    async def notify_status(
        self, reporter_id: str, ticket_id: str, new_status: str
    ) -> bool:
        """Kirim notifikasi status ke pelapor. Return True jika terkirim."""
        if not reporter_id or not reporter_id.startswith("tg:"):
            logger.info(
                "Notifikasi dilewati: channel non-telegram untuk reporter %s",
                reporter_id,
            )
            return False
        try:
            await _notify_reporter_status(
                reporter_id=reporter_id,
                ticket_id=ticket_id,
                new_status=new_status,
            )
            return True
        except Exception as exc:
            logger.warning("NotificationService gagal kirim: %s", exc)
            return False
