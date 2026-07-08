"""Unit tests for IncidentIdentifierAgent.

All tests mock the LLM client — no real API calls are made.
"""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.identifier import (
    VALID_SEVERITIES,
    VALID_TYPES,
    IncidentIdentifierAgent,
    _validate_and_normalize,
)
from app.utils.llm_parser import parse_llm_json as _parse_llm_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(response_json: dict | None = None, side_effect=None) -> IncidentIdentifierAgent:
    """Build an IncidentIdentifierAgent with a mocked AsyncOpenAI client."""
    mock_client = MagicMock()

    if side_effect is not None:
        mock_client.chat.completions.create = AsyncMock(side_effect=side_effect)
    else:
        content = json.dumps(response_json) if response_json is not None else ""
        choice = MagicMock()
        choice.message.content = content
        completion = MagicMock()
        completion.choices = [choice]
        mock_client.chat.completions.create = AsyncMock(return_value=completion)

    return IncidentIdentifierAgent(llm_client=mock_client, model="gpt-4o")


# ---------------------------------------------------------------------------
# Unit tests — pure helper functions (no async)
# ---------------------------------------------------------------------------

def test_parse_llm_response_valid_json():
    raw = '{"incident_type": "Phishing", "severity": "Tinggi", "confidence_score": 0.9, "reasoning": "test"}'
    result = _parse_llm_response(raw)
    assert result is not None
    assert result["incident_type"] == "Phishing"


def test_parse_llm_response_json_embedded_in_text():
    raw = 'Sure! Here is the result:\n{"incident_type": "Malware", "severity": "Sedang", "confidence_score": 0.8, "reasoning": "ok"}\nDone.'
    result = _parse_llm_response(raw)
    assert result is not None
    assert result["incident_type"] == "Malware"


def test_parse_llm_response_invalid_returns_none():
    assert _parse_llm_response("bukan json sama sekali") is None
    assert _parse_llm_response("") is None


def test_validate_unknown_incident_type_falls_back_to_lainnya():
    parsed = {
        "incident_type": "SQL Injection",  # not in VALID_TYPES
        "severity": "Tinggi",
        "confidence_score": 0.85,
        "reasoning": "test",
    }
    result = _validate_and_normalize(parsed)
    assert result["incident_type"] == "Lainnya"


def test_validate_unknown_severity_falls_back_to_sedang():
    parsed = {
        "incident_type": "Phishing",
        "severity": "Super Kritis",  # not in VALID_SEVERITIES
        "confidence_score": 0.85,
        "reasoning": "test",
    }
    result = _validate_and_normalize(parsed)
    assert result["severity"] == "Sedang"


def test_validate_low_confidence_sets_requires_review():
    parsed = {
        "incident_type": "Lainnya",
        "severity": "Rendah",
        "confidence_score": 0.55,
        "reasoning": "ambigu",
    }
    result = _validate_and_normalize(parsed)
    assert result["requires_review"] is True


def test_validate_high_confidence_no_review_required():
    parsed = {
        "incident_type": "Ransomware",
        "severity": "Kritis",
        "confidence_score": 0.95,
        "reasoning": "jelas ransomware",
    }
    result = _validate_and_normalize(parsed)
    assert result["requires_review"] is False


# ---------------------------------------------------------------------------
# Integration-style tests — async classify() with mocked LLM
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classify_phishing_report():
    agent = _make_agent({
        "incident_type": "Phishing",
        "severity": "Tinggi",
        "confidence_score": 0.95,
        "reasoning": "Email palsu yang meminta kredensial.",
    })
    result = await agent.classify("Saya menerima email dari CEO palsu meminta transfer dana.")
    assert result["incident_type"] == "Phishing"
    assert result["severity"] == "Tinggi"
    assert result["confidence_score"] >= 0.7
    assert result["requires_review"] is False


@pytest.mark.asyncio
async def test_classify_ransomware_report():
    agent = _make_agent({
        "incident_type": "Ransomware",
        "severity": "Kritis",
        "confidence_score": 0.98,
        "reasoning": "Enkripsi file dan permintaan tebusan.",
    })
    result = await agent.classify("Semua file saya ter-encrypt dan ada permintaan bayar Bitcoin.")
    assert result["incident_type"] == "Ransomware"
    assert result["severity"] == "Kritis"
    assert result["requires_review"] is False


@pytest.mark.asyncio
async def test_classify_ambiguous_report_low_confidence():
    agent = _make_agent({
        "incident_type": "Lainnya",
        "severity": "Rendah",
        "confidence_score": 0.45,
        "reasoning": "Laporan terlalu ambigu.",
    })
    result = await agent.classify("Ada yang aneh di komputer saya.")
    assert result["incident_type"] == "Lainnya"
    assert result["confidence_score"] < 0.7
    assert result["requires_review"] is True


@pytest.mark.asyncio
async def test_classify_invalid_llm_response_returns_fallback():
    """LLM returns non-JSON text → should return fallback, not raise."""
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Maaf, saya tidak mengerti pertanyaan Anda."
    completion = MagicMock()
    completion.choices = [choice]
    # Both attempts return the same bad response
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    agent = IncidentIdentifierAgent(llm_client=mock_client, model="gpt-4o")
    result = await agent.classify("input tidak penting")

    assert result["incident_type"] == "Lainnya"
    assert result["severity"] == "Sedang"
    assert result["confidence_score"] == 0.0
    assert result["requires_review"] is True


@pytest.mark.asyncio
async def test_classify_valid_types_enforced():
    """If LLM returns an out-of-list type, it should be normalised to 'Lainnya'."""
    agent = _make_agent({
        "incident_type": "Brute Force",  # not in VALID_TYPES
        "severity": "Tinggi",
        "confidence_score": 0.88,
        "reasoning": "Banyak percobaan login gagal.",
    })
    result = await agent.classify("Banyak percobaan login gagal dari satu IP.")
    assert result["incident_type"] == "Lainnya"


@pytest.mark.asyncio
async def test_classify_timeout_returns_fallback():
    from openai import APITimeoutError

    agent = _make_agent(side_effect=APITimeoutError(request=MagicMock()))
    result = await agent.classify("test input")

    assert result["incident_type"] == "Lainnya"
    assert result["requires_review"] is True
    assert "timeout" in result["reasoning"].lower()


@pytest.mark.asyncio
async def test_classify_result_keys_complete():
    """Result must always contain all required keys."""
    agent = _make_agent({
        "incident_type": "DDoS",
        "severity": "Kritis",
        "confidence_score": 0.91,
        "reasoning": "Traffic anomali sangat tinggi.",
    })
    result = await agent.classify("Website kami diserang dan tidak bisa diakses.")
    required_keys = {"incident_type", "severity", "confidence_score", "reasoning", "requires_review"}
    assert required_keys.issubset(result.keys())
