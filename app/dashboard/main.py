"""Dashboard Admin — Helpdesk Keamanan Siber Pusdatin Kementan.

UI email-like: inbox tiket di kiri, detail + aksi di kanan.
Notifikasi otomatis ketika tiket baru masuk.

Jalankan dengan:
    streamlit run app/dashboard/main.py
"""
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.constants import (
    ESCALATION_LEVELS,
    SEVERITY_BADGE,
    STATUS_BADGE,
    TICKET_STATUSES,
)
from app.dashboard.api_client import (
    get_all_tickets,
    get_stats,
    get_ticket,
    health_check,
    update_ticket,
)
from app.dashboard.report_generator import generate_report_filename, generate_report_html

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Admin — Helpdesk Keamanan Siber",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS: tampilan email-like
st.markdown("""
<style>
/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0f172a;
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #cbd5e1 !important;
    font-size: 14px;
}
section[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
}

/* Inbox ticket card */
.ticket-card {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: background 0.15s;
}
.ticket-card:hover { background: #f1f5f9; }
.ticket-card.selected { border-color: #3b82f6; background: #eff6ff; }
.ticket-card.unread { border-left: 4px solid #ef4444; }

.tc-header { display: flex; justify-content: space-between; align-items: center; }
.tc-id { font-weight: 700; font-size: 13px; color: #1e293b; }
.tc-time { font-size: 11px; color: #94a3b8; }
.tc-type { font-size: 12px; color: #475569; margin-top: 2px; }
.tc-badges { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }

/* Status & severity badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 600;
    color: #fff;
}
.badge-pending    { background: #f59e0b; }
.badge-progress   { background: #3b82f6; }
.badge-resolved   { background: #10b981; }
.badge-closed     { background: #6b7280; }
.badge-kritis     { background: #dc2626; }
.badge-tinggi     { background: #ea580c; }
.badge-sedang     { background: #ca8a04; }
.badge-rendah     { background: #16a34a; }
.badge-info       { background: #2563eb; }

/* Notif bell */
.notif-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #ef4444;
    border-radius: 50%;
    margin-left: 4px;
    vertical-align: middle;
}

/* Detail pane header */
.detail-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
    color: #fff;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.detail-header h2 { font-size: 20px; margin-bottom: 6px; }
.detail-header p  { font-size: 13px; opacity: 0.85; }
.detail-meta { display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap; }
.detail-meta-item label { font-size: 10px; opacity: 0.75; display: block; }
.detail-meta-item span  { font-size: 13px; font-weight: 600; }

/* Info table */
.info-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.info-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }
.info-table td:first-child { color: #64748b; width: 38%; font-size: 12px; }

/* Section card */
.section-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.section-card h4 {
    font-size: 12px;
    font-weight: 700;
    color: #3b82f6;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

_PAGE_OPTIONS = ["📊 Ringkasan", "📥 Inbox Tiket", "📄 Buat Laporan"]

_STATUS_BADGE    = STATUS_BADGE
_STATUS_OPTIONS  = TICKET_STATUSES
_SEV_BADGE       = SEVERITY_BADGE
_ESCALATION_OPTIONS = ESCALATION_LEVELS


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "selected_ticket_id": None,
        "current_page": "📥 Inbox Tiket",
        "known_ticket_ids": set(),
        "last_refresh": 0.0,
        "auto_refresh": False,
        "report_prepared_by": "Tim Keamanan Siber Pusdatin",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=20)
def _load_tickets() -> list[dict]:
    return get_all_tickets()


@st.cache_data(ttl=20)
def _load_stats() -> dict:
    return get_stats()


def _invalidate_cache() -> None:
    _load_tickets.clear()
    _load_stats.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _badge_html(css_class: str, label: str) -> str:
    return f'<span class="badge {css_class}">{label}</span>'


def _fmt_dt(dt_str) -> str:
    if not dt_str:
        return "—"
    s = str(dt_str)[:16].replace("T", " ")
    return s


def _relative_time(dt_str) -> str:
    """Tampilkan waktu relatif (5m, 2j, kemarin)."""
    if not dt_str:
        return ""
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        minutes = int(delta.total_seconds() / 60)
        if minutes < 1:
            return "baru saja"
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}j"
        days = hours // 24
        return f"{days}h"
    except Exception as exc:
        logger.debug("Gagal mem-parse waktu relatif '%s': %s", dt_str, exc)
        return ""


def _check_new_tickets(tickets: list[dict]) -> None:
    """Tampilkan toast notifikasi jika ada tiket baru sejak refresh terakhir."""
    current_ids = {t["ticket_id"] for t in tickets}
    prev_ids    = st.session_state.known_ticket_ids

    if prev_ids:  # Hanya notifikasi jika bukan load pertama
        new_ids = current_ids - prev_ids
        for tid in sorted(new_ids):
            # Cari info tiket
            t = next((x for x in tickets if x["ticket_id"] == tid), {})
            inc = t.get("incident_type", "")
            sev = t.get("severity", "")
            st.toast(
                f"🚨 Laporan baru masuk!\n**{tid}** — {inc} ({sev})",
                icon="🔔",
            )

    st.session_state.known_ticket_ids = current_ids


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar(stats: dict, api_ok: bool) -> str:
    with st.sidebar:
        st.markdown("## 🛡️ Admin Dashboard")
        st.caption("Helpdesk Keamanan Siber\nPusdatin Kementan")
        st.divider()

        # Metrik cepat di sidebar
        pending = stats.get("by_status", {}).get("PENDING_REVIEW", 0)
        in_prog = stats.get("by_status", {}).get("IN_PROGRESS", 0)
        total   = stats.get("total", 0)

        col1, col2 = st.columns(2)
        col1.metric("Total", total)
        col2.metric("🔔 Menunggu", pending)

        st.divider()

        # Navigasi — dengan badge notif jika ada pending
        pending_dot = " 🔴" if pending > 0 else ""
        page_labels = [
            "📊 Ringkasan",
            f"📥 Inbox Tiket{pending_dot}",
            "📄 Buat Laporan",
        ]
        # Resolve current page ke opsi tanpa dot
        current = st.session_state.current_page
        # Cari index
        base_options = _PAGE_OPTIONS
        try:
            idx = next(
                i for i, opt in enumerate(base_options)
                if current.startswith(opt.split(" ")[0] + " " + opt.split(" ")[1])
            )
        except StopIteration:
            idx = 1

        selected = st.radio(
            "Navigasi",
            options=page_labels,
            index=idx,
            label_visibility="collapsed",
        )
        # Normalize kembali ke _PAGE_OPTIONS
        selected_base = selected.rstrip(" 🔴")
        st.session_state.current_page = selected_base

        st.divider()

        # Status API
        if api_ok:
            st.success("🟢 API Online")
        else:
            st.error("🔴 API Offline")
            st.caption("Jalankan: `uvicorn app.main:app --reload`")

        col_ref, col_auto = st.columns(2)
        if col_ref.button("🔄 Refresh", use_container_width=True):
            _invalidate_cache()
            st.rerun()

        auto = col_auto.checkbox("Auto", value=st.session_state.auto_refresh, help="Auto-refresh 20 detik")
        st.session_state.auto_refresh = auto

        st.divider()
        st.markdown("📚 [Kelola Knowledge Base RAG](http://localhost:8502)")

    return selected_base


# ---------------------------------------------------------------------------
# Halaman: Ringkasan
# ---------------------------------------------------------------------------

def page_ringkasan(stats: dict) -> None:
    st.title("📊 Ringkasan Insiden")

    by_status   = stats.get("by_status", {})
    by_severity = stats.get("by_severity", {})
    by_type     = stats.get("by_type", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Tiket",  stats.get("total", 0))
    c2.metric("🟡 Menunggu",  by_status.get("PENDING_REVIEW", 0))
    c3.metric("🔵 Ditangani", by_status.get("IN_PROGRESS", 0))
    c4.metric("🟢 Selesai",   by_status.get("RESOLVED", 0))
    c5.metric("⚫ Ditutup",   by_status.get("CLOSED", 0))

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Per Jenis Insiden")
        if by_type:
            df = pd.DataFrame(list(by_type.items()), columns=["Jenis", "Jumlah"])
            st.bar_chart(df.set_index("Jenis"))
        else:
            st.info("Belum ada data.")

    with col_r:
        st.subheader("Per Tingkat Keparahan")
        if by_severity:
            order = ["Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"]
            df = pd.DataFrame(list(by_severity.items()), columns=["Keparahan", "Jumlah"])
            df["Keparahan"] = pd.Categorical(df["Keparahan"], categories=order, ordered=True)
            st.bar_chart(df.sort_values("Keparahan").set_index("Keparahan"))
        else:
            st.info("Belum ada data.")


# ---------------------------------------------------------------------------
# Halaman: Inbox Tiket (email-like)
# ---------------------------------------------------------------------------

def page_inbox(tickets: list[dict]) -> None:
    # Layout: inbox kiri | detail kanan
    col_inbox, col_detail = st.columns([1, 2], gap="medium")

    with col_inbox:
        _render_inbox_list(tickets)

    with col_detail:
        _render_detail_pane()


def _render_inbox_list(tickets: list[dict]) -> None:
    st.markdown("### 📥 Inbox")

    # Filter bar
    filter_status = st.multiselect(
        "Filter status",
        options=_STATUS_OPTIONS,
        default=[],
        format_func=lambda s: _STATUS_BADGE.get(s, ("", s))[1],
        placeholder="Semua status",
        label_visibility="collapsed",
    )

    filtered = tickets
    if filter_status:
        filtered = [t for t in tickets if t.get("status") in filter_status]

    st.caption(f"{len(filtered)} tiket")

    if not filtered:
        st.info("Tidak ada tiket.")
        return

    for t in filtered:
        tid     = t.get("ticket_id", "")
        status  = t.get("status", "")
        sev     = t.get("severity", "")
        inc     = t.get("incident_type", "—")
        rel_t   = _relative_time(t.get("created_at"))
        is_new  = status == "PENDING_REVIEW"
        is_sel  = tid == st.session_state.selected_ticket_id

        badge_cls, badge_lbl = _STATUS_BADGE.get(status, ("", status))
        sev_cls = _SEV_BADGE.get(sev, "")

        card_class = "ticket-card"
        if is_new:
            card_class += " unread"
        if is_sel:
            card_class += " selected"

        st.markdown(f"""
<div class="{card_class}">
  <div class="tc-header">
    <span class="tc-id">{'🔔 ' if is_new else ''}{tid}</span>
    <span class="tc-time">{rel_t}</span>
  </div>
  <div class="tc-type">{inc}</div>
  <div class="tc-badges">
    {_badge_html(badge_cls, badge_lbl)}
    {_badge_html(sev_cls, sev) if sev_cls else ''}
  </div>
</div>
""", unsafe_allow_html=True)

        if st.button("Buka", key=f"open_{tid}", use_container_width=True, type="secondary"):
            st.session_state.selected_ticket_id = tid
            st.rerun()


def _render_detail_pane() -> None:
    tid = st.session_state.selected_ticket_id

    if not tid:
        st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
height:400px;color:#94a3b8;text-align:center;">
  <div style="font-size:48px;margin-bottom:16px;">📬</div>
  <div style="font-size:16px;font-weight:600;">Pilih tiket dari inbox</div>
  <div style="font-size:13px;margin-top:8px;">Klik salah satu tiket di sebelah kiri untuk melihat detail</div>
</div>
""", unsafe_allow_html=True)
        return

    try:
        ticket = get_ticket(tid)
    except Exception as exc:
        st.error(f"Gagal memuat tiket: {exc}")
        return

    if ticket is None:
        st.error(f"Tiket {tid} tidak ditemukan.")
        return

    status  = ticket.get("status", "")
    sev     = ticket.get("severity", "")
    inc     = ticket.get("incident_type", "—")
    badge_cls, badge_lbl = _STATUS_BADGE.get(status, ("", status))
    sev_cls = _SEV_BADGE.get(sev, "")

    # --- Header detail pane ---
    st.markdown(f"""
<div class="detail-header">
  <h2>📌 {tid}</h2>
  <p>{inc}</p>
  <div class="detail-meta">
    <div class="detail-meta-item">
      <label>STATUS</label>
      <span>{_badge_html(badge_cls, badge_lbl)}</span>
    </div>
    <div class="detail-meta-item">
      <label>KEPARAHAN</label>
      <span>{_badge_html(sev_cls, sev)}</span>
    </div>
    <div class="detail-meta-item">
      <label>ESKALASI</label>
      <span>{ticket.get('escalation_level') or '—'}</span>
    </div>
    <div class="detail-meta-item">
      <label>DITUGASKAN KE</label>
      <span>{ticket.get('assigned_to') or 'Belum ditugaskan'}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # --- Tab: Info | Update | Laporan ---
    tab_info, tab_update, tab_report = st.tabs(["📋 Informasi", "⚙️ Update Status", "📄 Buat Laporan"])

    with tab_info:
        st.markdown('<div class="section-card"><h4>Pelapor</h4>', unsafe_allow_html=True)
        reporter = ticket.get("reporter_name") or ticket.get("reporter_id", "—")
        st.markdown(f"""
<table class="info-table">
  <tr><td>Nama Pelapor</td><td><strong>{reporter}</strong></td></tr>
  <tr><td>Waktu Laporan</td><td>{_fmt_dt(ticket.get('created_at'))}</td></tr>
  <tr><td>Diperbarui</td><td>{_fmt_dt(ticket.get('updated_at'))}</td></tr>
</table>
</div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-card"><h4>Deskripsi Insiden</h4>', unsafe_allow_html=True)
        st.write(ticket.get("description_sanitized") or "—")
        st.markdown("</div>", unsafe_allow_html=True)

        mitigation = ticket.get("mitigation_recommendation", "")
        if mitigation:
            st.markdown('<div class="section-card"><h4>Rekomendasi Mitigasi</h4>', unsafe_allow_html=True)
            st.markdown(mitigation)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_update:
        _render_update_form(ticket)

    with tab_report:
        _render_report_tab(ticket)


def _render_update_form(ticket: dict) -> None:
    tid = ticket.get("ticket_id", "")
    current_status = ticket.get("status", "PENDING_REVIEW")
    current_assigned = ticket.get("assigned_to") or ""
    current_escalation = ticket.get("escalation_level") or "Standar"

    with st.form(f"form_update_{tid}"):
        new_status = st.selectbox(
            "Status Baru",
            options=_STATUS_OPTIONS,
            index=_STATUS_OPTIONS.index(current_status) if current_status in _STATUS_OPTIONS else 0,
            format_func=lambda s: _STATUS_BADGE.get(s, ("", s))[1],
        )
        new_assigned = st.text_input(
            "Ditugaskan ke",
            value=current_assigned,
            placeholder="Nama analis CSIRT",
        )
        new_escalation = st.selectbox(
            "Tingkat Eskalasi",
            options=_ESCALATION_OPTIONS,
            index=_ESCALATION_OPTIONS.index(current_escalation)
            if current_escalation in _ESCALATION_OPTIONS else 2,
        )
        notify = st.checkbox("Kirim notifikasi ke pelapor via Telegram", value=True)
        submitted = st.form_submit_button("💾 Simpan Update", type="primary", use_container_width=True)

    if submitted:
        changed = (
            new_status != current_status
            or new_assigned != current_assigned
            or new_escalation != current_escalation
        )
        if not changed:
            st.warning("Tidak ada perubahan.")
        else:
            try:
                result = update_ticket(
                    ticket_id=tid,
                    status=new_status     if new_status != current_status         else None,
                    assigned_to=new_assigned if new_assigned != current_assigned  else None,
                    escalation_level=new_escalation if new_escalation != current_escalation else None,
                    notify_reporter=notify,
                )
                _, new_lbl = _STATUS_BADGE.get(result["status"], ("", result["status"]))
                st.success(
                    f"✅ **{result['ticket_id']}** diperbarui — Status: **{new_lbl}**"
                    + (" · Notifikasi terkirim." if notify else "")
                )
                _invalidate_cache()
            except Exception as exc:
                st.error(f"Gagal update: {exc}")


def _render_report_tab(ticket: dict) -> None:
    tid = ticket.get("ticket_id", "")
    st.markdown("#### 📄 Generate Laporan Insiden")
    st.caption(
        "Laporan dihasilkan dalam format HTML. "
        "Download dan buka di browser, lalu **Ctrl+P → Save as PDF** untuk cetak."
    )

    prepared_by = st.text_input(
        "Disiapkan oleh",
        value=st.session_state.report_prepared_by,
        placeholder="Nama / Tim",
        key=f"prep_{tid}",
    )
    st.session_state.report_prepared_by = prepared_by

    col_dl, col_tg = st.columns(2)

    with col_dl:
        if st.button("⬇️ Generate & Download", type="primary", use_container_width=True, key=f"gen_{tid}"):
            with st.spinner("Membuat laporan..."):
                html_content = generate_report_html(ticket, prepared_by)
                filename = generate_report_filename(ticket)
            st.download_button(
                label="📥 Download Laporan HTML",
                data=html_content.encode("utf-8"),
                file_name=filename,
                mime="text/html",
                use_container_width=True,
                key=f"dl_{tid}",
            )

    with col_tg:
        if st.button("📨 Kirim Ringkasan ke CSIRT", use_container_width=True, key=f"tg_{tid}"):
            _send_report_to_csirt(ticket)


def _send_report_to_csirt(ticket: dict) -> None:
    """Kirim ringkasan tiket ke CSIRT_CHAT_ID via Telegram."""
    import asyncio
    import os

    token    = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id  = os.getenv("CSIRT_CHAT_ID", "")
    if not token or not chat_id:
        st.error("TELEGRAM_BOT_TOKEN atau CSIRT_CHAT_ID belum diset di .env")
        return

    tid    = ticket.get("ticket_id", "—")
    inc    = ticket.get("incident_type", "—")
    sev    = ticket.get("severity", "—")
    status = _STATUS_BADGE.get(ticket.get("status", ""), ("", ticket.get("status", "")))[1]
    desc   = (ticket.get("description_sanitized") or "")[:300]

    message = (
        f"🚨 *LAPORAN INSIDEN — {tid}*\n\n"
        f"*Jenis:* {inc}\n"
        f"*Keparahan:* {sev}\n"
        f"*Status:* {status}\n"
        f"*Ditugaskan ke:* {ticket.get('assigned_to') or '—'}\n\n"
        f"*Deskripsi:*\n{desc}{'...' if len(desc) == 300 else ''}\n\n"
        f"_Silakan tinjau dan tangani segera melalui Dashboard Admin._"
    )

    async def _send() -> None:
        from telegram import Bot
        async with Bot(token=token) as bot:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

    try:
        asyncio.run(_send())
        st.success("✅ Ringkasan berhasil dikirim ke grup CSIRT.")
    except Exception as exc:
        st.error(f"Gagal kirim ke CSIRT: {exc}")


# ---------------------------------------------------------------------------
# Halaman: Buat Laporan (standalone)
# ---------------------------------------------------------------------------

def page_buat_laporan(tickets: list[dict]) -> None:
    st.title("📄 Buat Laporan Insiden")
    st.caption("Pilih tiket dan generate laporan formal untuk dikirim ke CSIRT atau diarsipkan.")

    if not tickets:
        st.info("Belum ada tiket yang tersedia.")
        return

    options = {
        f"{t['ticket_id']} — {t.get('incident_type','?')} ({t.get('status','?')})": t["ticket_id"]
        for t in tickets
    }
    selected_label = st.selectbox("Pilih Tiket", options=list(options.keys()))
    selected_tid   = options[selected_label]

    col_left, col_right = st.columns([1, 1])

    with col_left:
        prepared_by = st.text_input(
            "Disiapkan oleh",
            value=st.session_state.report_prepared_by,
        )
        st.session_state.report_prepared_by = prepared_by

        if st.button("⬇️ Generate & Download Laporan", type="primary", use_container_width=True):
            try:
                ticket = get_ticket(selected_tid)
                if ticket is None:
                    st.error("Tiket tidak ditemukan.")
                else:
                    html_content = generate_report_html(ticket, prepared_by)
                    filename     = generate_report_filename(ticket)
                    st.download_button(
                        label="📥 Download Laporan HTML",
                        data=html_content.encode("utf-8"),
                        file_name=filename,
                        mime="text/html",
                        use_container_width=True,
                    )
                    st.info("💡 Buka file di browser → Ctrl+P → Save as PDF untuk cetak.")
            except Exception as exc:
                st.error(f"Error: {exc}")

        if st.button("📨 Kirim Ringkasan ke CSIRT", use_container_width=True):
            try:
                ticket = get_ticket(selected_tid)
                if ticket:
                    _send_report_to_csirt(ticket)
            except Exception as exc:
                st.error(f"Error: {exc}")

    with col_right:
        # Preview preview info tiket
        ticket_preview = next((t for t in tickets if t["ticket_id"] == selected_tid), None)
        if ticket_preview:
            sev    = ticket_preview.get("severity", "")
            status = ticket_preview.get("status", "")
            _, status_lbl = _STATUS_BADGE.get(status, ("", status))
            sev_cls = _SEV_BADGE.get(sev, "")

            st.markdown(f"""
<div class="section-card">
  <h4>Preview Tiket</h4>
  <table class="info-table">
    <tr><td>Ticket ID</td><td><strong>{ticket_preview.get('ticket_id')}</strong></td></tr>
    <tr><td>Jenis Insiden</td><td>{ticket_preview.get('incident_type','—')}</td></tr>
    <tr><td>Keparahan</td><td>{_badge_html(sev_cls, sev)}</td></tr>
    <tr><td>Status</td><td>{status_lbl}</td></tr>
    <tr><td>Ditugaskan ke</td><td>{ticket_preview.get('assigned_to') or '—'}</td></tr>
    <tr><td>Waktu Laporan</td><td>{_fmt_dt(ticket_preview.get('created_at'))}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_state()

    # Load data (akan error jika API offline — ditangani per halaman)
    api_ok = health_check()
    try:
        tickets = _load_tickets()
        stats   = _load_stats()
        _check_new_tickets(tickets)
    except Exception:
        tickets = []
        stats   = {}

    # Render sidebar & dapatkan halaman aktif
    page = _render_sidebar(stats, api_ok)

    # Guard: API offline
    if not api_ok and page != "📊 Ringkasan":
        st.warning("⚠️ API tidak dapat dijangkau. Pastikan FastAPI berjalan di port 8000.")

    # Render halaman
    if page == "📊 Ringkasan":
        page_ringkasan(stats)
    elif page == "📥 Inbox Tiket":
        page_inbox(tickets)
    elif page == "📄 Buat Laporan":
        page_buat_laporan(tickets)

    # Auto-refresh
    if st.session_state.auto_refresh:
        now = time.time()
        if now - st.session_state.last_refresh >= 20:
            st.session_state.last_refresh = now
            _invalidate_cache()
            st.rerun()


if __name__ == "__main__":
    main()
