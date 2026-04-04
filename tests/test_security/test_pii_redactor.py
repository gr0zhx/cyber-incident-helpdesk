"""Unit tests for PIIRedactor."""
import pytest
from app.security.pii_redactor import PIIRedactor

r = PIIRedactor()


# --- IP Address ---

def test_redact_ipv4():
    text, mapping = r.redact("Server di 192.168.1.100 sudah dikompromis.")
    assert "192.168.1.100" not in text
    assert "[IP_DISUNTING]" in text
    assert mapping["[IP_DISUNTING]"] == "192.168.1.100"


def test_redact_multiple_ips():
    text, mapping = r.redact("Trafik dari 10.0.0.1 ke 10.0.0.2 mencurigakan.")
    assert "10.0.0.1" not in text
    assert "10.0.0.2" not in text
    assert len([k for k in mapping if "IP" in k]) == 2


def test_same_ip_twice_one_placeholder():
    text, mapping = r.redact("IP 192.168.1.1 dan lagi 192.168.1.1 muncul.")
    assert text.count("[IP_DISUNTING]") == 2
    assert len([k for k in mapping if "IP" in k]) == 1


# --- Email ---

def test_redact_email():
    text, mapping = r.redact("Kirim ke budi@kementan.go.id untuk konfirmasi.")
    assert "budi@kementan.go.id" not in text
    assert "[EMAIL_DISUNTING]" in text


def test_redact_multiple_emails():
    text, mapping = r.redact("Dari a@b.com ke c@d.com")
    assert "@" not in text.replace("[EMAIL_DISUNTING", "")
    assert len([k for k in mapping if "EMAIL" in k]) == 2


# --- NIK ---

def test_redact_nik_16_digits():
    text, mapping = r.redact("NIK saya 3275011234567890 mohon diverifikasi.")
    assert "3275011234567890" not in text
    assert "[NIK_DISUNTING]" in text


def test_not_redact_15_digit_number():
    text, mapping = r.redact("Nomor 123456789012345 bukan NIK.")
    assert "123456789012345" in text
    assert not any("NIK" in k for k in mapping)


# --- Telepon ---

def test_redact_phone_08xx():
    text, mapping = r.redact("Hubungi saya di 08123456789 segera.")
    assert "08123456789" not in text
    assert any("TELP" in k for k in mapping)


def test_redact_phone_plus62():
    text, mapping = r.redact("WA: +6281234567890")
    assert "+6281234567890" not in text
    assert any("TELP" in k for k in mapping)


# --- Restore ---

def test_restore_returns_original():
    original = "Email dari budi@kementan.go.id dari IP 10.1.2.3"
    redacted, mapping = r.redact(original)
    restored = r.restore(redacted, mapping)
    assert "budi@kementan.go.id" in restored
    assert "10.1.2.3" in restored


def test_restore_empty_mapping():
    text = "Laporan tanpa PII"
    redacted, mapping = r.redact(text)
    assert mapping == {}
    assert r.restore(redacted, mapping) == text


# --- No PII ---

def test_no_pii_text_unchanged():
    text = "Terjadi insiden phishing kemarin pagi di kantor pusat."
    redacted, mapping = r.redact(text)
    assert redacted == text
    assert mapping == {}
