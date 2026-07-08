"""Unit tests for InputSanitizer."""
import pytest
from app.security.sanitizer import InputSanitizer

s = InputSanitizer()


def test_strip_html_tags():
    assert "<script>" not in s.sanitize("<script>alert(1)</script>Laporan saya")
    assert "Laporan saya" in s.sanitize("<b>Laporan</b> saya")


def test_strip_html_preserves_content():
    result = s.sanitize("<p>Saya <b>klik</b> link phishing</p>")
    assert "klik" in result
    assert "phishing" in result
    assert "<" not in result


def test_max_length_enforcement():
    long_input = "A" * 3000
    result = s.sanitize(long_input)
    assert len(result) <= InputSanitizer.MAX_LENGTH


def test_max_length_exact():
    exact = "B" * InputSanitizer.MAX_LENGTH
    assert len(s.sanitize(exact)) == InputSanitizer.MAX_LENGTH


def test_control_chars_removed():
    result = s.sanitize("Laporan\x00ini\x01berbahaya\x07")
    assert "\x00" not in result
    assert "\x01" not in result
    assert "\x07" not in result
    assert "berbahaya" in result


def test_newlines_preserved():
    result = s.sanitize("Baris 1\nBaris 2\nBaris 3")
    assert "\n" in result


def test_multiple_spaces_collapsed():
    result = s.sanitize("Laporan    dengan     banyak   spasi")
    assert "  " not in result
    assert "banyak" in result


def test_strips_leading_trailing_whitespace():
    result = s.sanitize("   Laporan insiden   ")
    assert result == "Laporan insiden"


def test_empty_string():
    assert s.sanitize("") == ""


def test_non_string_input():
    result = s.sanitize(12345)
    assert isinstance(result, str)
    assert "12345" in result


def test_unicode_normalized():
    # NFC normalisasi: karakter dengan combining marks
    import unicodedata
    nfd = unicodedata.normalize("NFD", "é")  # e + combining acute
    result = s.sanitize(nfd)
    assert result == "é"  # NFC form
