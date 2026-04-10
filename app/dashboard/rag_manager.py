"""Dashboard Manajemen Knowledge Base RAG — Helpdesk Keamanan Siber.

Jalankan dengan:
    streamlit run app/dashboard/rag_manager.py

Env vars opsional:
    QDRANT_URL         — default: http://localhost:6333
    QDRANT_API_KEY     — opsional
    OPENAI_BASE_URL    — default: OpenAI langsung
    GITHUB_TOKEN       — untuk GitHub Models (dev mode)
    OPENAI_API_KEY     — untuk OpenAI (produksi)
"""
import json
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dashboard.rag_client import (
    delete_chunks_by_doc_id,
    delete_metadata,
    delete_pdf,
    delete_stix,
    get_chunks_sample,
    get_collection_info,
    get_collection_stats_by_source,
    list_metadata_documents,
    list_pdf_files,
    list_stix_files,
    reingest_document,
    reingest_stix,
    save_metadata,
    save_pdf,
    save_stix,
    search_chunks,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="RAG Knowledge Base Manager",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

_INCIDENT_TYPE_OPTIONS = [
    "phishing", "malware", "ransomware", "web_defacement",
    "ddos", "akses_tidak_sah", "kebocoran_data", "general",
]

_SOURCE_FRAMEWORK_OPTIONS = ["NIST", "MITRE", "BSSN", "ISO27001", "LAINNYA"]


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def _load_collection_info() -> dict:
    return get_collection_info()


@st.cache_data(ttl=60)
def _load_stats() -> list[dict]:
    return get_collection_stats_by_source()


@st.cache_data(ttl=30)
def _load_docs() -> list[dict]:
    return list_metadata_documents()


@st.cache_data(ttl=30)
def _load_pdfs() -> list[dict]:
    return list_pdf_files()


@st.cache_data(ttl=30)
def _load_stix() -> list[dict]:
    return list_stix_files()


def _clear_cache() -> None:
    _load_collection_info.clear()
    _load_stats.clear()
    _load_docs.clear()
    _load_pdfs.clear()
    _load_stix.clear()


# ---------------------------------------------------------------------------
# Halaman: Status Collection
# ---------------------------------------------------------------------------

def page_status() -> None:
    st.title("📊 Status Knowledge Base")

    col_refresh, _ = st.columns([1, 4])
    if col_refresh.button("🔄 Refresh", use_container_width=True):
        _clear_cache()
        st.rerun()

    # --- Collection info ---
    try:
        info = _load_collection_info()
    except Exception as exc:
        st.error(f"Tidak bisa terhubung ke Qdrant: {exc}")
        st.info("Pastikan Qdrant berjalan di `QDRANT_URL` (default: http://localhost:6333)")
        return

    if "error" in info:
        st.error(f"Error dari Qdrant: {info['error']}")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Chunks (Vectors)", f"{info.get('total_vectors', 0):,}")
    col2.metric("Indexed Vectors", f"{info.get('indexed_vectors', 0):,}")
    col3.metric("Status Collection", info.get("status", "-"))

    st.divider()

    # --- Stats per dokumen ---
    st.subheader("Distribusi Chunks per Dokumen Sumber")
    try:
        stats = _load_stats()
    except Exception as exc:
        st.error(f"Gagal memuat statistik: {exc}")
        return

    if not stats:
        st.info("Belum ada data di knowledge base.")
        return

    import pandas as pd
    df = pd.DataFrame(stats)
    df = df.rename(columns={
        "doc_id": "Doc ID",
        "doc_title": "Judul Dokumen",
        "source_framework": "Framework",
        "chunk_count": "Jumlah Chunk",
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Bar chart
    chart_data = pd.DataFrame({
        "Dokumen": [s["doc_title"] or s["doc_id"] for s in stats],
        "Chunks": [s["chunk_count"] for s in stats],
    })
    st.bar_chart(chart_data.set_index("Dokumen"))


# ---------------------------------------------------------------------------
# Halaman: Kelola Dokumen
# ---------------------------------------------------------------------------

def page_kelola_dokumen() -> None:
    st.title("📁 Kelola Dokumen Knowledge Base")

    tab_list, tab_add, tab_pdf, tab_stix = st.tabs([
        "📋 Daftar Dokumen Terdaftar",
        "➕ Tambah Dokumen Baru",
        "📂 File PDF di Server",
        "🔷 File STIX / ATT&CK",
    ])

    # ── Tab: Daftar Dokumen ──────────────────────────────────────────────────
    with tab_list:
        try:
            docs = _load_docs()
        except Exception as exc:
            st.error(f"Gagal memuat dokumen: {exc}")
            return

        if not docs:
            st.info("Belum ada dokumen terdaftar di metadata.")
        else:
            for doc in docs:
                with st.expander(
                    f"{'✅' if doc['_pdf_exists'] else '⚠️'} "
                    f"**{doc.get('doc_title', doc.get('doc_id', '-'))}** "
                    f"({doc.get('source_framework', '-')}) "
                    f"— {doc.get('filename', '-')}",
                    expanded=False,
                ):
                    col_info, col_act = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"""
| Field | Nilai |
|---|---|
| **Doc ID** | `{doc.get('doc_id', '-')}` |
| **Judul** | {doc.get('doc_title', '-')} |
| **Framework** | {doc.get('source_framework', '-')} |
| **Versi** | {doc.get('version', '-')} |
| **Bahasa** | {doc.get('language', '-')} |
| **File PDF** | `{doc.get('filename', '-')}` {'✅' if doc['_pdf_exists'] else '❌ Tidak ditemukan'} |
| **Ukuran PDF** | {doc.get('_pdf_size_kb', 0)} KB |
| **Incident Types** | {', '.join(doc.get('incident_types', []))} |
""")

                    with col_act:
                        st.caption("Aksi")

                        # Preview chunks
                        if st.button("🔍 Preview Chunks", key=f"prev_{doc['doc_id']}"):
                            with st.spinner("Mengambil sampel chunks..."):
                                samples = get_chunks_sample(doc["doc_id"], limit=3)
                            if samples:
                                for s in samples:
                                    st.text_area(
                                        f"Chunk #{s.get('chunk_index', '?')} — {s.get('section_header', '')}",
                                        value=s["content"],
                                        height=120,
                                        key=f"sample_{doc['doc_id']}_{s['id']}",
                                        disabled=True,
                                    )
                            else:
                                st.warning("Belum ada chunks untuk dokumen ini.")

                        # Re-ingest
                        if doc["_pdf_exists"]:
                            if st.button("🔄 Re-ingest", key=f"reingest_{doc['doc_id']}", type="primary"):
                                with st.spinner(f"Re-ingest {doc['doc_title']}..."):
                                    result = reingest_document(doc["_meta_file"])
                                if "error" in result:
                                    st.error(result["error"])
                                else:
                                    st.success(
                                        f"Selesai! Dihapus: {result['deleted']} chunk lama. "
                                        f"Diupload: {result['uploaded']} chunk baru."
                                    )
                                    _clear_cache()
                        else:
                            st.warning("PDF tidak ada,\ntidak bisa re-ingest.")

                        st.divider()

                        # Hapus chunks dari Qdrant
                        if st.button("🗑️ Hapus dari Qdrant", key=f"del_vec_{doc['doc_id']}"):
                            st.session_state[f"confirm_del_vec_{doc['doc_id']}"] = True

                        if st.session_state.get(f"confirm_del_vec_{doc['doc_id']}"):
                            st.warning("⚠️ Yakin? Semua chunks akan dihapus dari Qdrant.")
                            col_yes, col_no = st.columns(2)
                            if col_yes.button("Ya, hapus", key=f"yes_vec_{doc['doc_id']}", type="primary"):
                                n = delete_chunks_by_doc_id(doc["doc_id"])
                                st.success(f"{n} chunks dihapus dari Qdrant.")
                                _clear_cache()
                                st.session_state.pop(f"confirm_del_vec_{doc['doc_id']}", None)
                                st.rerun()
                            if col_no.button("Batal", key=f"no_vec_{doc['doc_id']}"):
                                st.session_state.pop(f"confirm_del_vec_{doc['doc_id']}", None)
                                st.rerun()

    # ── Tab: Tambah Dokumen ──────────────────────────────────────────────────
    with tab_add:
        st.subheader("Tambah Dokumen PDF Baru")
        st.caption("Upload PDF dan isi metadata, lalu klik **Tambah & Ingest** untuk langsung diproses.")

        with st.form("form_add_doc", clear_on_submit=False):
            uploaded_file = st.file_uploader(
                "Upload file PDF", type=["pdf"], accept_multiple_files=False
            )

            col1, col2 = st.columns(2)
            with col1:
                doc_id = st.text_input(
                    "Doc ID *",
                    placeholder="contoh: nist-800-61-rev3",
                    help="ID unik dokumen (huruf kecil, tanda hubung)",
                )
                doc_title = st.text_input(
                    "Judul Dokumen *",
                    placeholder="contoh: Computer Security Incident Handling Guide Rev.3",
                )
                source_framework = st.selectbox(
                    "Source Framework *",
                    options=_SOURCE_FRAMEWORK_OPTIONS,
                )

            with col2:
                version = st.text_input(
                    "Versi",
                    placeholder="contoh: Rev. 3",
                )
                language = st.selectbox(
                    "Bahasa",
                    options=["en", "id"],
                    index=0,
                )
                incident_types = st.multiselect(
                    "Tipe Insiden yang Dicakup *",
                    options=_INCIDENT_TYPE_OPTIONS,
                    default=["general"],
                )

            submitted = st.form_submit_button("➕ Tambah & Ingest", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if not doc_id.strip():
                errors.append("Doc ID wajib diisi.")
            if not doc_title.strip():
                errors.append("Judul Dokumen wajib diisi.")
            if not incident_types:
                errors.append("Pilih minimal satu tipe insiden.")
            if uploaded_file is None:
                errors.append("Upload file PDF terlebih dahulu.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                pdf_filename = uploaded_file.name
                meta_filename = f"{doc_id.strip()}.json"
                meta_data = {
                    "doc_id": doc_id.strip(),
                    "doc_title": doc_title.strip(),
                    "source_framework": source_framework,
                    "version": version.strip(),
                    "language": language,
                    "filename": pdf_filename,
                    "incident_types": incident_types,
                }

                with st.spinner("Menyimpan file dan mengingest ke Qdrant..."):
                    # Simpan PDF
                    save_pdf(pdf_filename, uploaded_file.getvalue())
                    # Simpan metadata
                    save_metadata(meta_filename, meta_data)
                    # Ingest
                    result = reingest_document(meta_filename)

                if "error" in result:
                    st.error(f"Ingest gagal: {result['error']}")
                else:
                    st.success(
                        f"✅ **{doc_title}** berhasil ditambahkan!\n\n"
                        f"Chunks diupload ke Qdrant: **{result['uploaded']}**"
                    )
                    _clear_cache()

    # ── Tab: File PDF ────────────────────────────────────────────────────────
    with tab_pdf:
        st.subheader("File PDF di Server")
        st.caption("Daftar semua file PDF di `knowledge_base/documents/`. "
                   "File yang belum punya metadata tidak akan di-ingest otomatis.")

        try:
            pdfs = _load_pdfs()
        except Exception as exc:
            st.error(f"Gagal memuat daftar PDF: {exc}")
            return

        if not pdfs:
            st.info("Belum ada file PDF di direktori dokumen.")
        else:
            import pandas as pd
            df = pd.DataFrame(pdfs)
            df["has_metadata"] = df["has_metadata"].map({True: "✅ Ada", False: "⚠️ Belum ada"})
            df.columns = ["Nama File", "Ukuran (KB)", "Status Metadata"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Hapus File PDF")
            pdfs_without_metadata = [p["filename"] for p in list_pdf_files() if not p["has_metadata"]]
            if pdfs_without_metadata:
                del_filename = st.selectbox("Pilih file untuk dihapus", options=pdfs_without_metadata)
                if st.button("🗑️ Hapus File PDF", type="primary"):
                    if delete_pdf(del_filename):
                        st.success(f"File `{del_filename}` berhasil dihapus.")
                        _clear_cache()
                        st.rerun()
            else:
                st.info("Semua PDF sudah terdaftar di metadata.")

    # ── Tab: File STIX ───────────────────────────────────────────────────────
    with tab_stix:
        st.subheader("File STIX / MITRE ATT&CK")
        st.caption(
            "File STIX JSON (misal: `enterprise-attack.json`) disimpan di root `knowledge_base/`. "
            "Setiap file di-parse menjadi chunks teknik + mitigasi dan diupload ke Qdrant."
        )

        # --- Daftar file STIX yang ada ---
        try:
            stix_files = _load_stix()
        except Exception as exc:
            st.error(f"Gagal memuat daftar STIX: {exc}")
            stix_files = []

        if not stix_files:
            st.info("Belum ada file STIX di `knowledge_base/`. Upload file di bawah.")
        else:
            for sf in stix_files:
                with st.expander(
                    f"🔷 **{sf['filename']}** — {sf['size_mb']} MB — Doc ID: `{sf['doc_id']}`",
                    expanded=True,
                ):
                    col_info, col_act = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"""
| Field | Nilai |
|---|---|
| **Nama File** | `{sf['filename']}` |
| **Ukuran** | {sf['size_mb']} MB |
| **Doc ID di Qdrant** | `{sf['doc_id']}` |
| **Framework** | MITRE ATT&CK |
""")
                        # Tampilkan chunk count dari Qdrant
                        try:
                            from qdrant_client.models import Filter, FieldCondition, MatchValue
                            from app.dashboard.rag_client import _get_qdrant
                            from app.rag.embedder import COLLECTION_NAME
                            client_q = _get_qdrant()
                            count_res = client_q.count(
                                collection_name=COLLECTION_NAME,
                                count_filter=Filter(
                                    must=[FieldCondition(
                                        key="doc_id",
                                        match=MatchValue(value=sf["doc_id"])
                                    )]
                                ),
                                exact=True,
                            )
                            chunk_count = count_res.count
                            if chunk_count > 0:
                                st.success(f"✅ **{chunk_count:,} chunks** tersimpan di Qdrant")
                            else:
                                st.warning("⚠️ Belum ada chunks di Qdrant — lakukan Ingest")
                        except Exception:
                            st.info("Tidak bisa cek status Qdrant.")

                    with col_act:
                        st.caption("Aksi")

                        # Re-ingest
                        reingest_key = f"reingest_stix_{sf['filename']}"
                        if st.button("🔄 Ingest / Re-ingest", key=reingest_key, type="primary"):
                            st.session_state[f"confirm_reingest_stix_{sf['filename']}"] = True

                        if st.session_state.get(f"confirm_reingest_stix_{sf['filename']}"):
                            st.warning(
                                f"⚠️ Proses ini akan embed **ribuan chunks** dan membutuhkan waktu lama "
                                f"serta memanggil API embedding. Lanjutkan?"
                            )
                            col_yes, col_no = st.columns(2)
                            if col_yes.button("Ya, mulai", key=f"yes_stix_{sf['filename']}", type="primary"):
                                st.session_state.pop(f"confirm_reingest_stix_{sf['filename']}", None)
                                with st.spinner(
                                    f"Memproses {sf['filename']}... (bisa beberapa menit)"
                                ):
                                    result = reingest_stix(sf["filename"])
                                if "error" in result:
                                    st.error(result["error"])
                                else:
                                    st.success(
                                        f"✅ Selesai!\n\n"
                                        f"Dihapus: {result['deleted']} chunk lama\n\n"
                                        f"Diupload: {result['uploaded']} chunk baru"
                                    )
                                    _clear_cache()
                                    st.rerun()
                            if col_no.button("Batal", key=f"no_stix_{sf['filename']}"):
                                st.session_state.pop(f"confirm_reingest_stix_{sf['filename']}", None)
                                st.rerun()

                        st.divider()

                        # Hapus chunks dari Qdrant saja
                        if st.button("🗑️ Hapus dari Qdrant", key=f"del_stix_vec_{sf['filename']}"):
                            st.session_state[f"confirm_del_stix_{sf['filename']}"] = True

                        if st.session_state.get(f"confirm_del_stix_{sf['filename']}"):
                            st.warning("Semua chunks akan dihapus dari Qdrant (file tetap ada).")
                            col_yes2, col_no2 = st.columns(2)
                            if col_yes2.button("Ya, hapus", key=f"yes_del_stix_{sf['filename']}", type="primary"):
                                n = delete_chunks_by_doc_id(sf["doc_id"])
                                st.success(f"{n} chunks dihapus dari Qdrant.")
                                _clear_cache()
                                st.session_state.pop(f"confirm_del_stix_{sf['filename']}", None)
                                st.rerun()
                            if col_no2.button("Batal", key=f"no_del_stix_{sf['filename']}"):
                                st.session_state.pop(f"confirm_del_stix_{sf['filename']}", None)
                                st.rerun()

        st.divider()

        # --- Upload STIX baru ---
        st.subheader("Upload File STIX Baru")
        st.caption(
            "Upload file STIX JSON dari MITRE ATT&CK Navigator atau TAXII. "
            "Nama file standar: `enterprise-attack.json`, `mobile-attack.json`, `ics-attack.json`."
        )

        uploaded_stix = st.file_uploader(
            "Pilih file STIX JSON",
            type=["json"],
            accept_multiple_files=False,
            key="stix_uploader",
        )

        if uploaded_stix is not None:
            st.info(f"File dipilih: **{uploaded_stix.name}** ({uploaded_stix.size / 1024 / 1024:.1f} MB)")
            col_save, col_ingest = st.columns(2)

            if col_save.button("💾 Simpan File Saja", use_container_width=True):
                save_stix(uploaded_stix.name, uploaded_stix.getvalue())
                st.success(f"File `{uploaded_stix.name}` disimpan. Lakukan Ingest dari panel di atas.")
                _clear_cache()
                st.rerun()

            if col_ingest.button("🚀 Simpan & Ingest Sekarang", type="primary", use_container_width=True):
                save_stix(uploaded_stix.name, uploaded_stix.getvalue())
                with st.spinner("Memproses STIX... (bisa beberapa menit)"):
                    result = reingest_stix(uploaded_stix.name)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(
                        f"✅ **{uploaded_stix.name}** berhasil diingest!\n\n"
                        f"Chunks diupload ke Qdrant: **{result['uploaded']}**"
                    )
                    _clear_cache()
                    st.rerun()


# ---------------------------------------------------------------------------
# Halaman: Edit Metadata
# ---------------------------------------------------------------------------

def page_edit_metadata() -> None:
    st.title("✏️ Edit Metadata Dokumen")
    st.caption("Ubah metadata dokumen (judul, versi, incident types, dll). "
               "Setelah diubah, lakukan **Re-ingest** agar perubahan berlaku di Qdrant.")

    try:
        docs = _load_docs()
    except Exception as exc:
        st.error(f"Gagal memuat dokumen: {exc}")
        return

    if not docs:
        st.info("Belum ada dokumen terdaftar.")
        return

    doc_options = {f"{d.get('doc_title', d['doc_id'])} ({d['_meta_file']})": d for d in docs}
    selected_label = st.selectbox("Pilih Dokumen", options=list(doc_options.keys()))
    doc = doc_options[selected_label]

    st.divider()

    with st.form("form_edit_meta"):
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Judul Dokumen *", value=doc.get("doc_title", ""))
            new_framework = st.selectbox(
                "Source Framework *",
                options=_SOURCE_FRAMEWORK_OPTIONS,
                index=_SOURCE_FRAMEWORK_OPTIONS.index(doc.get("source_framework", "NIST"))
                if doc.get("source_framework") in _SOURCE_FRAMEWORK_OPTIONS else 0,
            )
            new_version = st.text_input("Versi", value=doc.get("version", ""))

        with col2:
            new_language = st.selectbox(
                "Bahasa",
                options=["en", "id"],
                index=0 if doc.get("language", "en") == "en" else 1,
            )
            current_types = doc.get("incident_types", [])
            new_incident_types = st.multiselect(
                "Tipe Insiden *",
                options=_INCIDENT_TYPE_OPTIONS,
                default=[t for t in current_types if t in _INCIDENT_TYPE_OPTIONS],
            )

        st.info("⚠️ **Doc ID** dan **nama file PDF** tidak dapat diubah di sini "
                "(ubah langsung di file JSON jika diperlukan).")

        save_btn = st.form_submit_button("💾 Simpan Metadata", type="primary", use_container_width=True)

    if save_btn:
        if not new_title.strip() or not new_incident_types:
            st.error("Judul dan tipe insiden wajib diisi.")
        else:
            updated_meta = {
                **{k: v for k, v in doc.items() if not k.startswith("_")},
                "doc_title": new_title.strip(),
                "source_framework": new_framework,
                "version": new_version.strip(),
                "language": new_language,
                "incident_types": new_incident_types,
            }
            save_metadata(doc["_meta_file"], updated_meta)
            st.success(
                f"✅ Metadata **{doc['_meta_file']}** disimpan.\n\n"
                "Lakukan **Re-ingest** dari halaman *Kelola Dokumen* agar perubahan berlaku di Qdrant."
            )
            _clear_cache()


# ---------------------------------------------------------------------------
# Halaman: Cari & Preview Chunks
# ---------------------------------------------------------------------------

def page_search_chunks() -> None:
    st.title("🔍 Cari & Preview Chunks")
    st.caption("Uji pencarian knowledge base menggunakan full-text search (tanpa API embedding).")

    query = st.text_input(
        "Kata kunci pencarian",
        placeholder="contoh: ransomware containment isolate endpoint",
    )
    top_k = st.slider("Jumlah hasil maksimal", min_value=5, max_value=50, value=10, step=5)

    if st.button("🔍 Cari", type="primary", disabled=not query.strip()):
        with st.spinner("Mencari..."):
            results = search_chunks(query.strip(), top_k=top_k)

        if not results:
            st.info("Tidak ada hasil ditemukan.")
            return

        if "error" in results[0]:
            st.error(f"Error: {results[0]['error']}")
            return

        st.success(f"Ditemukan {len(results)} chunk")

        for i, r in enumerate(results, 1):
            framework = r.get("source_framework", "")
            doc_title = r.get("doc_title", r.get("doc_id", "-"))
            section = r.get("section_header", "")
            label = f"[{i}] {framework} — {doc_title}"
            if section:
                label += f" · {section}"

            with st.expander(label, expanded=(i <= 3)):
                st.markdown(f"**Doc ID:** `{r.get('doc_id', '-')}` | **Chunk:** #{r.get('chunk_index', '?')} | **ID:** `{r.get('id', '-')}`")
                st.text_area(
                    "Konten",
                    value=r.get("content", ""),
                    height=160,
                    key=f"chunk_{i}_{r.get('id', i)}",
                    disabled=True,
                )


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    with st.sidebar:
        st.title("📚 RAG Manager")
        st.caption("Knowledge Base\nHelpdesk Keamanan Siber")
        st.divider()

        page = st.radio(
            "Navigasi",
            options=["Status Collection", "Kelola Dokumen", "Edit Metadata", "Cari & Preview Chunks"],
            index=0,
        )

        st.divider()

        # Quick Qdrant connection check
        try:
            info = get_collection_info()
            if "error" in info:
                st.error(f"Qdrant: Error\n{info['error'][:60]}")
            else:
                total = info.get("total_vectors", 0)
                st.success(f"Qdrant: Online\n{total:,} chunks")
        except Exception:
            st.error("Qdrant: Offline")

        st.caption("Qdrant URL: " + __import__("os").getenv("QDRANT_URL", "http://localhost:6333"))

        st.divider()
        st.markdown("🛡️ [← Kembali ke Dashboard Tiket](http://localhost:8501)")

    if page == "Status Collection":
        page_status()
    elif page == "Kelola Dokumen":
        page_kelola_dokumen()
    elif page == "Edit Metadata":
        page_edit_metadata()
    elif page == "Cari & Preview Chunks":
        page_search_chunks()


if __name__ == "__main__":
    main()
