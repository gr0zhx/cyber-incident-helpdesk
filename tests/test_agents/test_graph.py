"""End-to-end pipeline tests for LangGraph helpdesk graph."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.graph import build_helpdesk_graph, route_by_intent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import IncidentState


# ---------------------------------------------------------------------------
# Mock factory helpers
# ---------------------------------------------------------------------------

def _llm_mock(response: dict):
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(response)
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create = AsyncMock(return_value=completion)
    return client


def _make_orchestrator(intent: str = "report_incident", confidence: float = 0.95):
    return OrchestratorAgent(
        llm_client=_llm_mock({
            "intent": intent,
            "confidence": confidence,
            "needs_clarification": intent == "needs_clarification",
            "clarification_message": "Mohon jelaskan." if intent == "needs_clarification" else "",
        })
    )


def _make_identifier(incident_type: str = "Phishing", severity: str = "Tinggi", confidence: float = 0.92):
    from app.agents.identifier import IncidentIdentifierAgent
    return IncidentIdentifierAgent(
        llm_client=_llm_mock({
            "incident_type": incident_type,
            "severity": severity,
            "confidence_score": confidence,
            "reasoning": "Terdeteksi pola phishing.",
        })
    )


def _make_mitigation_advisor(recommendation: str = "1. Jangan klik link. [NIST SP 800-61]"):
    from app.agents.mitigation import MitigationAdvisorAgent
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {"id": "1", "content": "Panduan NIST.", "metadata": {"source": "NIST SP 800-61", "section": "Bagian 3"},
         "final_score": 0.7, "rrf_score": 0.7}
    ]
    reranker_fn = lambda q, chunks, top_k=5, incident_type=None: chunks[:top_k]
    return MitigationAdvisorAgent(
        llm_client=_llm_mock({
            "mitigation_steps": [{"step": 1, "action": recommendation, "source": "NIST SP 800-61"}],
            "general_guidance": "Segera laporkan.",
            "escalation_note": "",
        }),
        retriever=retriever,
        reranker_fn=reranker_fn,
    )


def _make_ticket_manager():
    from app.agents.ticket_manager import TicketManagerAgent
    mock_ticket = MagicMock()
    mock_ticket.ticket_id = "TICKET-2026-0001"
    mock_ticket.status = "PENDING_REVIEW"
    mock_ticket.escalation_level = "Mendesak"
    repo = MagicMock()
    repo.check_duplicate.return_value = None
    repo.create_ticket.return_value = mock_ticket
    return TicketManagerAgent(ticket_repository=repo)


def _make_notifier():
    from app.agents.notifier import NotifierAgent
    return NotifierAgent(telegram_client=None)


def _make_initial_state(raw_input: str = "Email phishing dari CEO palsu.") -> IncidentState:
    orch = _make_orchestrator()
    return orch.initialize_state(
        raw_input=raw_input,
        reporter_id="user_001",
        reporter_name="Budi",
        reporter_contact="@budi",
        session_id="sess_test",
    )


# ---------------------------------------------------------------------------
# route_by_intent tests
# ---------------------------------------------------------------------------

def test_route_report_incident():
    state = _make_initial_state()
    state["intent"] = "report_incident"
    assert route_by_intent(state) == "report_incident"


def test_route_needs_clarification():
    state = _make_initial_state()
    state["intent"] = "needs_clarification"
    assert route_by_intent(state) == "needs_clarification"


def test_route_query_status():
    state = _make_initial_state()
    state["intent"] = "query_status"
    assert route_by_intent(state) == "query_status"


def test_route_general_help():
    state = _make_initial_state()
    state["intent"] = "general_help"
    assert route_by_intent(state) == "general_help"


def test_route_unknown_falls_back_to_general_help():
    state = _make_initial_state()
    state["intent"] = "unknown"
    assert route_by_intent(state) == "general_help"


# ---------------------------------------------------------------------------
# Full pipeline end-to-end tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_report_incident_full_flow():
    """Skenario 1: laporan phishing → semua agen dijalankan → IncidentState lengkap."""
    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("report_incident"),
        identifier=_make_identifier("Phishing", "Tinggi"),
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Saya klik link phishing dari CEO palsu.")
    result = await graph.ainvoke(state)

    # Intent
    assert result["intent"] == "report_incident"

    # Identifier
    assert result["incident_type"] == "Phishing"
    assert result["severity"] == "Tinggi"
    assert result["confidence_score"] > 0.0

    # Mitigation
    assert result["mitigation_recommendation"] != ""

    # Ticket
    assert result["ticket_id"] == "TICKET-2026-0001"
    assert result["ticket_status"] == "PENDING_REVIEW"
    assert result["escalation_level"] == "Mendesak"

    # Notifier
    assert result["notification_sent"] is True

    # Trace: semua 7 node harus ada
    agents_traced = {t["agent"] for t in result["agent_trace"]}
    assert agents_traced == {"guardrails", "orchestrator", "identifier", "mitigation_advisor", "output_validator", "ticket_manager", "notifier"}

    # Tidak ada error
    assert result["processing_errors"] == []


@pytest.mark.asyncio
async def test_pipeline_needs_clarification_stops_at_orchestrator():
    """Skenario 2: pesan ambigu → intent=needs_clarification → berhenti setelah orchestrator."""
    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("needs_clarification", 0.4),
        identifier=_make_identifier(),
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Ada yang aneh.")
    result = await graph.ainvoke(state)

    assert result["intent"] == "needs_clarification"
    assert result["requires_clarification"] is True
    assert result["clarification_message"] != ""

    # Agen berikutnya TIDAK boleh dijalankan
    agents_traced = {t["agent"] for t in result["agent_trace"]}
    assert "identifier" not in agents_traced
    assert "ticket_manager" not in agents_traced

    # Tiket tidak dibuat
    assert result["ticket_id"] == ""


@pytest.mark.asyncio
async def test_pipeline_query_status_stops_at_orchestrator():
    """Skenario 3: query status → berhenti setelah orchestrator."""
    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("query_status"),
        identifier=_make_identifier(),
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Status tiket TICKET-2026-0042?")
    result = await graph.ainvoke(state)

    assert result["intent"] == "query_status"
    agents_traced = {t["agent"] for t in result["agent_trace"]}
    assert "identifier" not in agents_traced
    assert result["ticket_id"] == ""


@pytest.mark.asyncio
async def test_pipeline_identifier_error_fallback():
    """Skenario 4: identifier gagal → fallback Lainnya/Sedang → pipeline tetap lanjut."""
    from openai import APITimeoutError
    from app.agents.identifier import IncidentIdentifierAgent

    identifier_timeout = IncidentIdentifierAgent(
        llm_client=MagicMock(
            chat=MagicMock(
                completions=MagicMock(
                    create=AsyncMock(side_effect=APITimeoutError(request=MagicMock()))
                )
            )
        )
    )

    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("report_incident"),
        identifier=identifier_timeout,
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Email mencurigakan.")
    result = await graph.ainvoke(state)

    # Identifier fallback
    assert result["incident_type"] == "Lainnya"
    assert result["severity"] == "Sedang"

    # Pipeline tetap lanjut ke ticket
    assert result["ticket_id"] == "TICKET-2026-0001"
    assert result["notification_sent"] is True


@pytest.mark.asyncio
async def test_pipeline_agent_trace_populated():
    """agent_trace harus terisi dengan entry untuk setiap agen yang dijalankan."""
    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("report_incident"),
        identifier=_make_identifier(),
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Ransomware terdeteksi.")
    result = await graph.ainvoke(state)

    assert len(result["agent_trace"]) == 7  # guardrails + orchestrator + identifier + mitigation + output_validator + ticket + notifier
    for entry in result["agent_trace"]:
        assert "agent" in entry
        assert "timestamp" in entry
        assert "status" in entry


@pytest.mark.asyncio
async def test_pipeline_processing_errors_empty_on_success():
    graph = build_helpdesk_graph(
        orchestrator=_make_orchestrator("report_incident"),
        identifier=_make_identifier(),
        mitigation_advisor=_make_mitigation_advisor(),
        ticket_manager=_make_ticket_manager(),
        notifier=_make_notifier(),
    )
    state = _make_initial_state("Akses tidak sah terdeteksi.")
    result = await graph.ainvoke(state)

    assert result["processing_errors"] == []
