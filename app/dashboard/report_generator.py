"""Generator laporan insiden keamanan informasi.

Mengikuti format Formulir No. 46.5/TI.100/A.8/01/2026 — Pusdatin Kementan.
Struktur: Bagian A (Pelapor) · B (Deskripsi) · C (Triase CIA) · D (Penanganan) · E (Pengesahan)
"""
import html as _html
from datetime import datetime, timezone
from typing import Any


def _safe(val: Any, fallback: str = "—") -> str:
    if val is None or val == "":
        return fallback
    return _html.escape(str(val))


def _fmt_dt(val: Any) -> str:
    if not val:
        return "—"
    s = str(val)[:16].replace("T", " ")
    return s + " WIB" if s != "—" else "—"


def _cia_row(label: str, checked: bool | None, desc: str) -> str:
    mark = "&#10003;" if checked else ""
    box_style = (
        "background:#1d4ed8;color:white;"
        if checked else
        "background:#f3f4f6;color:#9ca3af;"
    )
    return (
        f"<tr>"
        f"<td style='width:30%;font-weight:600;'>{_html.escape(label)}</td>"
        f"<td style='width:8%;text-align:center;'>"
        f"  <span style='display:inline-block;width:18px;height:18px;border:2px solid #1d4ed8;"
        f"  border-radius:3px;font-size:12px;line-height:16px;text-align:center;{box_style}'>"
        f"  {mark}</span></td>"
        f"<td style='color:#6b7280;font-size:12px;'>{_html.escape(desc)}</td>"
        f"</tr>"
    )


def _tl_row(label: str, dt_str: str) -> str:
    done = dt_str != "—"
    dot_color = "#16a34a" if done else "#d1d5db"
    return (
        f"<li style='display:flex;align-items:flex-start;gap:12px;"
        f"padding:8px 0;border-bottom:1px dashed #e5e7eb;'>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:{dot_color};"
        f"flex-shrink:0;margin-top:3px;display:inline-block;'></span>"
        f"<span style='font-size:12px;'><strong>{_html.escape(label)}</strong>"
        f"<span style='display:block;color:#6b7280;font-size:11px;'>{_html.escape(dt_str)}</span>"
        f"</span></li>"
    )


