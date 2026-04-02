from typing import TypedDict, Optional


class IncidentState(TypedDict):
    # Input
    raw_input: str
    sanitized_input: str
    reporter_id: str
    reporter_name: str
    reporter_contact: str
    timestamp_received: str
    session_id: str

    # Orchestrator
    intent: str
    requires_clarification: bool
    clarification_message: str

    # Identifier
    incident_type: str
    severity: str
    confidence_score: float
    classification_reasoning: str

    # RAG / Mitigation
    retrieved_chunks: list[dict]
    mitigation_recommendation: str
    citations: list[dict]
    rag_confidence: float

    # Ticket
    ticket_id: str
    ticket_status: str
    escalation_level: str

    # Notifier
    notification_sent: bool
    notification_recipients: list[str]
    notification_timestamp: str

    # Meta
    processing_errors: list[str]
    agent_trace: list[dict]
