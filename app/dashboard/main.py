"""Dashboard Admin — Helpdesk Keamanan Siber Pusdatin Kementan.

Jalankan dengan:
    streamlit run app/dashboard/main.py

Env vars opsional:
    HELPDESK_API_URL  — default: http://localhost:8000/api/v1
"""
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# Agar bisa import dari root project
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dashboard.api_client import (
    get_all_tickets,
    get_stats,
    get_ticket,
    health_check,
    update_ticket,
)

# ---------------------------------------------------------------------------
# Config & konstanta
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Admin — Helpdesk Keamanan Siber",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SEVERITY_COLOR = {
    "Kritis":        "🔴",
    "Tinggi":        "🟠",
    "Sedang":        "🟡",
    "Rendah":        "🟢",
    "Informasional": "🔵",
}

STATUS_COLOR = {
    "PENDING_REVIEW": "🟡",
    "IN_PROGRESS":    "🔵",
    "RESOLVED":       "🟢",
    "CLOSED":         "⚫",
}

STATUS_OPTIONS = ["PENDING_REVIEW", "IN_PROGRESS", "RESOLVED", "CLOSED"]

ESCALATION_OPTIONS = ["Segera", "Mendesak", "Standar", "Rutin"]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "selected_ticket_id": None,
        "last_refresh": 0.0,
        "auto_refresh": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_severity(sev: str) -> str:
    return f"{SEVERITY_COLOR.get(sev, '⚪')} {sev}"


def _fmt_status(status: str) -> str:
    return f"{STATUS_COLOR.get(status, '⚪')} {status}"


def _fmt_datetime(dt_str: str | None) -> str:
    if not dt_str:
        return "-"
    return str(dt_str)[:16].replace("T", " ")


@st.cache_data(ttl=30)
def _load_tickets() -> list[dict]:
    return get_all_tickets()


@st.cache_data(ttl=30)
def _load_stats() -> dict:
    return get_stats()


def _invalidate_cache() -> None:
    _load_tickets.clear()
    _load_stats.clear()


# ---------------------------------------------------------------------------
# Halaman: Ringkasan
# ---------------------------------------------------------------------------

def page_ringkasan() -> None:
    st.title("🛡️ Ringkasan Insiden")

    try:
        stats = _load_stats()
    except Exception as exc:
        st.error(f"Gagal memuat statistik: {exc}")
        return

    total = stats.get("total", 0)
    by_status = stats.get("by_status", {})
    by_severity = stats.get("by_severity", {})
    by_type = stats.get("by_type", {})

    # --- Metrik ringkasan ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tiket", total)
    col2.metric("🟡 Menunggu", by_status.get("PENDING_REVIEW", 0))
    col3.metric("🔵 Ditangani", by_status.get("IN_PROGRESS", 0))
    col4.metric("🟢 Selesai", by_status.get("RESOLVED", 0))
    col5.metric("⚫ Ditutup", by_status.get("CLOSED", 0))

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Per Jenis Insiden")
        if by_type:
            df_type = pd.DataFrame(
                list(by_type.items()), columns=["Jenis", "Jumlah"]
            ).sort_values("Jumlah", ascending=False)
            st.bar_chart(df_type.set_index("Jenis"))
        else:
            st.info("Belum ada data.")

    with col_right:
        st.subheader("Per Tingkat Keparahan")
        if by_severity:
            df_sev = pd.DataFrame(
                list(by_severity.items()), columns=["Keparahan", "Jumlah"]
            )
            # Urutan severity
            order = ["Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"]
            df_sev["Keparahan"] = pd.Categorical(df_sev["Keparahan"], categories=order, ordered=True)
            df_sev = df_sev.sort_values("Keparahan")
            st.bar_chart(df_sev.set_index("Keparahan"))
        else:
            st.info("Belum ada data.")


# ---------------------------------------------------------------------------
# Halaman: Daftar Tiket
# ---------------------------------------------------------------------------

