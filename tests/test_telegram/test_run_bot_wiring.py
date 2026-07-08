"""Regression test — Bug 1: notifikasi Telegram terkirim dobel.

Root cause: scripts/run_bot.py membangun NotifierAgent dengan telegram_client
ASLI untuk graph pipeline bot Telegram. Node send_notification di dalam graph
lalu mengirim pesan langsung ke CSIRT & pelapor via notifier, PADAHAL
app/telegram/bot.py::_send_result sudah mengirim konfirmasi ke pelapor
(reply_text) dan alert ke grup CSIRT (context.bot.send_message) secara
terpisah setelah graph selesai. Hasilnya: setiap laporan terkirim DUA KALI.

Bandingkan dengan flow web di app/api/dependencies.py — di situ notifier
sengaja dibuat log-only (telegram_client=None) karena app/web/routes/pelapor.py
tidak punya jalur pengiriman sendiri.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import run_bot  # noqa: E402


def test_bot_notifier_is_log_only_to_avoid_duplicate_telegram_messages():
    """Notifier yang dipasang ke graph bot Telegram harus log-only
    (telegram_client=None) — bot.py yang bertanggung jawab mengirim pesan
    Telegram untuk channel ini, bukan notifier di dalam graph."""
    fake_telegram_bot = MagicMock()
    notifier = run_bot._build_notifier(fake_telegram_bot)
    assert notifier.telegram is None
