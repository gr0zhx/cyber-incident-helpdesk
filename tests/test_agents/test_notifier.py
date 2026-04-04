"""Unit tests for NotifierAgent."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.notifier import NotifierAgent, _get_csirt_recipients
from app.telegram.templates import (
    format_csirt_alert,
    format_reporter_confirmation,
    SEVERITY_EMOJI,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> dict:
    base = {
        "ticket_id": "TICKET-2026-0001",
        "incident_type": "Phishing",
        "severity": "Tinggi",
        "reporter_id": "user_123",
        "reporter_name": "Budi Santoso",
        "reporter_contact": "@budi",
        "sanitized_input": "Email phishing dari CEO palsu.",
        "raw_input": "Email phishing dari CEO palsu.",
        "mitigation_recommendation": "1. Jangan klik link. [NIST SP 800-61]",
        "confidence_score": 0.92,
        "timestamp_received": "2026-04-04T10:00:00+00:00",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Template helper tests (pure functions)
# ---------------------------------------------------------------------------

def test_format_csirt_alert_contains_required_fields():
    msg = format_csirt_alert(
        ticket_id="TICKET-2026-0001",
        incident_type="Phishing",
        severity="Tinggi",
        reporter_name="Budi",
        timestamp="2026-04-04T10:00:00",
        description_short="Email phishing.",
        mitigation_short="Jangan klik link.",
    )
    assert "TICKET-2026-0001" in msg
    assert "Phishing" in msg
    assert "Tinggi" in msg
    assert "Budi" in msg
    assert "Email phishing." in msg
    assert "Jangan klik link." in msg


def test_format_csirt_alert_severity_emoji():
    for severity, emoji in SEVERITY_EMOJI.items():
        msg = format_csirt_alert(
            ticket_id="T-001", incident_type="Phishing", severity=severity,
            reporter_name="X", timestamp="2026-01-01", description_short="d", mitigation_short="m"
        )
        assert emoji in msg


def test_format_reporter_confirmation_contains_required_fields():
    msg = format_reporter_confirmation(
        ticket_id="TICKET-2026-0001",
        incident_type="Ransomware",
        severity="Kritis",
        confidence=0.95,
        mitigation_steps="1. Isolasi sistem.",
    )
    assert "TICKET-2026-0001" in msg
    assert "Ransomware" in msg
    assert "Kritis" in msg
    assert "95%" in msg
    assert "1. Isolasi sistem." in msg


def test_format_reporter_confirmation_confidence_rounded():
    msg = format_reporter_confirmation(
        ticket_id="T", incident_type="DDoS", severity="Sedang",
        confidence=0.876, mitigation_steps="Langkah mitigasi."
    )
    assert "88%" in msg


def test_format_csirt_alert_truncates_long_description():
    long_desc = "A" * 500
    msg = format_csirt_alert(
        ticket_id="T", incident_type="DDoS", severity="Sedang",
        reporter_name="X", timestamp="2026-01-01",
        description_short=long_desc, mitigation_short="m"
    )
    assert "A" * 300 in msg
    assert "A" * 301 not in msg


def test_format_reporter_confirmation_empty_mitigation():
    msg = format_reporter_confirmation(
        ticket_id="T", incident_type="DDoS", severity="Sedang",
        confidence=0.5, mitigation_steps=""
    )
    assert "CSIRT" in msg


# ---------------------------------------------------------------------------
# Severity routing tests
# ---------------------------------------------------------------------------

def test_severity_routing_kritis_includes_manager():
    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001", "CSIRT_MANAGER_CHAT_ID": "mgr_001"}):
        recipients = _get_csirt_recipients("Kritis")
    assert "csirt_001" in recipients
    assert "mgr_001" in recipients


def test_severity_routing_tinggi_includes_manager():
    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001", "CSIRT_MANAGER_CHAT_ID": "mgr_001"}):
        recipients = _get_csirt_recipients("Tinggi")
    assert "mgr_001" in recipients


def test_severity_routing_sedang_excludes_manager():
    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001", "CSIRT_MANAGER_CHAT_ID": "mgr_001"}):
        recipients = _get_csirt_recipients("Sedang")
    assert "csirt_001" in recipients
    assert "mgr_001" not in recipients


def test_severity_routing_rendah_excludes_manager():
    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001", "CSIRT_MANAGER_CHAT_ID": "mgr_001"}):
        recipients = _get_csirt_recipients("Rendah")
    assert "mgr_001" not in recipients


# ---------------------------------------------------------------------------
# NotifierAgent async tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_notifications_no_client_returns_sent_true():
    """Tanpa telegram_client (mode log), notification_sent harus True."""
    agent = NotifierAgent(telegram_client=None)
    result = await agent.send_notifications(_make_state())

    assert result["notification_sent"] is True
    assert "notification_timestamp" in result
    assert isinstance(result["notification_recipients"], list)


@pytest.mark.asyncio
async def test_send_notifications_with_telegram_calls_send_message():
    """Dengan telegram_client, send_message harus dipanggil untuk CSIRT dan pelapor."""
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    agent = NotifierAgent(telegram_client=mock_bot)

    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001", "CSIRT_MANAGER_CHAT_ID": ""}):
        result = await agent.send_notifications(_make_state())

    assert result["notification_sent"] is True
    # 1x CSIRT + 1x pelapor (reporter_id="user_123")
    assert mock_bot.send_message.call_count >= 2


@pytest.mark.asyncio
async def test_send_notifications_telegram_error_returns_sent_false():
    """Jika Telegram error, notification_sent False — pipeline tidak crash."""
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(side_effect=Exception("Network error"))
    agent = NotifierAgent(telegram_client=mock_bot)

    with patch.dict("os.environ", {"CSIRT_CHAT_ID": "csirt_001"}):
        result = await agent.send_notifications(_make_state())

    assert result["notification_sent"] is False
    assert "notification_timestamp" in result


@pytest.mark.asyncio
async def test_format_csirt_notification_uses_state():
    """_format_csirt_notification harus mengisi field dari state."""
    agent = NotifierAgent()
    state = _make_state(ticket_id="TICKET-2026-0042", incident_type="Ransomware", severity="Kritis")
    msg = agent._format_csirt_notification(state)

    assert "TICKET-2026-0042" in msg
    assert "Ransomware" in msg
    assert "Kritis" in msg


@pytest.mark.asyncio
async def test_format_reporter_confirmation_uses_state():
    """_format_reporter_confirmation harus mengisi field dari state."""
    agent = NotifierAgent()
    state = _make_state(ticket_id="TICKET-2026-0099", confidence_score=0.88)
    msg = agent._format_reporter_confirmation(state)

    assert "TICKET-2026-0099" in msg
    assert "88%" in msg


@pytest.mark.asyncio
async def test_result_keys_always_present():
    """Semua key wajib harus ada di semua kondisi."""
    agent = NotifierAgent(telegram_client=None)
    result = await agent.send_notifications(_make_state())

    required = {"notification_sent", "notification_recipients", "notification_timestamp"}
    assert required.issubset(result.keys())
