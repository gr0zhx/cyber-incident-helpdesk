import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import fakeredis
import pytest

from app.web.services.chat_service import ChatMessage, ChatService

PENDING_META = {
    "original_filename": "a.pdf",
    "stored_path": "/tmp/a.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 100,
}


def _make_graph(requires_clarification=False, ticket_id="", clarification_msg=""):
    state = {
        "requires_clarification": requires_clarification,
        "clarification_message": clarification_msg,
        "ticket_id": ticket_id,
        "mitigation_recommendation": "Segera isolasi host.",
        "incident_type": "PHISHING",
        "severity": "HIGH",
        "escalation_level": "MEDIUM",
        "confidence_score": 0.9,
    }
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=state)
    return graph


def _make_orchestrator():
    from app.agents.state import IncidentState
    orch = MagicMock()
    orch.initialize_state.return_value = IncidentState(
        raw_input="x", sanitized_input="x", reporter_id="web:abc",
        reporter_name="Test", reporter_contact="", session_id="sess-1",
        timestamp_received="", intent="", requires_clarification=False,
        clarification_message="", incident_type="", severity="",
        confidence_score=0.0, classification_reasoning="",
        retrieved_chunks=[], mitigation_recommendation="", citations=[],
        rag_confidence=0.0, ticket_id="", ticket_status="",
        escalation_level="", notification_sent=False,
        notification_recipients=[], notification_timestamp="",
        processing_errors=[], agent_trace=[],
    )
    return orch


def _make_service(redis=None):
    if redis is None:
        redis = fakeredis.FakeStrictRedis(decode_responses=False)
    return ChatService(redis=redis)


def test_get_history_empty(tmp_path):
    svc = _make_service()
    assert svc.get_history("new-session") == []


def test_get_history_returns_stored(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    msgs = [{"role": "user", "content": "halo", "ts": "2026-01-01"}]
    r.setex("web:chat:sess-1", 86400, json.dumps(msgs).encode())
    svc = _make_service(r)
    assert svc.get_history("sess-1") == msgs


def test_handle_message_clarification(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    graph = _make_graph(requires_clarification=True, clarification_msg="Apa unit Anda?")
    orch = _make_orchestrator()
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="email aneh", graph=graph, orchestrator=orch,
    ))
    assert result["requires_clarification"] is True
    assert result["bot_text"] == "Apa unit Anda?"
    assert result["ticket_id"] is None
    history = svc.get_history("sess-1")
    assert len(history) == 2  # user + assistant


def test_handle_message_ticket_created(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    # seed pending upload
    r.setex("web:pending_uploads:sess-1", 3600, json.dumps([PENDING_META]).encode())
    graph = _make_graph(ticket_id="INC-99")
    orch = _make_orchestrator()

    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="laptop terinfeksi", graph=graph, orchestrator=orch,
        db=db,
    ))
    assert result["ticket_id"] == "INC-99"
    assert result["requires_clarification"] is False
    # pending upload flushed
    assert r.get("web:pending_uploads:sess-1") is None
    # TicketAttachment inserted
    db.add.assert_called_once()


def test_handle_message_timeout_returns_fallback_message(tmp_path):
    import asyncio as _asyncio
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    orch = _make_orchestrator()

    async def _slow(state):
        await _asyncio.sleep(60)
        return {}

    graph = MagicMock()
    graph.ainvoke = _slow
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="test", graph=graph, orchestrator=orch,
        timeout=0.01,
    ))
    assert result["error"] is False
    assert "sistem sedang sibuk" in result["bot_text"].lower()


def test_clear_history(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    r.setex("web:chat:sess-1", 86400, b"[{}]")
    svc = _make_service(r)
    svc.clear_history("sess-1")
    assert svc.get_history("sess-1") == []
