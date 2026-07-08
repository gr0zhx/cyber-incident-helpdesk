"""Generator laporan insiden sebagai PDF asli, mengisi field fillable pada
template `assets/formulir_template.pdf` (hasil `scripts/build_pdf_form_template.py`)
yang meniru persis Formulir No. 46.5/TI.100/A.8/01/2026 — Pusdatin Kementan.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pypdf import PdfReader, PdfWriter

from app.utils.llm_client import create_llm_client
from app.utils.llm_parser import parse_llm_json
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

TEMPLATE_PDF = Path(__file__).parent / "assets" / "formulir_template.pdf"
_SUMMARY_MODEL = "gpt-4o"

_WIB = timezone(timedelta(hours=7))

_HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_BULAN_ID = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
]


def _fmt_tanggal_id(dt: datetime) -> str:
    """Format tanggal dengan nama bulan Indonesia (strftime %b bergantung locale server,
    yang seringkali default ke Inggris — jadi diformat manual di sini)."""
    return f"{dt.day:02d} {_BULAN_ID[dt.month - 1]} {dt.year}"

# incident_type (VALID_TYPES di app/agents/identifier.py) -> nama checkbox kategori resmi
_KATEGORI_MAP = {
    "Malware": "kategori_malware_virus",
    "Ransomware": "kategori_malware_virus",
    "Web Defacement": "kategori_serangan_web",
    "DDoS": "kategori_ketersediaan",
    "Akses Tidak Sah": "kategori_akses_ilegal",
    "Kebocoran Data": "kategori_kebocoran_data",
    # "Phishing" dan "Lainnya" tidak punya kategori resmi persis -> masuk "Lainnya"
}

# severity (VALID_SEVERITIES) -> nama checkbox severity resmi
_SEVERITY_MAP = {
    "Kritis": "severity_critical",
    "Tinggi": "severity_high",
    "Sedang": "severity_medium",
    "Rendah": "severity_low",
    "Informasional": "severity_low",  # tidak ada level resmi setara -> LOW (paling mendekati)
}

_MEDIA_MAP = {
    "Email": "media_email",
    "Telepon": "media_telepon",
    "WhatsApp": "media_whatsapp",
    "Datang Langsung": "media_datang_langsung",
    "Sistem Tiket": "media_sistem_tiket",
}

# status internal -> checkbox Status Insiden resmi (OPEN/MONITORING/CLOSED)
_STATUS_MAP = {
    "PENDING_REVIEW": "status_open",
    "IN_PROGRESS": "status_open",
    "RESOLVED": "status_monitoring",
    "CLOSED": "status_closed",
    "REJECTED": "status_closed",
}

_LINE_CHAR_BUDGET = 85  # kapasitas nyata 1 baris (~417pt lebar) pada Helvetica 10pt —
                         # diukur dari lebar teks sesungguhnya, bukan jumlah titik-titik asli


def _parse_dt(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        dt = val
    else:
        try:
            dt = datetime.fromisoformat(str(val))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_WIB)


def _wrap_lines(text: str, n_lines: int, chars_per_line: int = _LINE_CHAR_BUDGET) -> list[str]:
    """Bungkus teks ke maksimum n_lines baris, masing-masing <= chars_per_line,
    tanpa memotong kata (kecuali kata itu sendiri lebih panjang dari satu baris)."""
    text = " ".join(text.split())
    lines: list[str] = []
    remaining = text
    for _ in range(n_lines):
        if not remaining:
            lines.append("")
            continue
        if len(remaining) <= chars_per_line:
            lines.append(remaining)
            remaining = ""
            continue
        cut = remaining.rfind(" ", 0, chars_per_line)
        if cut <= 0:
            cut = chars_per_line
        lines.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        last = lines[-1]
        max_len = chars_per_line - 1
        if len(last) > max_len:
            last = last[:max_len].rstrip()
        lines[-1] = (last + "…") if last else "…"
    return lines


def _strip_chat_prefixes(text: str) -> str:
    """Fallback tanpa LLM: kalau teks berupa transkrip chat ('Pengguna: ... Asisten:
    ...'), ambil pesan pelapor TERAKHIR saja, bukan seluruh transkrip mentah."""
    if "Pengguna:" not in text:
        return text
    last_chunk = text.split("Pengguna:")[-1]
    return last_chunk.split("Asisten:")[0].strip() or text


def _fallback_summary(description: str, mitigation: str) -> dict[str, str]:
    """Ringkasan tanpa LLM (dipakai kalau panggilan LLM gagal/timeout/tidak ada API
    key) — tetap lebih baik daripada dump mentah, walau kurang natural dibanding hasil LLM."""
    kronologi = _strip_chat_prefixes(description)
    mid = len(mitigation) // 2
    split_at = mitigation.rfind(" ", 0, mid) if mid > 0 else -1
    if split_at <= 0:
        split_at = mid
    return {
        "kronologi": kronologi,
        "containment": mitigation[:split_at].strip(),
        "recovery": mitigation[split_at:].strip(),
    }


async def _call_summary_llm(description: str, mitigation: str) -> dict[str, str]:
    client = create_llm_client()
    prompt = (
        load_prompt("report_summary")
        .replace("{description}", description or "-")
        .replace("{mitigation}", mitigation or "-")
    )
    response = await client.chat.completions.create(
        model=_SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=300,
        response_format={"type": "json_object"},
        timeout=15.0,
    )
    parsed = parse_llm_json(response.choices[0].message.content)
    if not parsed:
        raise ValueError("LLM tidak mengembalikan JSON valid untuk ringkasan laporan.")
    return {
        "kronologi": str(parsed.get("kronologi") or "").strip(),
        "containment": str(parsed.get("containment") or "").strip(),
        "recovery": str(parsed.get("recovery") or "").strip(),
    }


def summarize_for_report(description: str, mitigation: str) -> dict[str, str]:
    """Ringkas kronologi & rekomendasi mitigasi jadi teks singkat khusus formulir PDF
    (kolomnya garis cetak fisik, bukan kotak teks bebas) via satu panggilan LLM.
    Fallback ke heuristik sederhana kalau LLM gagal/tidak tersedia."""
    if not description and not mitigation:
        return {"kronologi": "", "containment": "", "recovery": ""}
    try:
        return asyncio.run(_call_summary_llm(description, mitigation))
    except Exception:
        logger.warning("Ringkasan laporan PDF via LLM gagal, pakai fallback heuristik.", exc_info=True)
        return _fallback_summary(description, mitigation)


def _cia_checkbox(name_terjaga: str, name_negatif: str, value: Optional[bool]) -> dict[str, str]:
    if value is None:
        return {}
    return {name_negatif if value else name_terjaga: "/Yes"}


# Lebar field tanda tangan (poin PDF) — dipakai untuk menghitung ukuran font yang muat.
# pypdf TIDAK auto-shrink berdasarkan lebar teks (auto-size bawaannya cuma ikut tinggi
# kotak), jadi field yang isinya bisa panjang (nama tim/petugas) perlu dihitung manual.
_SIGNATURE_FIELD_WIDTH = {
    "ttd_pelapor_nama": 62.6,
    "ttd_penerima_nama": 102.8,
    "ttd_ketua_csirt_nama": 113.7,
}
_AVG_CHAR_WIDTH_EM = 0.52  # diukur dari lebar teks sungguhan Helvetica (~0.485em) + margin tipis
_DEFAULT_FONT_SIZE = 10.0  # harus sinkron dengan FONT_SIZE di scripts/build_pdf_form_template.py


def _fit_font_size(text: str, width_pt: float, max_size: float = _DEFAULT_FONT_SIZE, min_size: float = 6.0) -> float:
    """Hitung font size terbesar (dibulatkan 0.5pt) yang membuat `text` muat dalam
    `width_pt`, dibatasi [min_size, max_size]."""
    if not text:
        return max_size
    ideal = width_pt / (len(text) * _AVG_CHAR_WIDTH_EM)
    size = max(min_size, min(max_size, ideal))
    return round(size * 2) / 2


def build_field_values(ticket: dict, prepared_by: str) -> dict[str, Any]:
    """Petakan dict data tiket ke nama field PDF sesuai `scripts/build_pdf_form_template.py`.

    Sebagian besar value berupa str; field tanda tangan bisa berupa tuple
    (teks, font_id, font_size) untuk override ukuran font per pypdf's tuple convention.
    """
    values: dict[str, Any] = {}

    values["nama_pelapor"] = ticket.get("reporter_name") or ""
    values["unit_kerja"] = ticket.get("reporter_department") or ticket.get("reporter_unit") or ""
    values["no_telp_hp"] = ticket.get("reporter_contact") or ""

    created_at = _parse_dt(ticket.get("created_at"))
    if created_at:
        values["tanggal_jam_lapor"] = f"{_fmt_tanggal_id(created_at)} {created_at.strftime('%H:%M')} WIB"

    media = ticket.get("media_pelaporan") or ""
    if media in _MEDIA_MAP:
        values[_MEDIA_MAP[media]] = "/Yes"

    incident_time = _parse_dt(ticket.get("incident_time"))
    if incident_time:
        values["waktu_hari"] = _HARI_ID[incident_time.weekday()]
        values["waktu_tanggal"] = incident_time.strftime("%d-%m-%Y")
        values["waktu_jam"] = incident_time.strftime("%H:%M")

    affected_asset = ticket.get("affected_asset") or ""
    values["lokasi_kejadian"] = _wrap_lines(affected_asset, 1)[0] if affected_asset else ""

    description = ticket.get("description_sanitized") or ""
    mitigation = ticket.get("mitigation_recommendation") or ""
    containment_manual = ticket.get("containment_action") or ""
    recovery_manual = ticket.get("recovery_action") or ""
    summary = summarize_for_report(description, mitigation)

    kronologi = summary["kronologi"] or _strip_chat_prefixes(description)
    k1, k2, k3 = _wrap_lines(kronologi, 3) if kronologi else ("", "", "")
    values["kronologi_line1"] = k1
    values["kronologi_line2"] = k2
    values["kronologi_line3"] = k3

    incident_type = ticket.get("incident_type") or ""
    kategori_field = _KATEGORI_MAP.get(incident_type)
    if kategori_field:
        values[kategori_field] = "/Yes"
    else:
        values["kategori_lainnya"] = "/Yes"
        values["kategori_lainnya_text"] = incident_type[:40]

    severity = ticket.get("severity") or ""
    severity_field = _SEVERITY_MAP.get(severity)
    if severity_field:
        values[severity_field] = "/Yes"

    values.update(_cia_checkbox("cia_conf_terjaga", "cia_conf_terlanggar", ticket.get("cia_confidentiality")))
    values.update(_cia_checkbox("cia_integ_terjaga", "cia_integ_terlanggar", ticket.get("cia_integrity")))
    values.update(_cia_checkbox("cia_avail_terjaga", "cia_avail_terganggu", ticket.get("cia_availability")))

    containment = containment_manual or summary["containment"]
    recovery = recovery_manual or summary["recovery"]
    c1, c2 = _wrap_lines(containment, 2) if containment else ("", "")
    r1, r2 = _wrap_lines(recovery, 2) if recovery else ("", "")
    values["containment_line1"] = c1
    values["containment_line2"] = c2
    values["recovery_line1"] = r1
    values["recovery_line2"] = r2

    resolved_at = _parse_dt(ticket.get("resolved_at")) or _parse_dt(ticket.get("closed_at"))
    if resolved_at:
        values["penyelesaian_tanggal"] = resolved_at.strftime("%d-%m-%Y")
        values["penyelesaian_jam"] = resolved_at.strftime("%H:%M")
        if created_at:
            hours = round((resolved_at - created_at).total_seconds() / 3600)
            values["total_durasi_jam"] = str(max(hours, 0))

    status_field = _STATUS_MAP.get(ticket.get("status") or "")
    if status_field:
        values[status_field] = "/Yes"

    for field_name, text in (
        ("ttd_pelapor_nama", ticket.get("reporter_name") or ""),
        ("ttd_penerima_nama", prepared_by),
        ("ttd_ketua_csirt_nama", ticket.get("assigned_to") or ""),
    ):
        size = _fit_font_size(text, _SIGNATURE_FIELD_WIDTH[field_name])
        values[field_name] = (text, "/Helv", size) if size < _DEFAULT_FONT_SIZE else text
    if created_at:
        values["ttd_pelapor_tgl"] = created_at.strftime("%d-%m-%Y")
        values["ttd_penerima_tgl"] = created_at.strftime("%d-%m-%Y")
    reviewed_at = _parse_dt(ticket.get("reviewed_at"))
    if reviewed_at:
        values["ttd_ketua_csirt_tgl"] = reviewed_at.strftime("%d-%m-%Y")

    return values


_TD_RE = re.compile(rb"[\d.]+\s+[\d.]+\s+Td")
_TF_RE = re.compile(rb"/Helv\s+([\d.]+)\s+Tf")


def _recenter_text_field_appearances(writer: PdfWriter) -> None:
    """pypdf's built-in appearance generator posisikan baseline teks dengan rumus
    (tinggi_kotak - 1 - font_size) — untuk kotak pendek (~11pt) hasilnya nempel ke
    bawah, bukan di tengah vertikal. Field pendek/isolasi (mis. nama di kolom tanda
    tangan) jadi kelihatan tidak center. Di sini baseline dihitung ulang supaya
    benar-benar center secara vertikal, tanpa mengubah font/clip/resource lainnya."""
    for page in writer.pages:
        if "/Annots" not in page:
            continue
        for annot_ref in page["/Annots"]:
            annot = annot_ref.get_object()
            if annot.get("/FT") != "/Tx":
                continue
            ap = annot.get("/AP")
            if not ap or "/N" not in ap:
                continue
            stream_obj = ap["/N"].get_object()
            data = stream_obj.get_data()
            tf_match = _TF_RE.search(data)
            if not tf_match:
                continue
            font_size = float(tf_match.group(1))
            rect = annot["/Rect"]
            height = float(rect[3]) - float(rect[1])
            baseline_y = max(0.5, (height - font_size) / 2 + font_size * 0.18)
            new_data, n = _TD_RE.subn(f"2 {baseline_y:.2f} Td".encode("ascii"), data, count=1)
            if n:
                stream_obj.set_data(new_data)


def generate_report_pdf(ticket: dict, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> bytes:
    """Generate laporan insiden sebagai PDF asli (fillable form Kementan terisi).

    Args:
        ticket: dict data tiket (lihat ReportService.generate untuk struktur field).
        prepared_by: Nama petugas/tim yang menyiapkan laporan.

    Returns:
        Bytes PDF siap diunduh.
    """
    reader = PdfReader(str(TEMPLATE_PDF))
    writer = PdfWriter()
    writer.append(reader)

    values = build_field_values(ticket, prepared_by)
    for page in writer.pages:
        writer.update_page_form_field_values(page, values, auto_regenerate=False)
    _recenter_text_field_appearances(writer)

    from io import BytesIO

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_report_filename(ticket: dict) -> str:
    tid = ticket.get("ticket_id", "UNKNOWN")
    date = datetime.now().strftime("%Y%m%d")
    return f"Laporan-Insiden-{tid}-{date}.pdf"