def page_daftar_tiket() -> None:
    st.title("📋 Daftar Tiket")

    # --- Filter sidebar ---
    st.sidebar.subheader("Filter")
    filter_status = st.sidebar.multiselect(
        "Status",
        options=STATUS_OPTIONS,
        default=[],
        format_func=_fmt_status,
    )
    filter_severity = st.sidebar.multiselect(
        "Keparahan",
        options=["Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"],
        default=[],
        format_func=_fmt_severity,
    )
    filter_type = st.sidebar.multiselect(
        "Jenis Insiden",
        options=[
            "Phishing", "Malware", "Ransomware", "Web Defacement",
            "DDoS", "Akses Tidak Sah", "Kebocoran Data", "Lainnya",
        ],
        default=[],
    )

    # --- Load data ---
    try:
        tickets = _load_tickets()
    except Exception as exc:
        st.error(f"Gagal memuat tiket: {exc}")
        return

    if not tickets:
        st.info("Belum ada tiket yang masuk.")
        return

    # --- Apply filter ---
    df = pd.DataFrame(tickets)
    if filter_status:
        df = df[df["status"].isin(filter_status)]
    if filter_severity:
        df = df[df["severity"].isin(filter_severity)]
    if filter_type:
        df = df[df["incident_type"].isin(filter_type)]

    st.caption(f"Menampilkan {len(df)} dari {len(tickets)} tiket")

    if df.empty:
        st.info("Tidak ada tiket yang sesuai filter.")
        return

    # --- Tampilkan tabel ---
    display_cols = ["ticket_id", "incident_type", "severity", "status",
                    "escalation_level", "reporter_name", "assigned_to", "created_at"]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()

    # Format kolom
    if "severity" in df_display:
        df_display["severity"] = df_display["severity"].map(_fmt_severity).fillna(df_display["severity"])
    if "status" in df_display:
        df_display["status"] = df_display["status"].map(_fmt_status).fillna(df_display["status"])
    if "created_at" in df_display:
        df_display["created_at"] = df_display["created_at"].apply(_fmt_datetime)

    df_display.columns = [
        c.replace("_", " ").title() for c in df_display.columns
    ]
    df_display = df_display.rename(columns={"Ticket Id": "Ticket ID"})

    # Tabel interaktif
    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Jika ada baris yang dipilih
    selected_rows = event.selection.get("rows", [])
    if selected_rows:
        idx = selected_rows[0]
        original_df = df.reset_index(drop=True)
        ticket_id = original_df.loc[idx, "ticket_id"]
        st.session_state.selected_ticket_id = ticket_id
        st.info(f"Tiket dipilih: **{ticket_id}** — buka tab **Detail & Update** untuk mengelola.")


# ---------------------------------------------------------------------------
# Halaman: Detail & Update
# ---------------------------------------------------------------------------

