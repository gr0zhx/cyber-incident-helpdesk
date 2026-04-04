"""LangGraph helpdesk pipeline — menyatukan semua agen dalam satu graf."""
import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.state import IncidentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _trace(state: IncidentState, agent: str, status: str, **extra: Any) -> None:
    entry: dict = {
        "agent": agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }
    entry.update(extra)
    state["agent_trace"].append(entry)


def _error(state: IncidentState, msg: str) -> None:
    state["processing_errors"].append(msg)


# ---------------------------------------------------------------------------
# Node functions (closures over injected agents)
# ---------------------------------------------------------------------------

def make_orchestrator_node(orchestrator):
    async def orchestrator_node(state: IncidentState) -> IncidentState:
        try:
            result = await orchestrator.classify_intent(state["sanitized_input"])
            state["intent"] = result["intent"]
            state["requires_clarification"] = result["needs_clarification"]
            state["clarification_message"] = result.get("clarification_message", "")
            _trace(state, "orchestrator", "success", intent=result["intent"],
                   confidence=result["confidence"])
        except Exception as exc:
            logger.exception("Orchestrator node error: %s", exc)
            _error(state, f"Orchestrator error: {type(exc).__name__}")
            state["intent"] = "report_incident"
            state["requires_clarification"] = False
            _trace(state, "orchestrator", "fallback")
        return state
    return orchestrator_node


def make_identifier_node(identifier):
    async def identifier_node(state: IncidentState) -> IncidentState:
        try:
            result = await identifier.classify(state["sanitized_input"])
            state["incident_type"] = result["incident_type"]
            state["severity"] = result["severity"]
            state["confidence_score"] = result["confidence_score"]
            state["classification_reasoning"] = result.get("reasoning", "")
            _trace(state, "identifier", "success",
                   incident_type=result["incident_type"], severity=result["severity"])
        except Exception as exc:
            logger.exception("Identifier node error: %s", exc)
            _error(state, f"Identifier error: {type(exc).__name__}")
            state["incident_type"] = "Lainnya"
            state["severity"] = "Sedang"
            state["confidence_score"] = 0.0
            _trace(state, "identifier", "fallback")
        return state
    return identifier_node


def make_mitigation_node(mitigation_advisor):
    async def mitigation_node(state: IncidentState) -> IncidentState:
        try:
            result = await mitigation_advisor.generate_mitigation(
                sanitized_input=state["sanitized_input"],
                incident_type=state["incident_type"],
                severity=state["severity"],
            )
            state["mitigation_recommendation"] = result.get("mitigation_recommendation", "")
            state["citations"] = result.get("citations", [])
            state["retrieved_chunks"] = result.get("retrieved_chunks", [])
            state["rag_confidence"] = result.get("rag_confidence", 0.0)
            _trace(state, "mitigation_advisor", "success",
                   rag_confidence=result.get("rag_confidence", 0.0))
        except Exception as exc:
            logger.exception("Mitigation node error: %s", exc)
            _error(state, f"Mitigation error: {type(exc).__name__}")
            state["mitigation_recommendation"] = (
                "Sistem tidak dapat menghasilkan rekomendasi. "
                "Silakan hubungi tim CSIRT secara langsung."
            )
            _trace(state, "mitigation_advisor", "fallback")
        return state
    return mitigation_node


def make_ticket_node(ticket_manager):
    async def ticket_node(state: IncidentState) -> IncidentState:
        try:
            result = await ticket_manager.create_ticket(dict(state))
            state["ticket_id"] = result.get("ticket_id", "")
            state["ticket_status"] = result.get("ticket_status", "ERROR")
            state["escalation_level"] = result.get("escalation_level", "")
            _trace(state, "ticket_manager", "success",
                   ticket_id=result.get("ticket_id", ""),
                   is_duplicate=result.get("is_duplicate", False))
        except Exception as exc:
            logger.exception("Ticket node error: %s", exc)
            _error(state, f"Ticket error: {type(exc).__name__}")
            state["ticket_status"] = "ERROR"
            _trace(state, "ticket_manager", "fallback")
        return state
    return ticket_node


def make_notifier_node(notifier):
    async def notifier_node(state: IncidentState) -> IncidentState:
        try:
            result = await notifier.send_notifications(dict(state))
            state["notification_sent"] = result.get("notification_sent", False)
            state["notification_recipients"] = result.get("notification_recipients", [])
            state["notification_timestamp"] = result.get("notification_timestamp", "")
            _trace(state, "notifier", "success",
                   sent=result.get("notification_sent", False))
        except Exception as exc:
            logger.exception("Notifier node error: %s", exc)
            _error(state, f"Notifier error: {type(exc).__name__}")
            state["notification_sent"] = False
            _trace(state, "notifier", "fallback")
        return state
    return notifier_node


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_by_intent(state: IncidentState) -> str:
    intent = state.get("intent", "report_incident")
    if intent == "report_incident":
        return "report_incident"
    if intent == "needs_clarification":
        return "needs_clarification"
    if intent == "query_status":
        return "query_status"
    return "general_help"


# ---------------------------------------------------------------------------
# Graf builder
# ---------------------------------------------------------------------------

def build_helpdesk_graph(
    orchestrator,
    identifier,
    mitigation_advisor,
    ticket_manager,
    notifier,
):
    """Build dan compile LangGraph helpdesk pipeline.

    Alur:
      classify_intent
        ├─ report_incident → identify_incident → generate_mitigation
        │                                        → create_ticket → send_notification → END
        ├─ needs_clarification → END
        ├─ query_status        → END  (Fase 7+)
        └─ general_help        → END  (Fase 7+)
    """
    graph = StateGraph(IncidentState)

    # Tambahkan node
    graph.add_node("classify_intent", make_orchestrator_node(orchestrator))
    graph.add_node("identify_incident", make_identifier_node(identifier))
    graph.add_node("generate_mitigation", make_mitigation_node(mitigation_advisor))
    graph.add_node("create_ticket", make_ticket_node(ticket_manager))
    graph.add_node("send_notification", make_notifier_node(notifier))

    # Entry point
    graph.set_entry_point("classify_intent")

    # Routing kondisional dari orchestrator
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "report_incident":    "identify_incident",
            "needs_clarification": END,
            "query_status":        END,
            "general_help":        END,
        },
    )

    # Pipeline insiden
    graph.add_edge("identify_incident", "generate_mitigation")
    graph.add_edge("generate_mitigation", "create_ticket")
    graph.add_edge("create_ticket", "send_notification")
    graph.add_edge("send_notification", END)

    return graph.compile()