def generate_report_html(ticket: dict, prepared_by: str = "Tim Keamanan Siber Pusdatin") -> str:
    """Generate laporan insiden sebagai HTML sesuai formulir resmi Bagian A–E.

    Args:
        ticket: dict data tiket.
        prepared_by: Nama petugas/tim yang menyiapkan laporan.

    Returns:
        String HTML laporan insiden.
    """
    # ── Core fields ──────────────────────────────────────────────────────────
    tid             = _safe(ticket.get("ticket_id"))
    inc_type        = _safe(ticket.get("incident_type"))
    severity        = _safe(ticket.get("severity"))
    escalation      = _safe(ticket.get("escalation_level"))
    reporter        = _safe(ticket.get("reporter_name"))
    reporter_unit   = _safe(ticket.get("reporter_department") or ticket.get("reporter_unit"))
    reporter_contact= _safe(ticket.get("reporter_contact"))
    media_pelaporan = _safe(ticket.get("media_pelaporan"))
    incident_time   = _fmt_dt(ticket.get("incident_time"))
    affected_asset  = _safe(ticket.get("affected_asset"))
    assigned_to     = _safe(ticket.get("assigned_to"))
    description     = _safe(ticket.get("description_sanitized"), "Tidak ada deskripsi.")
    mitigation      = _safe(ticket.get("mitigation_recommendation"), "Belum ada rekomendasi.")
    containment     = _safe(ticket.get("containment_action"))
    recovery        = _safe(ticket.get("recovery_action"))
    created_at      = _fmt_dt(ticket.get("created_at"))
    reviewed_at     = _fmt_dt(ticket.get("reviewed_at"))
    resolved_at     = _fmt_dt(ticket.get("resolved_at"))
    closed_at       = _fmt_dt(ticket.get("closed_at"))
    report_date     = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M WIB")

    cia_c = ticket.get("cia_confidentiality")
    cia_i = ticket.get("cia_integrity")
    cia_a = ticket.get("cia_availability")

    from app.constants import SEVERITY_COLOR, STATUS_LABEL
    sev_color  = SEVERITY_COLOR.get(severity.split()[0] if severity != "—" else severity, "#6b7280")
    status_lbl = STATUS_LABEL.get(ticket.get("status", ""), _safe(ticket.get("status")))

    tl_html = "".join([
        _tl_row("Laporan Diterima", created_at),
        _tl_row("Ditinjau Tim CSIRT", reviewed_at),
        _tl_row("Insiden Terselesaikan", resolved_at),
        _tl_row("Tiket Ditutup", closed_at),
    ])

    mitigation_paragraphs = "".join(
        f"<p style='margin:0 0 6px;'>{line}</p>" if line.strip() else ""
        for line in mitigation.split("\n")
    )
    if not mitigation_paragraphs.strip():
        mitigation_paragraphs = f"<p style='margin:0;'>{mitigation}</p>"

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Laporan Insiden Keamanan Informasi — {tid}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 12.5px;
      color: #1f2937;
      background: #fff;
      padding: 36px 48px;
      max-width: 900px;
      margin: auto;
    }}
    h1 {{ font-size: 15px; text-transform: uppercase; letter-spacing: .05em; color: #1d4ed8; }}
    h2 {{
      font-size: 12px; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; color: white;
      background: #1d4ed8; padding: 5px 10px; margin: 0;
    }}
    .section {{ margin-bottom: 20px; border: 1px solid #d1d5db; border-radius: 4px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ text-align: left; padding: 7px 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 600; color: #374151; width: 32%; white-space: nowrap; }}
    td {{ color: #1f2937; }}
    tr:last-child th, tr:last-child td {{ border-bottom: none; }}
    .text-block {{
      background: #f9fafb; padding: 12px 14px;
      line-height: 1.7; white-space: pre-wrap; font-size: 12px;
    }}
    .badge {{
      display: inline-block; padding: 2px 10px; border-radius: 999px;
      font-size: 11px; font-weight: 700; color: #fff;
    }}
    .sig-block {{ display: flex; justify-content: space-between; margin-top: 28px; }}
    .sig-item {{ text-align: center; width: 180px; }}
    .sig-line {{ border-bottom: 1px solid #374151; height: 48px; margin-bottom: 5px; }}
    .sig-item p {{ font-size: 11px; color: #374151; line-height: 1.5; }}
    .footer {{
      margin-top: 24px; padding-top: 10px;
      border-top: 1px solid #e5e7eb;
      font-size: 11px; color: #9ca3af;
      display: flex; justify-content: space-between;
    }}
    @media print {{ body {{ padding: 16px; }} }}
  </style>
</head>
<body>

  <!-- KOP SURAT -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              border-bottom:3px solid #1d4ed8;padding-bottom:14px;margin-bottom:20px;">
    <div>
      <div style="font-size:11px;color:#6b7280;font-weight:600;letter-spacing:.04em;
                  text-transform:uppercase;margin-bottom:4px;">
        Pusat Data dan Sistem Informasi (Pusdatin)<br>
        Kementerian Pertanian Republik Indonesia
      </div>
      <h1>Formulir Laporan Insiden Keamanan Informasi</h1>
      <div style="font-size:11px;color:#9ca3af;margin-top:3px;">
        No. 46.5/TI.100/A.8/01/2026
      </div>
    </div>
    <div style="text-align:right;font-size:11px;color:#6b7280;line-height:1.6;">
      <strong style="font-size:15px;color:#1f2937;display:block;font-family:monospace;">
        {tid}
      </strong>
      Tanggal Laporan: {report_date}<br>
      Status: <span class="badge" style="background:{sev_color};">{status_lbl}</span>
    </div>
  </div>

  <!-- BAGIAN A: IDENTITAS PELAPOR -->
  <div class="section">
    <h2>Bagian A — Identitas Pelapor</h2>
    <table>
      <tr><th>Nama Pelapor</th><td>{reporter}</td></tr>
      <tr><th>Unit / Divisi</th><td>{reporter_unit}</td></tr>
      <tr><th>Kontak (HP / Email)</th><td>{reporter_contact}</td></tr>
      <tr><th>Tanggal &amp; Jam Laporan</th><td>{created_at}</td></tr>
      <tr><th>Media Pelaporan</th><td>{media_pelaporan}</td></tr>
    </table>
  </div>

  <!-- BAGIAN B: DESKRIPSI INSIDEN -->
  <div class="section">
    <h2>Bagian B — Deskripsi Insiden</h2>
    <table>
      <tr><th>Jenis Insiden</th>
          <td><strong>{inc_type}</strong>
          &nbsp;<span class="badge" style="background:{sev_color};">{severity}</span></td></tr>
      <tr><th>Waktu Kejadian</th><td>{incident_time}</td></tr>
      <tr><th>Sistem / Aset Terdampak</th><td>{affected_asset}</td></tr>
    </table>
    <div style="padding:10px 12px;background:#f9fafb;border-top:1px solid #e5e7eb;">
      <div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:.05em;margin-bottom:6px;">Kronologi / Deskripsi</div>
      <div class="text-block" style="border:none;padding:0;">{description}</div>
    </div>
  </div>

  <!-- BAGIAN C: TRIASE CIA -->
  <div class="section">
    <h2>Bagian C — Triase (CIA Triad)</h2>
    <table>
      {_cia_row("Kerahasiaan (Confidentiality)", cia_c, "Data sensitif terekspos atau bocor ke pihak tidak berwenang")}
      {_cia_row("Integritas (Integrity)", cia_i, "Data berubah, dimanipulasi, atau tidak dapat dipercaya")}
      {_cia_row("Ketersediaan (Availability)", cia_a, "Layanan atau sistem tidak dapat diakses / terganggu")}
    </table>
    <table style="margin-top:0;border-top:1px solid #e5e7eb;">
      <tr><th>Tingkat Keparahan</th>
          <td><span class="badge" style="background:{sev_color};">{severity}</span></td></tr>
      <tr><th>Level Eskalasi</th><td>{escalation}</td></tr>
    </table>
  </div>

  <!-- BAGIAN D: PENANGANAN -->
  <div class="section">
    <h2>Bagian D — Penanganan Insiden</h2>
    <table>
      <tr><th>Ditangani oleh</th><td>{assigned_to}</td></tr>
      <tr><th>Waktu Tinjauan CSIRT</th><td>{reviewed_at}</td></tr>
      <tr><th>Waktu Penyelesaian</th><td>{resolved_at}</td></tr>
    </table>
    <div style="padding:10px 12px;background:#f9fafb;border-top:1px solid #e5e7eb;">
      <div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:.05em;margin-bottom:6px;">Tindakan Penahanan (Containment)</div>
      <div class="text-block" style="border:none;padding:0;">{containment}</div>
    </div>
    <div style="padding:10px 12px;background:#f9fafb;border-top:1px solid #e5e7eb;">
      <div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:.05em;margin-bottom:6px;">Tindakan Pemulihan (Recovery)</div>
      <div class="text-block" style="border:none;padding:0;">{recovery}</div>
    </div>
    <div style="padding:10px 12px;background:#eff6ff;border-top:1px solid #dbeafe;">
      <div style="font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;
                  letter-spacing:.05em;margin-bottom:6px;">Rekomendasi Mitigasi (AI-Generated)</div>
      <div style="font-size:12px;line-height:1.7;">{mitigation_paragraphs}</div>
    </div>
  </div>

  <!-- TIMELINE -->
  <div class="section">
    <h2>Timeline Penanganan</h2>
    <div style="padding:12px 16px;">
      <ul style="list-style:none;padding:0;">{tl_html}</ul>
    </div>
  </div>

  <!-- BAGIAN E: PENGESAHAN -->
  <div class="section">
    <h2>Bagian E — Pengesahan</h2>
    <div style="padding:16px 20px;">
      <div class="sig-block">
        <div class="sig-item">
          <div class="sig-line"></div>
          <p><strong>Pelapor</strong><br>{reporter}</p>
        </div>
        <div class="sig-item">
          <div class="sig-line"></div>
          <p><strong>Disiapkan oleh</strong><br>{_safe(prepared_by)}</p>
        </div>
        <div class="sig-item">
          <div class="sig-line"></div>
          <p><strong>Diketahui oleh</strong><br>Kepala Pusdatin Kementan</p>
        </div>
      </div>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <span>Dokumen <strong>RAHASIA</strong> — hanya untuk penggunaan internal Pusdatin Kementan.</span>
    <span>Digenerate: {report_date}</span>
  </div>

</body>
</html>"""


def generate_report_filename(ticket: dict) -> str:
    """Nama file untuk download."""
    tid  = ticket.get("ticket_id", "UNKNOWN")
    date = datetime.now().strftime("%Y%m%d")
    return f"Laporan-Insiden-{tid}-{date}.html"
