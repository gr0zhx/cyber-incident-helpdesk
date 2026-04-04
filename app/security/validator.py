"""Output Validator — validasi output LLM sebelum disimpan ke tiket."""
import re

from app.security.pii_redactor import _EMAIL_RE, _IP_RE, _NIK_RE, _PHONE_RE

# Kata kunci aksi yang diizinkan (partial match, lowercase)
ALLOWED_ACTION_KEYWORDS: list[str] = [
    "ganti kata sandi", "ganti password",
    "putuskan koneksi", "disconnect",
    "laporkan ke it", "laporkan ke csirt", "hubungi csirt", "hubungi tim",
    "jangan klik link", "jangan buka", "jangan download",
    "scan antivirus", "jalankan antivirus",
    "backup data", "buat cadangan",
    "isolasi perangkat", "isolasi sistem", "karantina",
    "dokumentasikan kejadian", "catat kejadian",
    "blokir", "nonaktifkan akun", "reset akun",
    "perbarui", "update sistem", "patch",
    "aktifkan mfa", "aktifkan autentikasi",
    "segera", "langkah", "mitigasi", "prosedur",
]

_PII_PATTERNS = [_IP_RE, _EMAIL_RE, _NIK_RE, _PHONE_RE]


def _contains_pii(text: str) -> bool:
    return any(pat.search(text) for pat in _PII_PATTERNS)


class OutputValidator:
    def validate(self, output: str, retrieved_chunks: list) -> dict:
        """Validasi output mitigasi dari LLM.

        Pemeriksaan:
        1. Cek PII yang bocor di output
        2. Pastikan output tidak kosong
        3. Pastikan ada setidaknya satu kata kunci aksi yang diizinkan
           ATAU ada referensi sitasi ke sumber yang dikenal

        Returns:
            {
                "is_valid": bool,
                "issues": list[str],
                "cleaned_output": str,  # output setelah cleaning (saat ini passthrough)
            }
        """
        issues: list[str] = []

        # 1. Cek PII bocor
        if _contains_pii(output):
            issues.append("PII terdeteksi di output LLM")

        # 2. Cek output tidak kosong
        if not output or not output.strip():
            issues.append("Output kosong")

        # 3. Cek ada konten mitigasi yang bermakna
        output_lower = output.lower()
        has_action = any(kw in output_lower for kw in ALLOWED_ACTION_KEYWORDS)

        # Juga terima jika ada referensi ke sumber tepercaya
        has_known_source = any(
            src in output_lower
            for src in ["nist", "mitre", "bssn", "iso 27", "att&ck", "csirt"]
        )

        # Juga terima fallback resmi
        is_fallback = "tidak menemukan panduan sop" in output_lower or "hubungi tim csirt" in output_lower

        if not has_action and not has_known_source and not is_fallback and output.strip():
            issues.append("Output tidak mengandung tindakan mitigasi yang dikenal")

        is_valid = len(issues) == 0
        return {
            "is_valid": is_valid,
            "issues": issues,
            "cleaned_output": output,  # di Fase 7+ bisa ditambah auto-cleaning
        }
