"""Unit tests for OutputValidator."""
import pytest
from app.security.validator import OutputValidator

v = OutputValidator()


def test_valid_output_with_known_source():
    result = v.validate(
        "1. Jangan klik link mencurigakan. [NIST SP 800-61]",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is True
    assert result["issues"] == []


def test_valid_output_with_action_keyword():
    result = v.validate(
        "Langkah mitigasi: isolasi perangkat dan hubungi CSIRT segera.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is True


def test_valid_fallback_message():
    result = v.validate(
        "Sistem tidak menemukan panduan SOP yang relevan. Silakan hubungi tim CSIRT secara langsung.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is True


def test_empty_output_invalid():
    result = v.validate("", retrieved_chunks=[])
    assert result["is_valid"] is False
    assert any("kosong" in i.lower() or "empty" in i.lower() for i in result["issues"])


def test_output_with_pii_ip_invalid():
    result = v.validate(
        "Blokir IP 192.168.1.100 segera dan laporkan ke CSIRT.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is False
    assert any("PII" in i for i in result["issues"])


def test_output_with_pii_email_invalid():
    result = v.validate(
        "Kirim laporan ke budi@kementan.go.id untuk tindak lanjut.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is False
    assert any("PII" in i for i in result["issues"])


def test_pii_in_output_replaces_recommendation():
    """Pastikan validator mengembalikan cleaned_output (field wajib ada)."""
    result = v.validate("IP 10.0.0.1 harus diblokir", retrieved_chunks=[])
    assert "cleaned_output" in result


def test_result_keys_always_present():
    for text in ["", "mitigasi: scan antivirus", "tidak relevan sama sekali xyz abc"]:
        result = v.validate(text, retrieved_chunks=[])
        assert "is_valid" in result
        assert "issues" in result
        assert "cleaned_output" in result


def test_output_with_mitre_reference_valid():
    result = v.validate(
        "Terapkan mitigasi sesuai MITRE ATT&CK M1017 User Training.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is True


def test_output_no_action_no_source_invalid():
    result = v.validate(
        "Teks ini tidak memiliki rekomendasi sama sekali hanya kata-kata kosong.",
        retrieved_chunks=[]
    )
    assert result["is_valid"] is False
