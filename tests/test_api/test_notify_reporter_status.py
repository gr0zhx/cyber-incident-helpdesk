"""Regression test — Bug 2: reporter_id ber-prefix channel ('tg:'/'web:')
harus di-strip dulu menjadi chat_id Telegram asli sebelum dikirim ke API,
bukan diteruskan mentah-mentah sebagai chat_id."""
from unittest.mock import AsyncMock, patch

import pytest

from app.api.routes import _notify_reporter_status


@pytest.mark.asyncio
async def test_notify_reporter_status_strips_tg_prefix_for_chat_id(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")

    mock_bot_instance = AsyncMock()
    mock_bot_instance.send_message = AsyncMock()
    mock_bot_instance.__aenter__ = AsyncMock(return_value=mock_bot_instance)
    mock_bot_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("telegram.Bot", return_value=mock_bot_instance):
        await _notify_reporter_status(
            reporter_id="tg:123456", ticket_id="INC-1", new_status="IN_PROGRESS"
        )

    mock_bot_instance.send_message.assert_awaited_once()
    assert mock_bot_instance.send_message.call_args.kwargs["chat_id"] == "123456"
