import asyncio
from unittest.mock import AsyncMock, patch

from app.web.services.notification_service import NotificationService


def test_notify_returns_true_on_success():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(return_value=None),
    ) as mock:
        ok = asyncio.run(svc.notify_status("tg:123", "INC-1", "IN_PROGRESS"))
    assert ok is True
    mock.assert_awaited_once_with(
        reporter_id="tg:123", ticket_id="INC-1", new_status="IN_PROGRESS"
    )


def test_notify_returns_false_on_exception():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        ok = asyncio.run(svc.notify_status("tg:123", "INC-1", "IN_PROGRESS"))
    assert ok is False


def test_notify_skips_non_telegram_channel():
    svc = NotificationService()
    with patch(
        "app.web.services.notification_service._notify_reporter_status",
        new=AsyncMock(),
    ) as mock:
        ok = asyncio.run(svc.notify_status("web:abc", "INC-1", "IN_PROGRESS"))
    assert ok is False
    mock.assert_not_called()
