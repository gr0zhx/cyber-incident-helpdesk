"""Unit tests for OrchestratorAgent."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.orchestrator import (
    OrchestratorAgent,
    _parse_llm_response,
    _validate_intent,
    VALID_INTENTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(llm_response: dict | None = None, side_effect=None) -> OrchestratorAgent:
    mock_client = MagicMock()
    if side_effect is not None:
        mock_client.chat.completions.create = AsyncMock(side_effect=side_effect)
    else:
        content = json.dumps(llm_response) if llm_response else ""
        choice = MagicMock()
        choice.message.content = content
        completion = MagicMock()
        completion.choices = [choice]
        mock_client.chat.completions.create = AsyncMock(return_value=completion)
    return OrchestratorAgent(llm_client=mock_client, model="gpt-4o")


def _intent_response(intent: str, confidence: float = 0.95, needs_clarification: bool = False, msg: str = "") -> dict:
    return {
        "intent": intent,
        "confidence": confidence,
        "needs_clarification": needs_clarification,
        "clarification_message": msg,
    }


# ---------------------------------------------------------------------------
# Pure helper tests
# ---------------------------------------------------------------------------

def test_parse_llm_response_valid_json():
    raw = json.dumps({"intent": "report_incident", "confidence": 0.9, "needs_clarification": False, "clarification_message": ""})
    assert _parse_llm_response(raw) is not None


def test_parse_llm_response_embedded():
    payload = {"intent": "general_help", "confidence": 0.8, "needs_clarification": False, "clarification_message": ""}
    raw = f"Berikut:\n{json.dumps(payload)}\nSelesai."
    result = _parse_llm_response(raw)
    assert result is not None
    assert result["intent"] == "general_help"


def test_parse_llm_response_invalid_returns_none():
    assert _parse_llm_response("bukan json") is None
    assert _parse_llm_response("") is None


def test_validate_intent_valid():
    result = _validate_intent({"intent": "report_incident", "confidence": 0.95, "needs_clarification": False, "clarification_message": ""})
    assert result["intent"] == "report_incident"
    assert result["confidence"] == 0.95
    assert result["needs_clarification"] is False


def test_validate_intent_unknown_falls_back():
    result = _validate_intent({"intent": "unknown_intent", "confidence": 0.9})
    assert result["intent"] == "report_incident"


def test_validate_intent_clamps_confidence():
    r1 = _validate_intent({"intent": "general_help", "confidence": 2.5})
    assert r1["confidence"] == 1.0
    r2 = _validate_intent({"intent": "general_help", "confidence": -0.5})
    assert r2["confidence"] == 0.0


def test_validate_intent_needs_clarification_only_for_correct_intent():
    """needs_clarification True hanya valid jika intent adalah needs_clarification."""
    result = _validate_intent({
        "intent": "general_help",
        "confidence": 0.9,
        "needs_clarification": True,
        "clarification_message": "Tolong jelaskan."
    })
    assert result["needs_clarification"] is False
    assert result["clarification_message"] == ""


def test_validate_intent_clarification_preserved_when_correct():
    result = _validate_intent({
        "intent": "needs_clarification",
        "confidence": 0.4,
        "needs_clarification": True,
        "clarification_message": "Mohon jelaskan lebih detail.",
    })
    assert result["needs_clarification"] is True
    assert result["clarification_message"] == "Mohon jelaskan lebih detail."


def test_valid_intents_set():
    assert "report_incident" in VALID_INTENTS
    assert "query_status" in VALID_INTENTS
    assert "general_help" in VALID_INTENTS
    assert "needs_clarification" in VALID_INTENTS


# ---------------------------------------------------------------------------
# OrchestratorAgent.classify_intent async tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classify_intent_report_incident():
    agent = _make_agent(_intent_response("report_incident", 0.97))
    result = await agent.classify_intent("Saya klik link phishing dari CEO palsu.")
    assert result["intent"] == "report_incident"
    assert result["confidence"] > 0.5


@pytest.mark.asyncio
async def test_classify_intent_query_status():
    agent = _make_agent(_intent_response("query_status", 0.96))
    result = await agent.classify_intent("Status tiket TICKET-2026-0042?")
    assert result["intent"] == "query_status"


@pytest.mark.asyncio
async def test_classify_intent_general_help():
    agent = _make_agent(_intent_response("general_help", 0.93))
    result = await agent.classify_intent("Apa itu ransomware?")
    assert result["intent"] == "general_help"


@pytest.mark.asyncio
async def test_classify_intent_needs_clarification():
    agent = _make_agent(_intent_response(
        "needs_clarification", 0.40,
        needs_clarification=True,
        msg="Mohon ceritakan lebih detail."
    ))
    result = await agent.classify_intent("Ada yang aneh.")
    assert result["intent"] == "needs_clarification"
    assert result["needs_clarification"] is True
    assert result["clarification_message"] != ""


@pytest.mark.asyncio
async def test_classify_intent_invalid_json_returns_fallback():
    agent = _make_agent()
    choice = MagicMock()
    choice.message.content = "bukan json sama sekali"
    completion = MagicMock()
    completion.choices = [choice]
    agent.llm.chat.completions.create = AsyncMock(return_value=completion)

    result = await agent.classify_intent("test")
    assert result["intent"] == "report_incident"


@pytest.mark.asyncio
async def test_classify_intent_timeout_returns_fallback():
    from openai import APITimeoutError
    agent = _make_agent(side_effect=APITimeoutError(request=MagicMock()))
    result = await agent.classify_intent("test")
    assert result["intent"] == "report_incident"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_classify_intent_result_keys_complete():
    agent = _make_agent(_intent_response("general_help"))
    result = await agent.classify_intent("Apa itu phishing?")
    required = {"intent", "confidence", "needs_clarification", "clarification_message"}
    assert required.issubset(result.keys())


# ---------------------------------------------------------------------------
# OrchestratorAgent.initialize_state tests
# ---------------------------------------------------------------------------

def test_initialize_state_basic_fields():
    agent = _make_agent(_intent_response("report_incident"))
    state = agent.initialize_state(
        raw_input="Email phishing",
        reporter_id="user_001",
        reporter_name="Budi",
        reporter_contact="@budi",
        session_id="sess_abc",
    )
    assert state["raw_input"] == "Email phishing"
    assert state["sanitized_input"] == "Email phishing"
    assert state["reporter_id"] == "user_001"
    assert state["reporter_name"] == "Budi"
    assert state["session_id"] == "sess_abc"
    assert state["timestamp_received"] != ""
    assert state["processing_errors"] == []
    assert state["agent_trace"] == []


def test_initialize_state_all_keys_present():
    agent = _make_agent(_intent_response("report_incident"))
    state = agent.initialize_state(raw_input="test", reporter_id="u1")
    required = {
        "raw_input", "sanitized_input", "reporter_id", "reporter_name",
        "reporter_contact", "timestamp_received", "session_id",
        "intent", "requires_clarification", "clarification_message",
        "incident_type", "severity", "confidence_score", "classification_reasoning",
        "retrieved_chunks", "mitigation_recommendation", "citations", "rag_confidence",
        "ticket_id", "ticket_status", "escalation_level",
        "notification_sent", "notification_recipients", "notification_timestamp",
        "processing_errors", "agent_trace",
    }
    assert required.issubset(state.keys())


def test_initialize_state_defaults_are_empty():
    agent = _make_agent(_intent_response("report_incident"))
    state = agent.initialize_state(raw_input="test", reporter_id="u1")
    assert state["incident_type"] == ""
    assert state["ticket_id"] == ""
    assert state["notification_sent"] is False
    assert state["rag_confidence"] == 0.0
