"""Template pesan Telegram untuk notifikasi CSIRT dan konfirmasi pelapor."""

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

📎 Detail lengkap tersedia di sistem tiket."""

REPORTER_CONFIRMATION_TEMPLATE = """\
✅ Laporan Anda telah diterima.

📌 Tiket: {ticket_id}
📋 Jenis Insiden: {incident_type} (Kepercayaan: {confidence}%)
⚠️ Tingkat Keparahan: {severity}

🔧 Langkah Mitigasi Awal:
{mitigation_steps}

Tim Keamanan Siber telah diberitahu dan akan menindaklanjuti.
Simpan nomor tiket di atas untuk referensi."""


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
        description_short=description_short[:300] if description_short else "-",
        mitigation_short=mitigation_short[:300] if mitigation_short else "Hubungi tim CSIRT.",
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
        mitigation_steps=mitigation_steps[:500] if mitigation_steps else "Hubungi tim CSIRT secara langsung.",
    )
