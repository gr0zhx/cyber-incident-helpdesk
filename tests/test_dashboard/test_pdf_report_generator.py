from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypdf import PdfReader

import app.dashboard.pdf_report_generator as prg
from app.dashboard.pdf_report_generator import (
    _fallback_summary,
    _fit_font_size,
    _strip_chat_prefixes,
    _wrap_lines,
    build_field_values,
    generate_report_filename,
    generate_report_pdf,
    summarize_for_report,
)


def _base_ticket(**overrides) -> dict:
    ticket = {
        "ticket_id": "TICKET-2026-0001",
        "incident_type": "Phishing",
        "severity": "Tinggi",
        "status": "IN_PROGRESS",
        "reporter_name": "Budi Santoso",
        "reporter_contact": "0812-0000-0000",
        "reporter_department": "Divisi IT",
        "assigned_to": "andi",
        "description_sanitized": "Email mencurigakan meminta reset password.",
        "mitigation_recommendation": "Isolasi host dari jaringan dan reset kredensial akun terdampak segera.",
        "media_pelaporan": "Sistem Tiket",
        "incident_time": datetime(2026, 7, 5, 9, 30, tzinfo=timezone.utc),
        "affected_asset": "Laptop Dinas",
        "cia_confidentiality": True,
        "cia_integrity": False,
        "cia_availability": None,
        "containment_action": "",
        "recovery_action": "",
        "created_at": datetime(2026, 7, 5, 10, 0, tzinfo=timezone.utc),
        "reviewed_at": None,
        "resolved_at": None,
        "closed_at": None,
    }
    ticket.update(overrides)
    return ticket


@pytest.fixture(autouse=True)
def _no_real_llm_calls(monkeypatch):
    """Semua test di file ini memakai fallback heuristik (deterministik, tanpa
    network) sebagai pengganti summarize_for_report — kecuali test yang secara
    eksplisit menguji summarize_for_report itu sendiri (lihat class TestSummarizeForReport)."""
    monkeypatch.setattr(prg, "summarize_for_report", _fallback_summary)


def test_generate_report_pdf_returns_valid_pdf_bytes():
    pdf_bytes = generate_report_pdf(_base_ticket())
    assert pdf_bytes[:5] == b"%PDF-"
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 3


def test_generate_report_filename_ends_with_pdf():
    filename = generate_report_filename(_base_ticket())
    assert filename.startswith("Laporan-Insiden-TICKET-2026-0001")
    assert filename.endswith(".pdf")


def test_build_field_values_maps_reporter_and_media():
    values = build_field_values(_base_ticket(), prepared_by="Andi")
    assert values["nama_pelapor"] == "Budi Santoso"
    assert values["unit_kerja"] == "Divisi IT"
    assert values["media_sistem_tiket"] == "/Yes"
    assert "media_email" not in values


def test_build_field_values_maps_unknown_incident_type_to_lainnya():
    values = build_field_values(_base_ticket(incident_type="Phishing"), prepared_by="Andi")
    assert values["kategori_lainnya"] == "/Yes"
    assert values["kategori_lainnya_text"] == "Phishing"
    assert "kategori_malware_virus" not in values


def test_build_field_values_maps_known_incident_type_to_category():
    values = build_field_values(_base_ticket(incident_type="Ransomware"), prepared_by="Andi")
    assert values["kategori_malware_virus"] == "/Yes"
    assert "kategori_lainnya" not in values


def test_build_field_values_maps_severity():
    values = build_field_values(_base_ticket(severity="Kritis"), prepared_by="Andi")
    assert values["severity_critical"] == "/Yes"


def test_build_field_values_cia_checkbox_only_set_when_known():
    values = build_field_values(_base_ticket(), prepared_by="Andi")
    assert values["cia_conf_terlanggar"] == "/Yes"  # True -> terlanggar
    assert values["cia_integ_terjaga"] == "/Yes"     # False -> terjaga
    assert "cia_avail_terjaga" not in values          # None -> tidak dicentang
    assert "cia_avail_terganggu" not in values


def test_build_field_values_merges_mitigation_into_containment_recovery_when_empty():
    values = build_field_values(_base_ticket(containment_action="", recovery_action=""), prepared_by="Andi")
    combined = values["containment_line1"] + " " + values["containment_line2"]
    assert "Isolasi host" in combined
    assert values["recovery_line1"] or values["recovery_line2"]


