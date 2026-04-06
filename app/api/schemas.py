"""Pydantic schemas untuk FastAPI request/response."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=2000,
                           description="Deskripsi insiden keamanan siber")
    reporter_id: str = Field(..., min_length=1, max_length=50)
    reporter_name: str = Field(default="", max_length=100)
    reporter_contact: str = Field(default="", max_length=100)
    session_id: str = Field(default="", max_length=50)


class CitationOut(BaseModel):
    source: str
    section: str = ""
    content_preview: str = ""


class ReportResponse(BaseModel):
    ticket_id: str
    ticket_status: str
    intent: str
    incident_type: str
    severity: str
    confidence_score: float
    escalation_level: str
    mitigation_recommendation: str
    citations: list[CitationOut]
    rag_confidence: float
    requires_clarification: bool
    clarification_message: str
    notification_sent: bool
    processing_errors: list[str]


class TicketOut(BaseModel):
    ticket_id: str
    reporter_id: str
    reporter_name: str | None
    incident_type: str
    severity: str
    confidence_score: float | None
    status: str
    escalation_level: str | None
    description_sanitized: str
    mitigation_recommendation: str | None
    created_at: datetime | None
    is_duplicate: bool | None

    model_config = {"from_attributes": True}


class TicketUpdateRequest(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
    escalation_level: str | None = None
    notify_reporter: bool = True

    model_config = {"extra": "forbid"}


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_severity: dict[str, int]
    by_type: dict[str, int]


class HealthResponse(BaseModel):
    status: str
    service: str
    pipeline_ready: bool
