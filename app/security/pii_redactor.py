"""PII Redactor — deteksi dan redaksi data pribadi sebelum dikirim ke LLM."""
import re

# --- Pola regex PII ---
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_NIK_RE = re.compile(r"\b\d{16}\b")
# Telepon Indonesia: 08xx, +628xx, 628xx — 10–15 digit
_PHONE_RE = re.compile(r"(?<!\d)(?:\+62|62|0)[\s\-]?(?:8\d{2}|2[1-9]\d|7[1-9]\d)[\s\-]?\d{3,4}[\s\-]?\d{3,5}(?!\d)")


class PIIRedactor:
    def redact(self, text: str) -> tuple[str, dict]:
        """Redaksi PII dari teks dan kembalikan teks yang sudah bersih beserta mapping.

        Urutan redaksi: IP → Email → NIK → Telepon
        (IP lebih dulu agar tidak konflik dengan angka di nomor telepon)

        Returns:
            (redacted_text, mapping) — mapping: placeholder → nilai asli
        """
        mapping: dict[str, str] = {}
        counters: dict[str, int] = {}

        def _replace(match: re.Match, prefix: str) -> str:
            original = match.group(0)
            # Cek apakah sudah di-redaksi sebelumnya (nilai yang sama muncul dua kali)
            existing = next(
                (k for k, v in mapping.items() if v == original and k.startswith(f"[{prefix}")),
                None,
            )
            if existing:
                return existing
            counters[prefix] = counters.get(prefix, 0) + 1
            n = counters[prefix]
            placeholder = f"[{prefix}_{n}]" if n > 1 else f"[{prefix}]"
            mapping[placeholder] = original
            return placeholder

        text = _IP_RE.sub(lambda m: _replace(m, "IP_DISUNTING"), text)
        text = _EMAIL_RE.sub(lambda m: _replace(m, "EMAIL_DISUNTING"), text)
        text = _NIK_RE.sub(lambda m: _replace(m, "NIK_DISUNTING"), text)
        text = _PHONE_RE.sub(lambda m: _replace(m, "TELP_DISUNTING"), text)

        return text, mapping

    def restore(self, redacted_text: str, mapping: dict) -> str:
        """Kembalikan placeholder ke nilai asli (untuk tiket internal)."""
        text = redacted_text
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text
