"""Unit tests for TicketManagerAgent."""
from unittest.mock import MagicMock

import pytest

from app.agents.ticket_manager import TicketManagerAgent, ESCALATION_MAP, REQUIRED_FIELDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> dict:
    base = {
        "raw_input": "Email phishing dari CEO palsu.",
        "sanitized_input": "Email phishing dari CEO palsu.",
        "reporter_id": "user_123",
        "reporter_name": "Budi Santoso",
        "reporter_contact": "@budi",
        "incident_type": "Phishing",
        "severity": "Tinggi",
        "confidence_score": 0.92,
        "mitigation_recommendation": "Jangan klik link. Laporkan ke IT.",
        "citations": [{"source": "NIST SP 800-61"}],
        "rag_confidence": 0.85,
        "classification_reasoning": "Ciri-ciri phishing jelas.",
        "agent_trace": [],
    }
    base.update(overrides)
    return base


def _make_mock_ticket(ticket_id: str = "TICKET-2026-0001", status: str = "PENDING_REVIEW", escalation: str = "Mendesak"):
    ticket = MagicMock()
    ticket.ticket_id = ticket_id
    ticket.status = status
    ticket.escalation_level = escalation
    return ticket


def _make_repo(ticket=None, duplicate=None):
    repo = MagicMock()
    repo.check_duplicate.return_value = duplicate
    repo.create_ticket.return_value = ticket or _make_mock_ticket()
    return repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_ticket_success():
    """Happy path — tiket dibuat dan key wajib ada di hasil."""
    agent = TicketManagerAgent(_make_repo())
    result = await agent.create_ticket(_make_state())

    assert result["ticket_id"] == "TICKET-2026-0001"
    assert result["ticket_status"] == "PENDING_REVIEW"
    assert result["escalation_level"] == "Mendesak"
    assert result.get("is_duplicate") is False


@pytest.mark.asyncio
async def test_escalation_level_mapping():
    """Setiap nilai severity harus menghasilkan escalation_level yang benar."""
    expected = {
        "Kritis": "Segera",
        "Tinggi": "Mendesak",
        "Sedang": "Standar",
        "Rendah": "Rutin",
        "Informasional": "Rutin",
    }
    for severity, expected_level in expected.items():
        mock_ticket = _make_mock_ticket(escalation=expected_level)
        repo = _make_repo(ticket=mock_ticket)
        agent = TicketManagerAgent(repo)
        result = await agent.create_ticket(_make_state(severity=severity))
        assert result["escalation_level"] == expected_level, f"severity={severity}"


@pytest.mark.asyncio
async def test_duplicate_detection():
    """Jika check_duplicate mengembalikan tiket, kembalikan data tiket duplikat."""
    existing = _make_mock_ticket(ticket_id="TICKET-2026-0001", status="PENDING_REVIEW", escalation="Mendesak")
    repo = _make_repo(duplicate=existing)
    agent = TicketManagerAgent(repo)

    result = await agent.create_ticket(_make_state())

    assert result["ticket_id"] == "TICKET-2026-0001"
    assert result["is_duplicate"] is True
    repo.create_ticket.assert_not_called()


@pytest.mark.asyncio
async def test_missing_required_fields():
    """Jika field wajib tidak ada, kembalikan dict error — tidak raise."""
    agent = TicketManagerAgent(_make_repo())
    state = _make_state()
    del state["reporter_id"]

    result = await agent.create_ticket(state)

    assert result["ticket_status"] == "ERROR"
    assert result["ticket_id"] == ""
    assert "reporter_id" in result["error"]


@pytest.mark.asyncio
async def test_missing_multiple_required_fields():
    """Beberapa field wajib hilang — semua disebutkan di pesan error."""
    agent = TicketManagerAgent(_make_repo())
    state = _make_state()
    del state["reporter_id"]
    del state["incident_type"]

    result = await agent.create_ticket(state)

    assert result["ticket_status"] == "ERROR"
    assert "reporter_id" in result["error"]
    assert "incident_type" in result["error"]


@pytest.mark.asyncio
async def test_db_error_returns_error_dict():
    """Jika create_ticket di repo raise exception, kembalikan dict error — tidak crash."""
    repo = _make_repo()
    repo.create_ticket.side_effect = RuntimeError("DB connection lost")
    agent = TicketManagerAgent(repo)

    result = await agent.create_ticket(_make_state())

    assert result["ticket_status"] == "ERROR"
    assert result["ticket_id"] == ""
    assert "RuntimeError" in result["error"]


@pytest.mark.asyncio
async def test_duplicate_check_error_proceeds_to_create():
    """Jika check_duplicate raise exception, lanjut buat tiket baru."""
    repo = _make_repo()
    repo.check_duplicate.side_effect = Exception("Redis timeout")
    agent = TicketManagerAgent(repo)

    result = await agent.create_ticket(_make_state())

    assert result["ticket_id"] == "TICKET-2026-0001"
    repo.create_ticket.assert_called_once()


@pytest.mark.asyncio
async def test_result_always_has_required_keys():
    """Semua key wajib ada di hasil, bahkan saat error."""
    agent = TicketManagerAgent(_make_repo())
    required = {"ticket_id", "ticket_status", "escalation_level"}

    # Success case
    r = await agent.create_ticket(_make_state())
    assert required.issubset(r.keys())

    # Error case
    r = await agent.create_ticket(_make_state(reporter_id=""))
    assert required.issubset(r.keys())


def test_escalation_map_covers_all_severities():
    """ESCALATION_MAP harus mencakup semua 5 severity yang valid."""
    valid_severities = {"Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"}
    assert valid_severities == set(ESCALATION_MAP.keys())
