"""Layanan chat pelapor: history Redis + pipeline invoke."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Pola sapaan pembuka — dibalas langsung tanpa pipeline LLM
_GREETING_RE = re.compile(
    r"""^\s*
    (
        (halo+|hai+|hi+|hey+|hei+|helo+|hello+)   # sapaan dasar
        (\s+(semuanya|kak|pak|bu|min|admin|bot|semua))?  # opsional panggilan
        |
        (selamat\s+(pagi|siang|sore|malam))        # salam waktu
        (\s+(kak|pak|bu|min|admin|semua))?
        |
        (assalamualaikum|assalamu'alaikum|ass\.?wr\.?wb\.?)  # salam islami
        |
        (permisi|horas|sugeng|apa\s+kabar)         # variasi lain
    )
    \s*[!.,?]*\s*$""",
    re.IGNORECASE | re.VERBOSE,
)

# Pola pesan penutup/acknowledgment — dibalas langsung tanpa pipeline LLM
_FAREWELL_RE = re.compile(
    r"""^\s*
    (
        # Ucapan terima kasih saja atau diikuti kalimat pendek
        (terima\s*kasih|makasih|thanks|thank\s*you)(\s+.{0,50})?
        |
        # Pamit / salam penutup
        (sampai\s*jumpa|selamat\s*tinggal|bye+|see\s*you|dadah)(\s+.{0,30})?
        |
        # Oke/baik/sip + opsional terima kasih + opsional kalimat pendek
        (oke+|ok|baik|sip|siap|mantap|noted|got\s*it|alright|paham|mengerti)
        (\s*[!.,]?\s*(terima\s*kasih|makasih|thanks)?)?(\s+.{0,40})?
    )
    \s*[!.,]*\s*$""",
    re.IGNORECASE | re.VERBOSE,
)

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
        reporter_unit: str = "",
        text: str,
        graph: Any,
        orchestrator: Any,
        db: Any = None,
        timeout: float = 60.0,
        # Bagian A / B dari form identitas
        media_pelaporan: str = "",
        incident_time: str = "",
        affected_asset: str = "",
    ) -> dict:
        """Invoke pipeline dan return dict hasil untuk template."""
        history = self.get_history(session_id)
        ts = datetime.now(timezone.utc).isoformat()
        history.append({"role": "user", "content": text, "ts": ts})

        # Hitung berapa kali bot sudah minta klarifikasi sebelumnya.
        # Hanya hitung pesan yang secara eksplisit diberi tag type="clarification"
        # agar pesan timeout/error tidak ikut terhitung.
        clarification_rounds = sum(
            1 for m in history
            if m.get("type") == "clarification"
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

        # Sertakan info file lampiran (jika ada) ke dalam konteks teks
        # supaya LLM pipeline tahu bahwa ada bukti visual / dokumen.
        pending_key = f"web:pending_uploads:{session_id}"
        pending_raw = self._redis.get(pending_key)
        if pending_raw:
            try:
                pending_files = json.loads(pending_raw)
                if pending_files:
                    attach_lines = []
                    for pf in pending_files:
                        name = pf.get("original_filename", "file")
                        mime = pf.get("mime_type", "")
                        kind = "gambar" if mime.startswith("image/") else "dokumen PDF" if "pdf" in mime else "file"
                        attach_lines.append(f"- {name} ({kind})")
                    context_text += (
                        "\n\n[Lampiran yang disertakan pengguna:\n"
                        + "\n".join(attach_lines)
                        + "\nFile-file ini akan direview oleh Tim Keamanan Siber dan PDP.]"
                    )
            except (json.JSONDecodeError, ValueError):
                pass

        # Jika tiket sudah dibuat di sesi ini, teruskan ke graph agar orchestrator
        # bisa memutuskan dalam SATU classify_intent: kalau intent-nya upaya
        # melapor insiden lagi, graph merutekan ke node existing_ticket (tanpa
        # membuat tiket baru); intent lain (query_knowledge/general_help/dst)
        # tetap diproses seperti biasa.
        existing_ticket = self.get_session_ticket(session_id)

        # Short-circuit: sapaan pembuka — tidak perlu LLM
        if len(text) <= 80 and _GREETING_RE.match(text):
            bot_text = (
                "Halo! Selamat datang di layanan pelaporan insiden siber Pusdatin Kementan. "
                "Saya siap membantu Anda.\n\n"
                "Anda dapat:\n"
                "- **Melaporkan insiden siber** (phishing, malware, ransomware, dll.)\n"
                "- **Menanyakan informasi** seputar keamanan siber\n"
                "- **Mengecek prosedur** penanganan insiden\n\n"
                "Silakan ceritakan apa yang ingin Anda laporkan atau tanyakan!"
            )
            history.append({"role": "assistant", "content": bot_text, "ts": ts})
            self._save_history(session_id, history)
            return {
                "user_text": text,
                "bot_text": bot_text,
                "requires_clarification": False,
                "ticket_id": None,
                "incident_type": "",
                "severity": "",
                "escalation_level": "",
                "confidence_score": 0.0,
                "error": False,
            }

        # Short-circuit: pesan penutup / acknowledgment — tidak perlu LLM
        if len(text) <= 120 and _FAREWELL_RE.match(text):
            bot_text = (
                "Sama-sama! Jika ada insiden siber atau pertanyaan lain, "
                "jangan ragu menghubungi kami kembali. Semoga harimu menyenangkan!"
            )
            history.append({"role": "assistant", "content": bot_text, "ts": ts})
            self._save_history(session_id, history)
            return {
                "user_text": text,
                "bot_text": bot_text,
                "requires_clarification": False,
                "ticket_id": None,
                "incident_type": "",
                "severity": "",
                "escalation_level": "",
                "confidence_score": 0.0,
                "error": False,
            }

        state = orchestrator.initialize_state(
            raw_input=context_text,
            reporter_id=reporter_id,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            reporter_unit=reporter_unit,
            session_id=session_id,
            clarification_rounds=clarification_rounds,
            session_existing_ticket=existing_ticket or "",
        )

        try:
            result = await asyncio.wait_for(graph.ainvoke(state), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Pipeline timeout session=%s", session_id[:8])
            self._save_history(session_id, history)
            bot_text = (
                "Maaf, sistem sedang sibuk memproses laporan Anda. "
                "Silakan coba kirim ulang pesan dalam beberapa saat lagi."
            )
            history.append({"role": "assistant", "content": bot_text, "ts": ts})
            self._save_history(session_id, history)
            return {
                "user_text": text,
                "bot_text": bot_text,
                "requires_clarification": False,
                "ticket_id": None,
                "incident_type": "",
                "severity": "",
                "escalation_level": "",
                "confidence_score": 0.0,
                "error": False,
            }
        except Exception as exc:
            logger.exception("Pipeline error session=%s: %s", session_id[:8], exc)
            bot_text = (
                "Maaf, sistem mengalami kendala saat memproses laporan Anda. "
                "Silakan coba lagi sebentar lagi."
            )
            history.append({"role": "assistant", "content": bot_text, "ts": ts})
            self._save_history(session_id, history)
            return {
                "user_text": text,
                "bot_text": bot_text,
                "requires_clarification": False,
                "ticket_id": None,
                "incident_type": "",
                "severity": "",
                "escalation_level": "",
                "confidence_score": 0.0,
                "error": False,
            }

        requires_clarification: bool = result.get("requires_clarification", False)
        ticket_id: Optional[str] = result.get("ticket_id") or None

        # ticket_id takes priority — if a ticket was created, show it regardless
        # of clarification flags (avoids simultaneous clarification + ticket bug)
        if ticket_id and existing_ticket and ticket_id == existing_ticket:
            bot_text = (
                f"Tiket insiden **{ticket_id}** sudah dibuat untuk sesi ini. "
                f"Tim Keamanan Siber dan PDP akan segera menghubungi Anda. "
                f"Jika ada informasi tambahan, sampaikan langsung dengan menyebutkan nomor tiket tersebut."
            )
        elif ticket_id:
            bot_text = (
                f"Tiket insiden berhasil dibuat: **{ticket_id}**.\n\n"
                f"{result.get('mitigation_recommendation', '')}"
            ).strip()
            self._set_session_ticket(session_id, ticket_id)
            if db is not None:
                self._flush_pending_uploads(session_id, ticket_id, reporter_id, db)
                try:
                    self._backfill_form_fields(
                        ticket_id, db,
                        media_pelaporan=media_pelaporan,
                        incident_time_str=incident_time,
                        affected_asset=affected_asset,
                    )
                except Exception as exc:
                    logger.warning(
                        "Backfill form fields gagal (tiket %s tetap ada): %s",
                        ticket_id, exc,
                    )
        elif requires_clarification:
            bot_text = result.get("clarification_message", "Mohon berikan informasi lebih lanjut.")
        else:
            mitigation = result.get("mitigation_recommendation", "")
            bot_text = mitigation if mitigation else "Respons tidak tersedia."

        # Tag pesan klarifikasi agar counter clarification_rounds akurat.
        # JANGAN tag jika ini hasil blokir guardrails — guardrails mengisi
        # processing_errors; klarifikasi asli dari orchestrator tidak.
        msg_entry: dict = {"role": "assistant", "content": bot_text, "ts": ts}
        guardrails_blocked = bool(result.get("processing_errors"))
        if requires_clarification and not ticket_id and not guardrails_blocked:
            msg_entry["type"] = "clarification"
        history.append(msg_entry)
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

    def _backfill_form_fields(
        self, ticket_id: str, db: Any, *,
        media_pelaporan: str,
        incident_time_str: str,
        affected_asset: str,
    ) -> None:
        from app.database.models import IncidentTicket
        from datetime import datetime as _dt
        ticket = db.query(IncidentTicket).filter_by(ticket_id=ticket_id).first()
        if ticket is None:
            return
        if media_pelaporan:
            ticket.media_pelaporan = media_pelaporan
        if affected_asset:
            ticket.affected_asset = affected_asset
        if incident_time_str:
            try:
                ticket.incident_time = _dt.fromisoformat(incident_time_str)
            except ValueError:
                pass
        db.commit()

    def _flush_pending_uploads(
        self, session_id: str, ticket_id: str, uploaded_by: str, db: Any
    ) -> None:
        from app.database.models import TicketAttachment
        key = f"web:pending_uploads:{session_id}"
        # Atomic GET+DELETE via pipeline — mencegah race condition jika ada upload
        # bersamaan selama pipeline LLM berjalan (~10-30 detik).
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
