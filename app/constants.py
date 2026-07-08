"""Konstanta aplikasi helpdesk keamanan siber — satu sumber kebenaran.

Semua magic string untuk status tiket, severity, eskalasi, dan badge mapping
dikonsolidasikan di sini agar tidak tersebar di banyak file.
"""

# ---------------------------------------------------------------------------
# Status tiket
# ---------------------------------------------------------------------------

STATUS_PENDING_REVIEW = "PENDING_REVIEW"
STATUS_IN_PROGRESS    = "IN_PROGRESS"
STATUS_RESOLVED       = "RESOLVED"
STATUS_CLOSED         = "CLOSED"

TICKET_STATUSES: list[str] = [
    STATUS_PENDING_REVIEW,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
]

# ---------------------------------------------------------------------------
# Tingkat keparahan (severity)
# ---------------------------------------------------------------------------

SEVERITY_KRITIS        = "Kritis"
SEVERITY_TINGGI        = "Tinggi"
SEVERITY_SEDANG        = "Sedang"
SEVERITY_RENDAH        = "Rendah"
SEVERITY_INFORMASIONAL = "Informasional"

SEVERITY_LEVELS: list[str] = [
    SEVERITY_KRITIS,
    SEVERITY_TINGGI,
    SEVERITY_SEDANG,
    SEVERITY_RENDAH,
    SEVERITY_INFORMASIONAL,
]

# ---------------------------------------------------------------------------
# Tingkat eskalasi
# ---------------------------------------------------------------------------

ESCALATION_SEGERA   = "Segera"
ESCALATION_MENDESAK = "Mendesak"
ESCALATION_STANDAR  = "Standar"
ESCALATION_RUTIN    = "Rutin"

ESCALATION_LEVELS: list[str] = [
    ESCALATION_SEGERA,
    ESCALATION_MENDESAK,
    ESCALATION_STANDAR,
    ESCALATION_RUTIN,
]

# ---------------------------------------------------------------------------
# Status badge: status_key → (css_class, label_bahasa_indonesia)
# Dipakai oleh: dashboard/main.py, dashboard/report_generator.py
# ---------------------------------------------------------------------------

STATUS_BADGE: dict[str, tuple[str, str]] = {
    STATUS_PENDING_REVIEW: ("badge-pending",  "Menunggu Tinjauan"),
    STATUS_IN_PROGRESS:    ("badge-progress", "Sedang Ditangani"),
    STATUS_RESOLVED:       ("badge-resolved", "Terselesaikan"),
    STATUS_CLOSED:         ("badge-closed",   "Ditutup"),
}

# Label teks saja (tanpa css class) — berguna untuk laporan dan pesan teks
STATUS_LABEL: dict[str, str] = {k: v for k, (_, v) in STATUS_BADGE.items()}

# ---------------------------------------------------------------------------
# Severity badge: severity_key → css_class
# Dipakai oleh: dashboard/main.py
# ---------------------------------------------------------------------------

SEVERITY_BADGE: dict[str, str] = {
    SEVERITY_KRITIS:        "badge-kritis",
    SEVERITY_TINGGI:        "badge-tinggi",
    SEVERITY_SEDANG:        "badge-sedang",
    SEVERITY_RENDAH:        "badge-rendah",
    SEVERITY_INFORMASIONAL: "badge-info",
}

# Warna hex untuk severity — dipakai oleh report_generator.py (HTML inline style)
SEVERITY_COLOR: dict[str, str] = {
    SEVERITY_KRITIS:        "#dc2626",
    SEVERITY_TINGGI:        "#ea580c",
    SEVERITY_SEDANG:        "#ca8a04",
    SEVERITY_RENDAH:        "#16a34a",
    SEVERITY_INFORMASIONAL: "#2563eb",
}

# ---------------------------------------------------------------------------
# Status labels dengan emoji — dipakai oleh telegram/bot.py (/status handler)
# ---------------------------------------------------------------------------

STATUS_LABEL_TELEGRAM: dict[str, str] = {
    STATUS_PENDING_REVIEW: "⏳ Menunggu Tinjauan",
    STATUS_IN_PROGRESS:    "🔄 Sedang Ditangani",
    STATUS_RESOLVED:       "✅ Terselesaikan",
    STATUS_CLOSED:         "🔒 Ditutup",
}