def test_build_field_values_prefers_explicit_containment_recovery():
    values = build_field_values(
        _base_ticket(containment_action="Matikan akses VPN.", recovery_action="Pulihkan dari backup."),
        prepared_by="Andi",
    )
    assert values["containment_line1"] == "Matikan akses VPN."
    assert values["recovery_line1"] == "Pulihkan dari backup."


def test_build_field_values_status_maps_to_checkbox():
    values = build_field_values(_base_ticket(status="RESOLVED"), prepared_by="Andi")
    assert values["status_monitoring"] == "/Yes"
    assert "status_open" not in values


def test_build_field_values_strips_chat_transcript_from_kronologi():
    ticket = _base_ticket(
        description_sanitized="Pengguna: Halo Asisten: Halo, ada yang bisa dibantu? "
        "Pengguna: File saya terenkripsi dan minta tebusan."
    )
    values = build_field_values(ticket, prepared_by="Andi")
    combined = values["kronologi_line1"] + values["kronologi_line2"] + values["kronologi_line3"]
    assert "Pengguna:" not in combined
    assert "Asisten:" not in combined
    assert "terenkripsi" in combined


@pytest.mark.parametrize("n_lines", [1, 2, 3])
def test_wrap_lines_respects_char_budget_and_word_boundaries(n_lines):
    text = "kata " * 60
    lines = _wrap_lines(text, n_lines, chars_per_line=50)
    assert len(lines) == n_lines
    for line in lines:
        assert len(line) <= 50
        assert not line.startswith(" ")


def test_wrap_lines_truncates_with_ellipsis_when_too_long():
    text = "x " * 200
    lines = _wrap_lines(text, 1, chars_per_line=20)
    assert lines[0].endswith("…")
    assert len(lines[0]) <= 20


def test_build_field_values_shrinks_font_for_long_signature_name():
    values = build_field_values(_base_ticket(), prepared_by="Tim Keamanan Siber Pusdatin")
    value = values["ttd_penerima_nama"]
    assert isinstance(value, tuple)
    text, font_id, size = value
    assert text == "Tim Keamanan Siber Pusdatin"
    assert font_id == "/Helv"
    assert size < 10.0


def test_build_field_values_keeps_plain_string_for_short_signature_name():
    values = build_field_values(_base_ticket(reporter_name="Andi"), prepared_by="Andi")
    assert values["ttd_pelapor_nama"] == "Andi"


def test_fit_font_size_returns_max_for_empty_text():
    assert _fit_font_size("", 100) == 10.0


def test_fit_font_size_shrinks_for_long_text_in_narrow_box():
    size = _fit_font_size("Tim Keamanan Siber Pusdatin", 102.8)
    assert 6.0 <= size < 10.0


def test_fit_font_size_never_below_minimum():
    size = _fit_font_size("Teks yang sangat sangat sangat panjang sekali", 20)
    assert size == 6.0


def test_strip_chat_prefixes_keeps_plain_text_unchanged():
    assert _strip_chat_prefixes("Deskripsi biasa tanpa transkrip.") == "Deskripsi biasa tanpa transkrip."


def test_strip_chat_prefixes_extracts_last_user_message():
    text = "Pengguna: halo Asisten: ada yang bisa dibantu? Pengguna: laptop saya kena ransomware"
    assert _strip_chat_prefixes(text) == "laptop saya kena ransomware"


class TestSummarizeForReport:
    """Test summarize_for_report langsung (LLM di-mock, tidak ada network call nyata)."""

    def test_returns_empty_when_both_inputs_empty(self):
        assert summarize_for_report("", "") == {"kronologi": "", "containment": "", "recovery": ""}

    def test_falls_back_when_llm_client_unavailable(self):
        with patch.object(prg, "create_llm_client", side_effect=EnvironmentError("no API key")):
            result = summarize_for_report("Deskripsi insiden.", "Isolasi host segera.")
        assert result["kronologi"] == "Deskripsi insiden."
        assert result["containment"] or result["recovery"]

    def test_parses_llm_json_response(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"kronologi": "Ringkas.", "containment": "Isolasi.", "recovery": "Restore."}'
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        with patch.object(prg, "create_llm_client", return_value=mock_client):
            result = summarize_for_report("transkrip panjang...", "rekomendasi panjang...")
        assert result == {"kronologi": "Ringkas.", "containment": "Isolasi.", "recovery": "Restore."}

    def test_falls_back_when_llm_returns_invalid_json(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "bukan json"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        with patch.object(prg, "create_llm_client", return_value=mock_client):
            result = summarize_for_report("Deskripsi insiden.", "Isolasi host segera.")
        assert result["kronologi"] == "Deskripsi insiden."
