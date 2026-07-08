"""Template pesan Telegram untuk notifikasi CSIRT, konfirmasi pelapor, dan update status."""

from app.constants import (
    STATUS_PENDING_REVIEW,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
)

SEVERITY_EMOJI = {
    "Kritis": "🔴",
    "Tinggi": "🟠",
    "Sedang": "🟡",
    "Rendah": "🟢",
    "Informasional": "🔵",
}

CSIRT_ALERT_TEMPLATE = """\
🚨 [{severity}] Insiden Baru — {ticket_id}

📋 Jenis: {incident_type}
⚠️ Keparahan: {severity_emoji} {severity}
👤 Pelapor: {reporter_name}
🕐 Waktu: {timestamp}

📝 Ringkasan:
{description_short}

🔧 Rekomendasi Awal:
{mitigation_short}

📎 Detail lengkap tersedia di sistem tiket"""

REPORTER_CONFIRMATION_TEMPLATE = """\
✅ Laporan Anda telah diterima

📌 Tiket: {ticket_id}
📋 Jenis Insiden: {incident_type} (Kepercayaan: {confidence}%)
⚠️ Tingkat Keparahan: {severity}

🔧 Langkah Mitigasi Awal:
{mitigation_steps}

Tim Keamanan Siber telah diberitahu dan akan menindaklanjuti.
Simpan nomor tiket di atas untuk referensi."""


def _trim_for_telegram(text: str, limit: int) -> str:
    value = (text or "").strip()
    if not value:
        return "-"
    if len(value) <= limit:
        return value

    clipped = value[:limit].rstrip()
    last_break = max(clipped.rfind("\n"), clipped.rfind(". "), clipped.rfind("; "), clipped.rfind(", "))
    if last_break >= int(limit * 0.55):
        clipped = clipped[: last_break + 1].rstrip()
    return clipped.rstrip(" .,;:") + "..."


def format_csirt_alert(
    ticket_id: str,
    incident_type: str,
    severity: str,
    reporter_name: str,
    timestamp: str,
    description_short: str,
    mitigation_short: str,
) -> str:
    emoji = SEVERITY_EMOJI.get(severity, "⚠️")
    return CSIRT_ALERT_TEMPLATE.format(
        ticket_id=ticket_id,
        incident_type=incident_type,
        severity=severity,
        severity_emoji=emoji,
        reporter_name=reporter_name or "Tidak diketahui",
        timestamp=timestamp,
        description_short=_trim_for_telegram(description_short, 280),
        mitigation_short=_trim_for_telegram(mitigation_short or "Hubungi tim CSIRT.", 280),
    )


_STATUS_INFO: dict[str, tuple[str, str, str]] = {
    STATUS_PENDING_REVIEW: ("⏳", "Menunggu Tinjauan",  "Laporan Anda sedang dalam antrian tinjauan Tim Keamanan Siber dan PDP"),
    STATUS_IN_PROGRESS:    ("🔄", "Sedang Ditangani",   "Tim Keamanan Siber dan PDP sedang aktif menangani insiden Anda"),
    STATUS_RESOLVED:       ("✅", "Terselesaikan",       "Insiden Anda telah berhasil ditangani oleh Tim Keamanan Siber dan PDP"),
    STATUS_CLOSED:         ("🔒", "Ditutup",             "Tiket ini telah ditutup. Hubungi Tim Keamanan Siber dan PDP jika masalah muncul kembali"),
}

STATUS_UPDATE_TEMPLATE = """\
📋 Update Status Tiket Anda

🔖 Tiket  : {ticket_id}
📌 Status : {emoji} {label}
🕐 Waktu  : {updated_at}

{detail_message}

Gunakan /status {ticket_id} untuk cek status kapan saja."""


def format_status_update(ticket_id: str, new_status: str, updated_at: str) -> str:
    """Format pesan notifikasi update status tiket ke pelapor."""
    emoji, label, detail = _STATUS_INFO.get(
        new_status, ("📋", new_status, "Status tiket Anda telah diperbarui.")
    )
    return STATUS_UPDATE_TEMPLATE.format(
        ticket_id=ticket_id,
        emoji=emoji,
        label=label,
        updated_at=updated_at,
        detail_message=detail,
    )


def format_reporter_confirmation(
    ticket_id: str,
    incident_type: str,
    severity: str,
    confidence: float,
    mitigation_steps: str,
) -> str:
    confidence_pct = int(round(confidence * 100))
    return REPORTER_CONFIRMATION_TEMPLATE.format(
        ticket_id=ticket_id,
        incident_type=incident_type,
        severity=severity,
        confidence=confidence_pct,
        mitigation_steps=_trim_for_telegram(
            mitigation_steps or "Hubungi Tim Keamanan Siber dan PDP secara langsung.",
            1600,
        ),
    )
