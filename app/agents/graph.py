"""LangGraph helpdesk pipeline — menyatukan semua agen dalam satu graf."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.state import IncidentState
from app.security.guardrails import run_input_guardrails
from app.security.validator import OutputValidator

_output_validator = OutputValidator()

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
# Security node functions (stateless — no injected agents needed)
# ---------------------------------------------------------------------------

async def guardrails_node(state: IncidentState) -> IncidentState:
    """Node 1: sanitasi input + deteksi injeksi + redaksi PII."""
    try:
        result = await asyncio.to_thread(run_input_guardrails, state["raw_input"])
        if result.blocked:
            _error(state, result.block_reason)
            # Tandai sebagai needs_clarification agar pipeline berhenti
            state["intent"] = "needs_clarification"
            state["requires_clarification"] = True
            state["clarification_message"] = (
                "Input Anda tidak dapat diproses karena terdeteksi konten yang tidak diizinkan. "
                "Silakan ulangi dengan menjelaskan insiden keamanan siber secara langsung."
            )
            _trace(state, "guardrails", "blocked", reason=result.block_reason)
        else:
            state["sanitized_input"] = result.sanitized_input
            _trace(state, "guardrails", "success", pii_redacted=len(result.pii_mapping))
    except Exception as exc:
        logger.exception("Guardrails node error: %s", exc)
        _error(state, f"Guardrails error: {type(exc).__name__}")
        # Fail-closed: blokir jika guardrails sendiri crash
        state["intent"] = "needs_clarification"
        state["requires_clarification"] = True
        state["clarification_message"] = "Terjadi kesalahan saat memproses input. Silakan coba lagi."
        _trace(state, "guardrails", "fallback")
    return state


def make_validate_output_node():
    """Node antara mitigation dan ticket: validasi output LLM."""
    async def validate_output_node(state: IncidentState) -> IncidentState:
        try:
            validation = _output_validator.validate(
                output=state.get("mitigation_recommendation", ""),
                retrieved_chunks=state.get("retrieved_chunks", []),
            )
            if not validation["is_valid"]:
                logger.warning("Output LLM tidak lolos validasi: %s", validation["issues"])
                for issue in validation["issues"]:
                    _error(state, f"Output validation: {issue}")
                # Jika ada isu PII — hapus output
                if any("PII" in i for i in validation["issues"]):
                    state["mitigation_recommendation"] = (
                        "Rekomendasi tidak dapat ditampilkan karena terdeteksi data sensitif. "
                        "Silakan hubungi Tim Keamanan Siber dan PDP secara langsung."
                    )
            _trace(state, "output_validator", "success" if validation["is_valid"] else "issues_found",
                   issues=validation["issues"])
        except Exception as exc:
            logger.exception("Output validator node error: %s", exc)
            _error(state, f"Output validator error: {type(exc).__name__}")
            _trace(state, "output_validator", "fallback")
        return state
    return validate_output_node


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
            # Gunakan general_help agar tidak memicu guard existing_ticket
            # saat terjadi error tak terduga di orchestrator
            state["intent"] = "general_help"
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
                "Silakan hubungi Tim Keamanan Siber dan PDP secara langsung."
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


def make_general_help_node(orchestrator):
    async def general_help_node(state: IncidentState) -> IncidentState:
        try:
            response = await orchestrator.generate_help_response(state["sanitized_input"])
            state["mitigation_recommendation"] = response
            _trace(state, "general_help", "success")
        except Exception as exc:
            logger.exception("General help node error: %s", exc)
            state["mitigation_recommendation"] = (
                "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini. "
                "Silakan hubungi Tim Keamanan Siber dan PDP untuk bantuan lebih lanjut."
            )
            _trace(state, "general_help", "fallback")
        return state
    return general_help_node


def make_knowledge_node(mitigation_advisor):
    async def knowledge_node(state: IncidentState) -> IncidentState:
        try:
            result = await mitigation_advisor.generate_knowledge_response(
                sanitized_input=state["sanitized_input"],
                source_preference=None,
            )
            state["mitigation_recommendation"] = result.get("mitigation_recommendation", "")
            state["citations"] = result.get("citations", [])
            state["retrieved_chunks"] = result.get("retrieved_chunks", [])
            state["rag_confidence"] = result.get("rag_confidence", 0.0)
            _trace(state, "knowledge_advisor", "success",
                   rag_confidence=result.get("rag_confidence", 0.0))
        except Exception as exc:
            logger.exception("Knowledge node error: %s", exc)
            state["mitigation_recommendation"] = (
                "Sistem tidak dapat menemukan jawaban dari dokumen referensi. "
                "Silakan hubungi Tim Keamanan Siber dan PDP Pusdatin Kementan untuk bantuan lebih lanjut."
            )
            _trace(state, "knowledge_advisor", "fallback")
        return state
    return knowledge_node


async def existing_ticket_node(state: IncidentState) -> IncidentState:
    """Node: sesi sudah punya tiket & pesan ini upaya melapor lagi — jangan buat tiket baru."""
    state["ticket_id"] = state.get("session_existing_ticket", "")
    state["ticket_status"] = "EXISTING"
    _trace(state, "ticket_manager", "existing_session_ticket", ticket_id=state["ticket_id"])
    return state


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
    rounds = state.get("clarification_rounds", 0)

    # Sesi sudah punya tiket & pesan ini upaya melapor insiden lagi → jangan
    # jalankan pipeline pembuatan tiket baru, cukup rujuk ke tiket yang ada.
    if intent == "report_incident" and state.get("session_existing_ticket"):
        return "existing_ticket"

    # Hard limit: setelah 1 ronde klarifikasi, langsung proses — jangan tanya lagi
    if rounds >= 1 and intent == "report_incident":
        return "report_incident"

    # report_incident dengan info kurang → minta klarifikasi (hanya ronde pertama)
    if intent == "report_incident" and state.get("requires_clarification"):
        return "needs_clarification"
    if intent == "report_incident":
        return "report_incident"
    if intent == "needs_clarification":
        return "needs_clarification"
    if intent == "query_knowledge":
        return "query_knowledge"
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
    """Build dan compile LangGraph helpdesk pipeline dengan lapisan keamanan.

    Alur lengkap:
      guardrails (sanitize + injection check + PII redact)
        ├─ blocked → END
        └─ ok → classify_intent
                  ├─ report_incident (sesi belum punya tiket)
                  │        → identify_incident → generate_mitigation
                  │        → validate_output → create_ticket
                  │        → send_notification → END
                  ├─ report_incident (sesi sudah punya tiket)
                  │        → existing_ticket → END
                  ├─ query_knowledge  → query_knowledge → END
                  ├─ needs_clarification → END
                  ├─ query_status        → general_help → END
                  └─ general_help        → general_help → END
    """
    graph = StateGraph(IncidentState)

    # Tambahkan node
    graph.add_node("guardrails", guardrails_node)
    graph.add_node("classify_intent", make_orchestrator_node(orchestrator))
    graph.add_node("general_help", make_general_help_node(orchestrator))
    graph.add_node("query_knowledge", make_knowledge_node(mitigation_advisor))
    graph.add_node("identify_incident", make_identifier_node(identifier))
    graph.add_node("generate_mitigation", make_mitigation_node(mitigation_advisor))
    graph.add_node("validate_output", make_validate_output_node())
    graph.add_node("create_ticket", make_ticket_node(ticket_manager))
    graph.add_node("send_notification", make_notifier_node(notifier))
    graph.add_node("existing_ticket", existing_ticket_node)

    # Entry point: guardrails dulu
    graph.set_entry_point("guardrails")

    # Setelah guardrails: lanjut atau berhenti
    graph.add_conditional_edges(
        "guardrails",
        lambda s: "blocked" if s.get("requires_clarification") else "ok",
        {
            "blocked": END,
            "ok": "classify_intent",
        },
    )

    # Routing kondisional dari orchestrator
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "report_incident":     "identify_incident",
            "query_knowledge":     "query_knowledge",
            "needs_clarification": END,
            "query_status":        "general_help",
            "general_help":        "general_help",
            "existing_ticket":     "existing_ticket",
        },
    )

    graph.add_edge("general_help", END)
    graph.add_edge("query_knowledge", END)
    graph.add_edge("existing_ticket", END)

    # Pipeline insiden (dengan validate_output setelah mitigation)
    graph.add_edge("identify_incident", "generate_mitigation")
    graph.add_edge("generate_mitigation", "validate_output")
    graph.add_edge("validate_output", "create_ticket")
    graph.add_edge("create_ticket", "send_notification")
    graph.add_edge("send_notification", END)

    return graph.compile()
