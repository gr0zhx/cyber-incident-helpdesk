from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, Integer, JSON, Numeric, String, Text, DateTime, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

# Resolves to JSONB on PostgreSQL, JSON (TEXT-backed) on SQLite/others
JsonB = JSON().with_variant(JSONB(), "postgresql")

# Resolves to BIGINT on PostgreSQL, INTEGER on SQLite (needed for autoincrement)
BigInt = Integer().with_variant(BigInteger(), "postgresql")


class Base(DeclarativeBase):
    pass


class IncidentTicket(Base):
    __tablename__ = "incident_tickets"

    ticket_id = Column(String(20), primary_key=True)
    reporter_id = Column(String(50), nullable=False)
    reporter_name = Column(String(100))
    reporter_contact = Column(String(100))
    reporter_department = Column(String(100))

    incident_type = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence_score = Column(Numeric(4, 3))

    description_raw = Column(Text, nullable=False)
    description_sanitized = Column(Text, nullable=False)

    evidence_files = Column(JsonB)
    evidence_urls = Column(JsonB)

    mitigation_recommendation = Column(Text)
    citations = Column(JsonB)
    rag_confidence = Column(Numeric(4, 3))

    status = Column(String(30), default="PENDING_REVIEW")
    escalation_level = Column(String(20))
    assigned_to = Column(String(100))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    classification_reasoning = Column(Text)
    agent_trace = Column(JsonB)
    notification_status = Column(String(20))
    is_duplicate = Column(Boolean, default=False)
    parent_ticket_id = Column(String(20))

    created_by = Column(String(50), default="SYSTEM")
    modified_by = Column(String(50))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(BigInt, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    event_type = Column(String(50), nullable=False)
    session_id = Column(String(50))
    user_id = Column(String(50))
    agent_name = Column(String(30))
    action = Column(String(100))
    input_summary = Column(Text)
    output_summary = Column(Text)
    guardrail_result = Column(String(20))
    llm_model = Column(String(50))
    token_count = Column(Integer)
    latency_ms = Column(Integer)
    error_message = Column(Text)
    extra_metadata = Column("metadata", JsonB)
