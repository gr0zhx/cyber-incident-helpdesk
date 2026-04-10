"""Generator laporan insiden keamanan siber dalam format HTML.

Laporan yang dihasilkan bisa didownload dan dicetak sebagai PDF via browser.
"""
from datetime import datetime, timezone
from typing import Any

from app.constants import SEVERITY_COLOR, STATUS_LABEL

_SEVERITY_COLOR = SEVERITY_COLOR
_STATUS_LABEL   = STATUS_LABEL

_ESCALATION_LABEL = {
    "Segera":    "🔴 Segera",
    "Mendesak":  "🟠 Mendesak",
    "Standar":   "🟡 Standar",
    "Rutin":     "🟢 Rutin",
}


def _fmt_dt(dt_str: str | None) -> str:
    if not dt_str:
        return "—"
    return str(dt_str)[:16].replace("T", " ") + " UTC"


def _safe(val: Any, fallback: str = "—") -> str:
    if val is None or val == "":
        return fallback
    return str(val)


def generate_report_html(ticket: dict, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> str:
    """Generate laporan insiden sebagai string HTML.

    Args:
        ticket: dict data tiket dari API (TicketOut schema).
        prepared_by: Nama petugas/tim yang menyiapkan laporan.

    Returns:
        String HTML laporan insiden yang siap didownload / dicetak.
    """
    tid         = _safe(ticket.get("ticket_id"))
    inc_type    = _safe(ticket.get("incident_type"))
    severity    = _safe(ticket.get("severity"))
    status      = _STATUS_LABEL.get(ticket.get("status", ""), _safe(ticket.get("status")))
    escalation  = _ESCALATION_LABEL.get(ticket.get("escalation_level", ""), _safe(ticket.get("escalation_level")))
    reporter    = _safe(ticket.get("reporter_name")) or _safe(ticket.get("reporter_id"))
    assigned_to = _safe(ticket.get("assigned_to"))
    description = _safe(ticket.get("description_sanitized"), "Tidak ada deskripsi.")
    mitigation  = _safe(ticket.get("mitigation_recommendation"), "Belum ada rekomendasi mitigasi.")
    confidence  = ticket.get("confidence_score") or 0.0
    created_at  = _fmt_dt(str(ticket.get("created_at", "")))
    updated_at  = _fmt_dt(str(ticket.get("updated_at", "")))
    reviewed_at = _fmt_dt(str(ticket.get("reviewed_at", "")))
    resolved_at = _fmt_dt(str(ticket.get("resolved_at", "")))

    sev_color   = _SEVERITY_COLOR.get(severity, "#6b7280")
    report_date = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    # --- Konversi mitigation markdown sederhana ke paragraf ---
    mitigation_html = "<br>".join(
        f"<p>{line}</p>" if line.strip() else ""
        for line in mitigation.split("\n")
    )

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Laporan Insiden — {tid}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 13px;
      color: #1f2937;
      background: #fff;
      padding: 40px;
      max-width: 900px;
      margin: auto;
    }}

    /* Header */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 3px solid #1d4ed8;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }}
    .header-left h1 {{ font-size: 22px; color: #1d4ed8; }}
    .header-left p  {{ font-size: 12px; color: #6b7280; margin-top: 4px; }}
    .header-right   {{ text-align: right; font-size: 12px; color: #6b7280; }}
    .header-right strong {{ font-size: 14px; color: #1f2937; display: block; margin-bottom: 4px; }}

    /* Badge */
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      color: #fff;
    }}

    /* Summary box */
    .summary-box {{
      background: #eff6ff;
      border-left: 4px solid #1d4ed8;
      border-radius: 4px;
      padding: 16px 20px;
      margin-bottom: 24px;
    }}
    .summary-box h2 {{ font-size: 14px; color: #1d4ed8; margin-bottom: 10px; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }}
    .summary-item label {{ display: block; font-size: 11px; color: #6b7280; margin-bottom: 2px; }}
    .summary-item span  {{ font-size: 13px; font-weight: 600; }}

    /* Section */
    .section {{ margin-bottom: 24px; }}
    .section h2 {{
      font-size: 13px;
      font-weight: 700;
      color: #1d4ed8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid #dbeafe;
      padding-bottom: 6px;
      margin-bottom: 12px;
    }}

    /* Table */
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ text-align: left; padding: 8px 12px; border: 1px solid #e5e7eb; }}
    th {{ background: #f3f4f6; font-weight: 600; color: #374151; width: 30%; }}
    td {{ color: #1f2937; }}

    /* Description & mitigation */
    .text-block {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      padding: 14px 16px;
      line-height: 1.7;
      white-space: pre-wrap;
      font-size: 12.5px;
    }}
    .text-block p {{ margin-bottom: 6px; }}

    /* Timeline */
    .timeline {{ list-style: none; padding: 0; }}
    .timeline li {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px dashed #e5e7eb;
    }}
    .timeline li:last-child {{ border-bottom: none; }}
    .tl-dot {{
      width: 10px; height: 10px;
      border-radius: 50%;
      background: #1d4ed8;
      margin-top: 3px;
      flex-shrink: 0;
    }}
    .tl-dot.done  {{ background: #16a34a; }}
    .tl-dot.empty {{ background: #d1d5db; }}
    .tl-label {{ font-size: 12px; }}
    .tl-label strong {{ display: block; }}
    .tl-label span   {{ color: #6b7280; font-size: 11px; }}

    /* Signature */
    .signature-block {{
      margin-top: 40px;
      display: flex;
      justify-content: space-between;
    }}
    .signature-item {{ text-align: center; width: 200px; }}
    .signature-item .line {{
      border-bottom: 1px solid #374151;
      height: 50px;
      margin-bottom: 6px;
    }}
    .signature-item p {{ font-size: 11px; color: #374151; }}

    /* Footer */
    .footer {{
      margin-top: 32px;
      padding-top: 12px;
      border-top: 1px solid #e5e7eb;
      font-size: 11px;
      color: #9ca3af;
      display: flex;
      justify-content: space-between;
    }}

    @media print {{
      body {{ padding: 20px; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <h1>LAPORAN INSIDEN KEAMANAN SIBER</h1>
      <p>Pusat Data dan Sistem Informasi (Pusdatin) — Kementerian Pertanian RI</p>
    </div>
    <div class="header-right">
      <strong>{tid}</strong>
      Tanggal Laporan:<br>{report_date}
    </div>
  </div>

  <!-- SUMMARY BOX -->
  <div class="summary-box">
    <h2>Ringkasan Eksekutif</h2>
    <div class="summary-grid">
      <div class="summary-item">
        <label>Jenis Insiden</label>
        <span>{inc_type}</span>
      </div>
      <div class="summary-item">
        <label>Tingkat Keparahan</label>
        <span>
          <span class="badge" style="background:{sev_color}">{severity}</span>
        </span>
      </div>
      <div class="summary-item">
        <label>Status</label>
        <span>{status}</span>
      </div>
      <div class="summary-item">
        <label>Tingkat Eskalasi</label>
        <span>{escalation}</span>
      </div>
      <div class="summary-item">
        <label>Kepercayaan Klasifikasi</label>
        <span>{confidence:.0%}</span>
      </div>
      <div class="summary-item">
        <label>Ditangani Oleh</label>
        <span>{assigned_to}</span>
      </div>
    </div>
  </div>

  <!-- INFORMASI PELAPOR -->
  <div class="section">
    <h2>Informasi Pelapor</h2>
    <table>
      <tr><th>Nama Pelapor</th><td>{reporter}</td></tr>
      <tr><th>ID Pelapor (Telegram)</th><td>{_safe(ticket.get("reporter_id"))}</td></tr>
      <tr><th>Waktu Pelaporan</th><td>{created_at}</td></tr>
    </table>
  </div>

  <!-- DESKRIPSI INSIDEN -->
  <div class="section">
    <h2>Deskripsi Insiden</h2>
    <div class="text-block">{description}</div>
  </div>

  <!-- REKOMENDASI MITIGASI -->
  <div class="section">
    <h2>Rekomendasi Mitigasi</h2>
    <div class="text-block">{mitigation_html}</div>
  </div>

  <!-- TIMELINE -->
  <div class="section">
    <h2>Timeline Penanganan</h2>
    <ul class="timeline">
      <li>
        <div class="tl-dot done"></div>
        <div class="tl-label">
          <strong>Laporan Diterima</strong>
          <span>{created_at}</span>
        </div>
      </li>
      <li>
        <div class="tl-dot {'done' if reviewed_at != '—' else 'empty'}"></div>
        <div class="tl-label">
          <strong>Ditinjau Tim CSIRT</strong>
          <span>{reviewed_at}</span>
        </div>
      </li>
      <li>
        <div class="tl-dot {'done' if resolved_at != '—' else 'empty'}"></div>
        <div class="tl-label">
          <strong>Insiden Terselesaikan</strong>
          <span>{resolved_at}</span>
        </div>
      </li>
      <li>
        <div class="tl-dot {'done' if updated_at != '—' else 'empty'}"></div>
        <div class="tl-label">
          <strong>Pembaruan Terakhir</strong>
          <span>{updated_at}</span>
        </div>
      </li>
    </ul>
  </div>

  <!-- TANDA TANGAN -->
  <div class="signature-block">
    <div class="signature-item">
      <div class="line"></div>
      <p><strong>Disiapkan oleh</strong><br>{prepared_by}</p>
    </div>
    <div class="signature-item">
      <div class="line"></div>
      <p><strong>Disetujui oleh</strong><br>Kepala Tim Keamanan Siber</p>
    </div>
    <div class="signature-item">
      <div class="line"></div>
      <p><strong>Diketahui oleh</strong><br>Kepala Pusdatin Kementan</p>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <span>Dokumen ini bersifat <strong>RAHASIA</strong> — hanya untuk penggunaan internal Pusdatin Kementan.</span>
    <span>Digenerate otomatis oleh Sistem Helpdesk Keamanan Siber</span>
  </div>

</body>
</html>"""


def generate_report_filename(ticket: dict) -> str:
    """Nama file untuk download."""
    tid  = ticket.get("ticket_id", "UNKNOWN")
    date = datetime.now().strftime("%Y%m%d")
    return f"Laporan-Insiden-{tid}-{date}.html"
