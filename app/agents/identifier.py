import json
import logging
from pathlib import Path

from openai import AsyncOpenAI, APITimeoutError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "config" / "prompts" / "identifier.txt"

VALID_TYPES = [
    "Phishing",
    "Malware",
    "Ransomware",
    "Web Defacement",
    "DDoS",
    "Akses Tidak Sah",
    "Kebocoran Data",
    "Lainnya",
]

VALID_SEVERITIES = ["Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"]

_FALLBACK_RESULT = {
    "incident_type": "Lainnya",
    "severity": "Sedang",
    "confidence_score": 0.0,
    "reasoning": "Klasifikasi otomatis gagal. Perlu review manual.",
    "requires_review": True,
}


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _parse_llm_response(raw: str) -> dict | None:
    """Try to extract a valid JSON object from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON block from surrounding text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return None


def _validate_and_normalize(parsed: dict) -> dict:
    """Validate required fields and normalise values."""
    incident_type = parsed.get("incident_type", "")
    if incident_type not in VALID_TYPES:
        logger.warning("incident_type '%s' tidak valid, fallback ke 'Lainnya'", incident_type)
        incident_type = "Lainnya"

    severity = parsed.get("severity", "")
    if severity not in VALID_SEVERITIES:
        logger.warning("severity '%s' tidak valid, fallback ke 'Sedang'", severity)
        severity = "Sedang"

    try:
        confidence = float(parsed.get("confidence_score", 0.0))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0

    reasoning = str(parsed.get("reasoning", "")).strip()

    requires_review = confidence < 0.7

    return {
        "incident_type": incident_type,
        "severity": severity,
        "confidence_score": round(confidence, 3),
        "reasoning": reasoning,
        "requires_review": requires_review,
    }


class IncidentIdentifierAgent:
    def __init__(self, llm_client: AsyncOpenAI, model: str = "gpt-4o") -> None:
        self.llm = llm_client
        self.model = model
        self._prompt_template = _load_prompt()

    def _build_messages(self, sanitized_input: str) -> list[dict]:
        prompt = self._prompt_template.replace("{sanitized_input}", sanitized_input)
        return [{"role": "user", "content": prompt}]

    async def classify(self, sanitized_input: str) -> dict:
        """Classify an incident report and return a structured dict.

        Always returns a dict — never raises. Falls back gracefully on error.
        """
        messages = self._build_messages(sanitized_input)

        for attempt in range(2):
            try:
                response = await self.llm.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=300,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or ""
                parsed = _parse_llm_response(raw)

                if parsed is None:
                    logger.error("Tidak bisa parse JSON dari LLM (attempt %d): %s", attempt + 1, raw[:200])
                    if attempt == 0:
                        continue
                    return {**_FALLBACK_RESULT, "reasoning": f"Gagal parse JSON LLM. Raw: {raw[:100]}"}

                return _validate_and_normalize(parsed)

            except APITimeoutError:
                logger.warning("LLM timeout pada attempt %d", attempt + 1)
                if attempt == 1:
                    return {**_FALLBACK_RESULT, "reasoning": "LLM timeout setelah 2 percobaan."}

            except Exception as exc:
                logger.exception("Error tidak terduga saat classify (attempt %d): %s", attempt + 1, exc)
                return {**_FALLBACK_RESULT, "reasoning": f"Error tidak terduga: {type(exc).__name__}"}

        return _FALLBACK_RESULT
