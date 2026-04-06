"""Orchestrator Agent — klasifikasi intent dan inisialisasi IncidentState."""
import logging
from datetime import datetime, timezone

from openai import AsyncOpenAI, APITimeoutError

from app.agents.state import IncidentState
from app.utils.llm_parser import parse_llm_json
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

VALID_INTENTS = {"report_incident", "query_status", "general_help", "needs_clarification"}

_FALLBACK_INTENT = {
    "intent": "report_incident",
    "confidence": 0.0,
    "needs_clarification": False,
    "clarification_message": "",
}



def _validate_intent(parsed: dict) -> dict:
    intent = parsed.get("intent", "")
    if intent not in VALID_INTENTS:
        logger.warning("Intent '%s' tidak valid, fallback ke report_incident", intent)
        intent = "report_incident"

    try:
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    needs_clarification = bool(parsed.get("needs_clarification", False))
    clarification_message = str(parsed.get("clarification_message", "")).strip()

    # Konsistensi: needs_clarification hanya boleh True jika intent memang needs_clarification
    if intent != "needs_clarification":
        needs_clarification = False
        clarification_message = ""

    return {
        "intent": intent,
        "confidence": round(confidence, 3),
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_message,
    }


class OrchestratorAgent:
    def __init__(self, llm_client: AsyncOpenAI, model: str = "gpt-4o") -> None:
        self.llm = llm_client
        self.model = model
        self._prompt_template = load_prompt("orchestrator")

    def _build_messages(self, sanitized_input: str) -> list[dict]:
        prompt = self._prompt_template.replace("{sanitized_input}", sanitized_input)
        return [{"role": "user", "content": prompt}]

    async def classify_intent(self, sanitized_input: str) -> dict:
        """Klasifikasi intent pesan pengguna.

        Selalu mengembalikan dict — tidak pernah raise.
        Fallback: report_incident (fail-safe untuk insiden yang tidak terdeteksi).
        """
        messages = self._build_messages(sanitized_input)

        for attempt in range(2):
            try:
                response = await self.llm.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or ""
                parsed = parse_llm_json(raw)

                if parsed is None:
                    logger.error("Tidak bisa parse JSON dari LLM (attempt %d): %s", attempt + 1, raw[:200])
                    if attempt == 0:
                        continue
                    return dict(_FALLBACK_INTENT)

                return _validate_intent(parsed)

            except APITimeoutError:
                logger.warning("LLM timeout pada attempt %d", attempt + 1)
                if attempt == 1:
                    return dict(_FALLBACK_INTENT)

            except Exception as exc:
                logger.exception("Error tidak terduga saat classify_intent: %s", exc)
                return dict(_FALLBACK_INTENT)

        return dict(_FALLBACK_INTENT)

    def initialize_state(
        self,
        raw_input: str,
        reporter_id: str,
        reporter_name: str = "",
        reporter_contact: str = "",
        session_id: str = "",
    ) -> IncidentState:
        """Buat IncidentState baru dengan field input terisi."""
        return IncidentState(
            # Input
            raw_input=raw_input,
            sanitized_input=raw_input,  # akan diisi ulang oleh sanitizer di Fase 7
            reporter_id=reporter_id,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            timestamp_received=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            # Orchestrator
            intent="",
            requires_clarification=False,
            clarification_message="",
            # Identifier
            incident_type="",
            severity="",
            confidence_score=0.0,
            classification_reasoning="",
            # RAG / Mitigation
            retrieved_chunks=[],
            mitigation_recommendation="",
            citations=[],
            rag_confidence=0.0,
            # Ticket
            ticket_id="",
            ticket_status="",
            escalation_level="",
            # Notifier
            notification_sent=False,
            notification_recipients=[],
            notification_timestamp="",
            # Meta
            processing_errors=[],
            agent_trace=[],
        )
