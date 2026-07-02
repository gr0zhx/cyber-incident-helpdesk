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


def _make_orchestrator(classify_intent_result=None):
    from app.agents.state import IncidentState
    orch = MagicMock()
    orch.classify_intent = AsyncMock(
        return_value=classify_intent_result or {
            "intent": "report_incident", "confidence": 0.9,
            "needs_clarification": False, "clarification_message": "",
        }
    )
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
        processing_errors=[], agent_trace=[], clarification_rounds=0,
        session_existing_ticket="",
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


def test_handle_message_existing_ticket_blocks_new_report(tmp_path):
    """Repeat report_incident attempts in a session with a ticket already
    created should get the canned reply instead of a second ticket.

    Routing happens inside the graph (existing_ticket node), so classify_intent
    is only ever invoked once — chat_service just forwards session_existing_ticket
    into the state and reacts to the ticket_id the graph returns.
    """
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    r.setex("web:session_ticket:sess-1", 86400, b"INC-1")
    # Graph would route report_incident + session_existing_ticket to the
    # existing_ticket node, which echoes back the same ticket_id.
    graph = _make_graph(ticket_id="INC-1")
    orch = _make_orchestrator()
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="laptop saya kena ransomware lagi",
        graph=graph, orchestrator=orch,
    ))
    assert result["ticket_id"] == "INC-1"
    assert "sudah dibuat untuk sesi ini" in result["bot_text"]
    graph.ainvoke.assert_called_once()
    orch.classify_intent.assert_not_called()
    orch.initialize_state.assert_called_once()
    assert orch.initialize_state.call_args.kwargs["session_existing_ticket"] == "INC-1"


def test_handle_message_existing_ticket_allows_followup_question(tmp_path):
    """Follow-up questions (e.g. general_help) after a ticket exists should
    still reach the pipeline and produce a normal (non-canned) response."""
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    r.setex("web:session_ticket:sess-1", 86400, b"INC-1")
    # Graph classifies as general_help internally and never touches ticket_id.
    graph = _make_graph(ticket_id="")
    orch = _make_orchestrator()
    svc = _make_service(r)
    result = asyncio.run(svc.handle_message(
        session_id="sess-1", reporter_id="web:abc", reporter_name="X",
        reporter_contact="", text="halo saya ingin bertanya-tanya lagi",
        graph=graph, orchestrator=orch,
    ))
    graph.ainvoke.assert_called_once()
    orch.classify_intent.assert_not_called()
    assert "sudah dibuat untuk sesi ini" not in result["bot_text"]


def test_clear_history(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    r.setex("web:chat:sess-1", 86400, b"[{}]")
    svc = _make_service(r)
    svc.clear_history("sess-1")
    assert svc.get_history("sess-1") == []
