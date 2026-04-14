"""Layanan chat pelapor: history Redis + pipeline invoke."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HISTORY_TTL = 86400  # 24h


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str
    ts: str


class ChatService:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(self, session_id: str) -> list[dict]:
        raw = self._redis.get(f"web:chat:{session_id}")
        if not raw:
            return []
        return json.loads(raw)

    def _save_history(self, session_id: str, history: list[dict]) -> None:
        self._redis.setex(
            f"web:chat:{session_id}", _HISTORY_TTL, json.dumps(history).encode()
        )

    def clear_history(self, session_id: str) -> None:
        self._redis.delete(f"web:chat:{session_id}")

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def handle_message(
        self,
        *,
        session_id: str,
        reporter_id: str,
        reporter_name: str,
        reporter_contact: str,
        text: str,
        graph: Any,
        orchestrator: Any,
        db: Any = None,
        timeout: float = 30.0,
    ) -> dict:
        """Invoke pipeline dan return dict hasil untuk template."""
        history = self.get_history(session_id)
        ts = datetime.now(timezone.utc).isoformat()
        history.append({"role": "user", "content": text, "ts": ts})

        # Multi-turn context: concat last 3 user messages
        user_msgs = [m["content"] for m in history if m["role"] == "user"]
        context_text = "\n".join(user_msgs[-3:])

        state = orchestrator.initialize_state(
            raw_input=context_text,
            reporter_id=reporter_id,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            session_id=session_id,
        )

        try:
            result = await asyncio.wait_for(graph.ainvoke(state), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Pipeline timeout session=%s", session_id[:8])
            self._save_history(session_id, history)
            return {"error": True, "trace_id": session_id[:8]}

        requires_clarification: bool = result.get("requires_clarification", False)
        ticket_id: Optional[str] = result.get("ticket_id") or None

        if requires_clarification:
            bot_text = result.get("clarification_message", "Mohon berikan informasi lebih lanjut.")
        elif ticket_id:
            bot_text = (
                f"Tiket insiden berhasil dibuat: **{ticket_id}**.\n\n"
                f"{result.get('mitigation_recommendation', '')}"
            ).strip()
            if db is not None:
                self._flush_pending_uploads(session_id, ticket_id, reporter_id, db)
        else:
            bot_text = result.get("mitigation_recommendation", "Respons tidak tersedia.")

        history.append({"role": "assistant", "content": bot_text, "ts": ts})
        self._save_history(session_id, history)

        return {
            "user_text": text,
            "bot_text": bot_text,
            "requires_clarification": requires_clarification,
            "ticket_id": ticket_id,
            "incident_type": result.get("incident_type", ""),
            "severity": result.get("severity", ""),
            "escalation_level": result.get("escalation_level", ""),
            "confidence_score": result.get("confidence_score", 0.0),
            "error": False,
        }

    def _flush_pending_uploads(
        self, session_id: str, ticket_id: str, uploaded_by: str, db: Any
    ) -> None:
        from app.database.models import TicketAttachment
        pending_raw = self._redis.get(f"web:pending_uploads:{session_id}")
        if not pending_raw:
            return
        self._redis.delete(f"web:pending_uploads:{session_id}")
        for meta in json.loads(pending_raw):
            att = TicketAttachment(
                ticket_id=ticket_id,
                original_filename=meta["original_filename"],
                stored_path=meta["stored_path"],
                mime_type=meta["mime_type"],
                size_bytes=meta["size_bytes"],
                uploaded_by=uploaded_by,
            )
            db.add(att)
        db.commit()
