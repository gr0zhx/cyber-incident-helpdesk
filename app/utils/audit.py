"""Audit trail — catat setiap event pipeline ke tabel audit_logs."""
import logging
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


async def log_audit_event(
    audit_repository: Any,
    session_id: str,
    event_type: str,
    agent_name: str = "",
    action: str = "",
    user_id: str = "",
    input_summary: str = "",
    output_summary: str = "",
    guardrail_result: str = "",
    llm_model: str = "",
    token_count: int | None = None,
    latency_ms: int | None = None,
    error_message: str = "",
    extra_metadata: dict | None = None,
) -> None:
    """Catat satu event audit ke database secara async-safe (fire-and-forget).

    Jika audit_repository None atau operasi gagal, hanya log warning — jangan
    biarkan audit failure memblokir pipeline utama.
    """
    if audit_repository is None:
        return

    event_data = {
        "timestamp": datetime.now(timezone.utc),
        "event_type": event_type,
        "session_id": session_id,
        "user_id": user_id,
        "agent_name": agent_name,
        "action": action,
        "input_summary": input_summary[:500] if input_summary else "",
        "output_summary": output_summary[:500] if output_summary else "",
        "guardrail_result": guardrail_result,
        "llm_model": llm_model,
        "token_count": token_count,
        "latency_ms": latency_ms,
        "error_message": error_message[:500] if error_message else "",
        "extra_metadata": extra_metadata or {},
    }
    try:
        audit_repository.log_event(event_data)
    except Exception as exc:
        logger.warning("Gagal menyimpan audit log: %s", exc)


class PipelineAuditContext:
    """Context manager untuk mengukur latensi dan mencatat audit otomatis."""

    def __init__(
        self,
        audit_repository: Any,
        session_id: str,
        event_type: str,
        agent_name: str,
        action: str,
        user_id: str = "",
        llm_model: str = "",
    ) -> None:
        self._repo = audit_repository
        self._session_id = session_id
        self._event_type = event_type
        self._agent_name = agent_name
        self._action = action
        self._user_id = user_id
        self._llm_model = llm_model
        self._start: float = 0.0
        self.input_summary: str = ""
        self.output_summary: str = ""
        self.error_message: str = ""
        self.extra_metadata: dict = {}

    async def __aenter__(self) -> "PipelineAuditContext":
        self._start = time.monotonic()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        latency_ms = int((time.monotonic() - self._start) * 1000)
        if exc_val:
            self.error_message = f"{type(exc_val).__name__}: {exc_val}"
        await log_audit_event(
            audit_repository=self._repo,
            session_id=self._session_id,
            event_type=self._event_type,
            agent_name=self._agent_name,
            action=self._action,
            user_id=self._user_id,
            input_summary=self.input_summary,
            output_summary=self.output_summary,
            llm_model=self._llm_model,
            latency_ms=latency_ms,
            error_message=self.error_message,
            extra_metadata=self.extra_metadata,
        )
