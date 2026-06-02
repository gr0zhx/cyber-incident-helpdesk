"""Guardrails — entry point lapisan keamanan pipeline."""
import logging

from app.security.llm_judge import LLMJudge
from app.security.pii_redactor import PIIRedactor
from app.security.prompt_injection import PromptInjectionDetector
from app.security.sanitizer import InputSanitizer

logger = logging.getLogger(__name__)

_sanitizer = InputSanitizer()
_detector = PromptInjectionDetector()
_redactor = PIIRedactor()
_judge = LLMJudge()


class GuardrailsResult:
    __slots__ = ("sanitized_input", "pii_mapping", "blocked", "block_reason")

    def __init__(
        self,
        sanitized_input: str,
        pii_mapping: dict,
        blocked: bool,
        block_reason: str,
    ) -> None:
        self.sanitized_input = sanitized_input
        self.pii_mapping = pii_mapping
        self.blocked = blocked
        self.block_reason = block_reason


def run_input_guardrails(raw_input: str) -> GuardrailsResult:
    """Jalankan seluruh pipeline guardrails input.

    Urutan:
    1. Sanitasi (HTML strip, kontrol char, panjang)
    2. Deteksi prompt injection regex → blokir jika positif (fail-closed)
    3. LLM judge → blokir jika positif (hanya jika token tersedia, fail-open)
    4. Redaksi PII → kirim versi ter-redaksi ke LLM

    Returns:
        GuardrailsResult dengan sanitized_input, pii_mapping, dan blocked flag.
    """
    # 1. Sanitasi
    sanitized = _sanitizer.sanitize(raw_input)

    # 2. Deteksi injeksi regex
    detection = _detector.detect(sanitized)
    if detection["is_injection"]:
        logger.warning(
            "Prompt injection terdeteksi (pattern: %s): %.80s",
            detection["matched_pattern"],
            sanitized,
        )
        return GuardrailsResult(
            sanitized_input="",
            pii_mapping={},
            blocked=True,
            block_reason=f"Input diblokir: terdeteksi pola '{detection['matched_pattern']}'",
        )

    # 3. LLM judge (skip jika tidak tersedia)
    if _judge.is_available() and _judge.is_jailbreak(sanitized):
        logger.warning("LLM judge: jailbreak terdeteksi: %.80s", sanitized)
        return GuardrailsResult(
            sanitized_input="",
            pii_mapping={},
            blocked=True,
            block_reason="Input diblokir: terdeteksi jailbreak oleh LLM judge",
        )

    # 4. Redaksi PII
    redacted, pii_mapping = _redactor.redact(sanitized)

    if pii_mapping:
        logger.info("PII ditemukan dan di-redaksi: %d item", len(pii_mapping))

    return GuardrailsResult(
        sanitized_input=redacted,
        pii_mapping=pii_mapping,
        blocked=False,
        block_reason="",
    )