def page_detail_update() -> None:
    st.title("🔧 Detail & Update Tiket")

    # --- Pilih tiket ---
    ticket_id_input = st.text_input(
        "Nomor Tiket",
        value=st.session_state.selected_ticket_id or "",
        placeholder="Contoh: TICKET-2026-0001",
    )

    if not ticket_id_input.strip():
        st.info("Pilih tiket dari halaman **Daftar Tiket** atau masukkan nomor tiket di atas.")
        return

    ticket_id = ticket_id_input.strip().upper()

    try:
        ticket = get_ticket(ticket_id)
    except Exception as exc:
        st.error(f"Gagal memuat tiket: {exc}")
        return

    if ticket is None:
        st.error(f"Tiket **{ticket_id}** tidak ditemukan.")
        return

    # --- Tampilkan info tiket ---
    col_info, col_form = st.columns([3, 2])

    with col_info:
        st.subheader(f"📌 {ticket['ticket_id']}")

        st.markdown(f"""
| Field | Nilai |
|---|---|
| **Jenis Insiden** | {ticket.get('incident_type', '-')} |
| **Keparahan** | {_fmt_severity(ticket.get('severity', '-'))} |
| **Status** | {_fmt_status(ticket.get('status', '-'))} |
| **Eskalasi** | {ticket.get('escalation_level', '-')} |
| **Pelapor** | {ticket.get('reporter_name') or ticket.get('reporter_id', '-')} |
| **Ditugaskan ke** | {ticket.get('assigned_to') or 'Belum ditugaskan'} |
| **Dibuat** | {_fmt_datetime(ticket.get('created_at'))} |
| **Diperbarui** | {_fmt_datetime(ticket.get('updated_at'))} |
""")

        with st.expander("📝 Deskripsi Insiden"):
            st.write(ticket.get("description_sanitized", "-"))

        with st.expander("🔧 Rekomendasi Mitigasi"):
            mitigation = ticket.get("mitigation_recommendation", "")
            if mitigation:
                st.markdown(mitigation)
            else:
                st.info("Tidak ada rekomendasi mitigasi.")

    with col_form:
        st.subheader("⚙️ Update Tiket")

        current_status = ticket.get("status", "PENDING_REVIEW")
        current_assigned = ticket.get("assigned_to") or ""
        current_escalation = ticket.get("escalation_level") or "Standar"

        new_status = st.selectbox(
            "Status",
            options=STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0,
            format_func=_fmt_status,
        )
        new_assigned = st.text_input(
            "Ditugaskan ke (opsional)",
            value=current_assigned,
            placeholder="Nama atau ID analis CSIRT",
        )
        new_escalation = st.selectbox(
            "Tingkat Eskalasi",
            options=ESCALATION_OPTIONS,
            index=ESCALATION_OPTIONS.index(current_escalation) if current_escalation in ESCALATION_OPTIONS else 2,
        )
        notify = st.checkbox("Kirim notifikasi ke pelapor via Telegram", value=True)

        st.caption("⚠️ Notifikasi dikirim otomatis ke pelapor jika dicentang.")

        if st.button("💾 Simpan Update", type="primary", use_container_width=True):
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
                        ticket_id=ticket_id,
                        status=new_status if new_status != current_status else None,
                        assigned_to=new_assigned if new_assigned != current_assigned else None,
                        escalation_level=new_escalation if new_escalation != current_escalation else None,
                        notify_reporter=notify,
                    )
                    st.success(
                        f"Tiket **{result['ticket_id']}** berhasil diperbarui!\n\n"
                        f"Status: {_fmt_status(result['status'])}"
                        + (" — Notifikasi terkirim ke pelapor." if notify else "")
                    )
                    _invalidate_cache()
                    st.session_state.selected_ticket_id = ticket_id
                except Exception as exc:
                    st.error(f"Gagal update tiket: {exc}")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    _init_state()

    # --- Sidebar ---
    with st.sidebar:
        st.title("🛡️ Admin Dashboard")
        st.caption("Helpdesk Keamanan Siber\nPusdatin Kementan")
        st.divider()

        page = st.radio(
            "Navigasi",
            options=["Ringkasan", "Daftar Tiket", "Detail & Update"],
            index=0,
        )

        st.divider()

        # Status koneksi API
        if health_check():
            st.success("API: Online")
        else:
            st.error("API: Offline")

        if st.button("🔄 Refresh Data", use_container_width=True):
            _invalidate_cache()
            st.rerun()

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (30 detik)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh

        st.divider()
        st.page_link("rag_manager.py", label="📚 Kelola Knowledge Base RAG", icon="📚")

    # --- Render halaman ---
    if page == "Ringkasan":
        page_ringkasan()
    elif page == "Daftar Tiket":
        page_daftar_tiket()
    elif page == "Detail & Update":
        page_detail_update()

    # --- Auto-refresh ---
    if st.session_state.auto_refresh:
        now = time.time()
        if now - st.session_state.last_refresh >= 30:
            st.session_state.last_refresh = now
            _invalidate_cache()
            time.sleep(0.5)
            st.rerun()
        remaining = max(0, int(30 - (time.time() - st.session_state.last_refresh)))
        st.caption(f"Auto-refresh dalam {remaining} detik")


if __name__ == "__main__":
    main()
