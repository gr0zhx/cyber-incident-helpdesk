"""Prompt Injection Detector — deteksi upaya manipulasi instruksi LLM."""
import base64
import re

# Pola injeksi yang umum — fail-closed: jika cocok, blokir
_RAW_PATTERNS: list[tuple[str, str]] = [
    # Instruksi override
    (r"ignore\s+(previous|all|above|prior)\s+(instructions?|prompt|rules?|context)", "override_instruction"),
    (r"disregard\s+(previous|all|above|prior|the)", "override_instruction"),
    (r"forget\s+(everything|all|previous|prior|above)", "override_instruction"),

    # Persona manipulation
    (r"you\s+are\s+now\s+(?!a\s+helpdesk)", "persona_switch"),
    (r"\bact\s+as\b", "persona_switch"),
    (r"pretend\s+(to\s+be|you\s+are)", "persona_switch"),
    (r"roleplay\s+as", "persona_switch"),
    (r"simulate\s+(being|a)", "persona_switch"),

    # Instruksi sistem
    (r"(system\s+prompt|system\s+instruction|your\s+instructions?)", "system_leak"),
    (r"reveal\s+(your|the)\s+(instructions?|prompt|rules?|system)", "system_leak"),
    (r"print\s+(your|the)\s+(instructions?|prompt|system\s+prompt)", "system_leak"),
    (r"what\s+(are|is)\s+your\s+(instructions?|system\s+prompt)", "system_leak"),

    # Encoding obfuscation — gunakan karakter literal \\x dan \\u agar cocok dengan teks yang ditulis user
    (r"\\x[0-9a-fA-F]{2}", "encoding_obfuscation"),
    (r"\\u00[0-9a-fA-F]{2}", "encoding_obfuscation"),
    (r"&#x[0-9a-fA-F]+;", "encoding_obfuscation"),

    # Jailbreak klasik
    (r"jailbreak", "jailbreak"),
    (r"do\s+anything\s+now", "jailbreak"),
    (r"developer\s+mode", "jailbreak"),

    # Persona AI buatan (contoh: "BasedGPT", "FreeSpeechGPT", "CumGPT")
    (r"\b\w{2,}gpt\b", "persona_switch"),
    (r"an?\s+(?:ai|bot|model|assistant)\s+named", "persona_switch"),
    (r"from\s+now\s+(?:on\s+)?you\s+are", "persona_switch"),
    (r"always\s+stays?\s+in\s+character", "persona_switch"),
    # "You are [NamaKarakter]" atau "YOU ARE X" — persona assignment langsung
    (r"you\s+are\s+(?!(?:able|correct|welcome|sure|right|aware|going|trying|looking|asking|saying|thinking|using|working|doing|making|getting|helping|ready|here|a\s+helpdesk))[A-Z]\w+", "persona_switch"),

    # Konten amoral / tanpa filter
    (r"\bamoral\b", "jailbreak"),
    (r"\buncensored\b", "jailbreak"),
    (r"\bunfiltered\b", "jailbreak"),
    (r"\bno\s+restrictions?\b", "jailbreak"),

    # Instruksi untuk tidak menolak
    (r"never\s+refus", "jailbreak"),
    (r"answer\s+any\s+(?:request|question|prompt)", "jailbreak"),

    # Framing dua mode / dua kepribadian
    (r"two\s+(?:different\s+)?(?:ways?|modes?|responses?|personalities?)", "jailbreak"),

    # Framing hipotetikal / cerita fiksi
    (r"in\s+this\s+(?:fictional|hypothetical)\s+(?:story|scenario|world|universe|reality)", "jailbreak"),

    # Blok konfigurasi karakter (rules={, settings:{)
    (r"rules\s*[=:]\s*\{", "jailbreak"),
]

_COMPILED: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in _RAW_PATTERNS
]

# Pola base64 heuristik: string panjang tanpa spasi yang terlihat seperti base64
_BASE64_RE = re.compile(r"(?<!\w)[A-Za-z0-9+/]{40,}={0,2}(?!\w)")

_REGEX_CONFIDENCE = 0.95
_BASE64_CONFIDENCE = 0.80


def _check_base64(text: str) -> bool:
    """Cek apakah ada base64 yang terlihat, dan coba decode untuk isi berbahaya."""
    for match in _BASE64_RE.finditer(text):
        candidate = match.group(0)
        try:
            decoded = base64.b64decode(candidate + "==").decode("utf-8", errors="ignore")
            decoded_lower = decoded.lower()
            if any(kw in decoded_lower for kw in ["ignore", "system", "prompt", "act as", "jailbreak"]):
                return True
        except Exception:
            pass
    return False


class PromptInjectionDetector:
    def detect(self, text: str) -> dict:
        """Deteksi upaya prompt injection dalam teks input.

        Layer 1: regex pattern matching
        Layer 2: base64 obfuscation check

        Returns:
            {
                "is_injection": bool,
                "confidence": float,    # 0.0–1.0
                "matched_pattern": str, # label pola yang cocok, atau ""
            }
        """
        if not text:
            return {"is_injection": False, "confidence": 0.0, "matched_pattern": ""}

        # Layer 1: regex
        for pattern, label in _COMPILED:
            if pattern.search(text):
                return {"is_injection": True, "confidence": _REGEX_CONFIDENCE, "matched_pattern": label}

        # Layer 2: base64
        if _check_base64(text):
            return {"is_injection": True, "confidence": _BASE64_CONFIDENCE, "matched_pattern": "encoding_obfuscation"}

        return {"is_injection": False, "confidence": 0.0, "matched_pattern": ""}
