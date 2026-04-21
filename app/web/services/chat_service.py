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

    def get_session_ticket(self, session_id: str) -> Optional[str]:
        """Return ticket_id created in this chat session, or None."""
        val = self._redis.get(f"web:session_ticket:{session_id}")
        return val.decode() if val else None

    def _set_session_ticket(self, session_id: str, ticket_id: str) -> None:
        self._redis.setex(f"web:session_ticket:{session_id}", _HISTORY_TTL, ticket_id.encode())

    def get_history(self, session_id: str) -> list[dict]:
        raw = self._redis.get(f"web:chat:{session_id}")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupt chat history session=%s, reset", session_id[:8])
            self._redis.delete(f"web:chat:{session_id}")
            return []

    def _save_history(self, session_id: str, history: list[dict]) -> None:
        self._redis.setex(
            f"web:chat:{session_id}", _HISTORY_TTL, json.dumps(history).encode()
        )

    def clear_history(self, session_id: str) -> None:
        self._redis.delete(f"web:chat:{session_id}")
        self._redis.delete(f"web:session_ticket:{session_id}")

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

        # Bug fix: jika tiket sudah dibuat di sesi ini, jangan buat tiket baru
        existing_ticket = self.get_session_ticket(session_id)
        if existing_ticket:
            bot_text = (
                f"Tiket insiden **{existing_ticket}** sudah dibuat untuk sesi ini. "
                f"Tim CSIRT akan segera menghubungi Anda. "
                f"Jika ada informasi tambahan, sampaikan langsung ke CSIRT dengan menyebutkan nomor tiket tersebut."
            )
            history.append({"role": "assistant", "content": bot_text, "ts": ts})
            self._save_history(session_id, history)
            return {
                "user_text": text,
                "bot_text": bot_text,
                "requires_clarification": False,
                "ticket_id": existing_ticket,
                "incident_type": "",
                "severity": "",
                "escalation_level": "",
                "confidence_score": 0.0,
                "error": False,
            }

        # Hitung berapa kali bot sudah minta klarifikasi sebelumnya
        clarification_rounds = sum(
            1 for m in history
            if m["role"] == "assistant" and not m["content"].startswith("Tiket insiden")
        )

        # Jika sudah ada percakapan sebelumnya, kirim konteks lengkap (Q&A)
        # agar orchestrator bisa memahami jawaban-jawaban user secara kontekstual
        recent = history[-8:]  # maks 4 pasang pesan
        if clarification_rounds >= 1:
            context_text = "\n".join(
                f"{'Pengguna' if m['role'] == 'user' else 'Asisten'}: {m['content']}"
                for m in recent
            )
        else:
            user_msgs = [m["content"] for m in history if m["role"] == "user"]
            context_text = "\n".join(user_msgs[-3:])

        state = orchestrator.initialize_state(
            raw_input=context_text,
            reporter_id=reporter_id,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            session_id=session_id,
            clarification_rounds=clarification_rounds,
        )

        try:
            result = await asyncio.wait_for(graph.ainvoke(state), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Pipeline timeout session=%s", session_id[:8])
            self._save_history(session_id, history)
            return {"error": True, "trace_id": session_id[:8]}

        requires_clarification: bool = result.get("requires_clarification", False)
        ticket_id: Optional[str] = result.get("ticket_id") or None

        # ticket_id takes priority — if a ticket was created, show it regardless
        # of clarification flags (avoids simultaneous clarification + ticket bug)
        if ticket_id:
            bot_text = (
                f"Tiket insiden berhasil dibuat: **{ticket_id}**.\n\n"
                f"{result.get('mitigation_recommendation', '')}"
            ).strip()
            self._set_session_ticket(session_id, ticket_id)
            if db is not None:
                self._flush_pending_uploads(session_id, ticket_id, reporter_id, db)
        elif requires_clarification:
            bot_text = result.get("clarification_message", "Mohon berikan informasi lebih lanjut.")
        else:
            mitigation = result.get("mitigation_recommendation", "")
            bot_text = mitigation if mitigation else "Respons tidak tersedia."

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
        key = f"web:pending_uploads:{session_id}"
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        pending_raw, _ = pipe.execute()
        if not pending_raw:
            return
        try:
            metas = json.loads(pending_raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupt pending_uploads session=%s, abort flush", session_id[:8])
            return
        for meta in metas:
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
