# Code Overview — pusdatin-help

> Dokumen ini merangkum tujuan tiap file kode dalam proyek dan alasan di balik struktur yang dipilih.
> Dibuat untuk keperluan review sistematis. Terakhir diperbarui: 2026-04-10.

---

## Mengapa Struktur Ini?

Proyek ini adalah sistem **multi-agent** dengan tiga entry point berbeda (bot Telegram, API REST, dashboard web). Struktur folder memisahkan tiap concern agar tidak saling bergantung:

```
pusdatin-help/
├── app/            ← kode utama aplikasi
│   ├── agents/     ← logika LangGraph (otak sistem)
│   ├── api/        ← REST API (jembatan bot ↔ backend)
│   ├── dashboard/  ← UI admin (Streamlit)
│   ├── database/   ← ORM, migrasi, repository pattern
│   ├── rag/        ← pipeline Retrieval-Augmented Generation
│   ├── security/   ← lapisan keamanan input/output
│   ├── telegram/   ← bot handler
│   └── utils/      ← helper lintas modul
├── config/prompts/ ← template prompt LLM (pisah dari kode)
├── knowledge_base/ ← dokumen sumber RAG
├── scripts/        ← utilitas CLI (ingest, test manual)
├── tests/          ← pytest (cermin struktur app/)
└── docs/           ← arsitektur & panduan
```

**Prinsip utama:** setiap agen berkomunikasi hanya lewat `IncidentState` (bukan langsung), sehingga tiap agen bisa diuji dan diganti secara independen.

---

## `app/` — Inti Aplikasi

### `app/main.py`
Entry point FastAPI. Mendaftarkan router, mengatur CORS, dan inisialisasi awal (koneksi DB, dsb). Dijalankan dengan `uvicorn app.main:app`.

### `app/config.py`
Memuat semua konfigurasi dari environment variable menggunakan `pydantic-settings`. Satu-satunya tempat yang boleh membaca `.env`. Modul lain import `settings` dari sini — tidak boleh membaca `os.environ` langsung.

### `app/constants.py`
Single source of truth untuk string konstan: status tiket, level severity, level eskalasi, label badge. Mencegah magic string tersebar di banyak file dan mempermudah perubahan label di satu tempat.

---

## `app/agents/` — Pipeline Multi-Agent (LangGraph)

Ini adalah inti sistem. LangGraph memodelkan pipeline sebagai graf berarah di mana setiap node adalah agen dengan tanggung jawab tunggal.

### `app/agents/state.py`
Mendefinisikan `IncidentState` — TypedDict yang menjadi satu-satunya medium komunikasi antar agen. Semua data insiden (input, klasifikasi, rekomendasi, tiket) ada di sini. **Tidak boleh diubah sembarangan** karena semua agen bergantung pada struktur ini.

### `app/agents/graph.py`
Merakit graf LangGraph: mendaftarkan node (agen) dan edge (alur). Di sinilah urutan eksekusi pipeline ditentukan. Juga titik masuk utama untuk memproses satu pesan insiden dari awal sampai selesai (`run_pipeline()`).

### `app/agents/orchestrator.py`
Agen pertama dalam pipeline. Menerima input mentah dari pengguna, membersihkan konteks, dan memutuskan apakah perlu lanjut ke agen berikutnya atau sudah cukup dijawab langsung (untuk pertanyaan umum). Menggunakan prompt dari `config/prompts/orchestrator.txt`.

### `app/agents/identifier.py`
Agen klasifikasi insiden. Menganalisis deskripsi dan menentukan: jenis insiden (phishing, malware, dll.), tingkat keparahan (low/medium/high/critical), dan apakah butuh eskalasi ke CSIRT. Menggunakan prompt dari `config/prompts/identifier.txt`.

### `app/agents/mitigation.py`
Agen rekomendasi mitigasi. Memanggil RAG retriever untuk mencari dokumen relevan (NIST, MITRE ATT&CK), lalu menghasilkan langkah mitigasi konkret menggunakan LLM. Menggunakan prompt dari `config/prompts/mitigation.txt`.

### `app/agents/ticket_manager.py`
Agen pembuatan tiket. Setelah insiden diklasifikasi dan rekomendasi dibuat, agen ini menyimpan tiket ke PostgreSQL dengan status awal `PENDING_REVIEW`. Memastikan audit trail tersimpan.

### `app/agents/notifier.py`
Agen notifikasi. Mengirim ringkasan tiket ke grup Telegram CSIRT (jika eskalasi diperlukan) dan/atau membalas pengguna dengan hasil analisis. Agen terakhir dalam pipeline.

---

## `app/api/` — REST API (FastAPI)

Layer ini memisahkan bot Telegram dari logika bisnis. Bot tidak langsung memanggil agen — selalu lewat HTTP API.

### `app/api/routes.py`
Mendefinisikan semua endpoint REST: `/chat` (proses pesan), `/tickets` (CRUD tiket), `/health`. Tiap endpoint memanggil pipeline agen atau repository database. Error 500 menyertakan trace ID untuk debugging.

### `app/api/schemas.py`
Pydantic schema untuk request/response body API. Memvalidasi input sebelum masuk ke logika bisnis dan memastikan output terstruktur. Pisah dari model ORM database.

### `app/api/dependencies.py`
FastAPI dependency injection: session database, instance repository, dsb. Memastikan resource dibuat dan dibersihkan dengan benar per request (terutama koneksi DB).

---

## `app/dashboard/` — UI Admin (Streamlit)

Dashboard untuk analis CSIRT: melihat tiket masuk, update status, kelola knowledge base RAG.

### `app/dashboard/main.py`
Halaman utama dashboard admin. Layout email-like: sidebar navigasi + inbox dua kolom (daftar tiket kiri, detail kanan). Fitur: notifikasi `st.toast()` tiket baru, badge status berwarna, update status tiket, tab buat laporan insiden, kirim laporan ke CSIRT via Telegram.

### `app/dashboard/api_client.py`
HTTP client (httpx) untuk dashboard berkomunikasi dengan FastAPI backend. Mengabstraksi semua `requests.get/post` ke fungsi bernama jelas (`get_tickets()`, `update_ticket()`, dsb). Dashboard tidak boleh akses DB langsung.

### `app/dashboard/rag_client.py`
HTTP client khusus untuk operasi RAG: list dokumen di Qdrant, upload PDF baru, delete dokumen, re-ingest file STIX/ATT&CK. Memanggil Qdrant API dan filesystem lokal.

### `app/dashboard/rag_manager.py`
Halaman Streamlit untuk manajemen knowledge base: lihat status koleksi Qdrant, upload dokumen PDF, kelola file STIX MITRE ATT&CK (list/upload/reingest/delete). Diakses dari sidebar dashboard utama.

### `app/dashboard/report_generator.py`
Menghasilkan laporan insiden formal dalam format HTML. Berisi branding Kementan, ringkasan eksekutif, tabel detail insiden, rekomendasi mitigasi, timeline, dan blok tanda tangan. Output bisa diunduh atau dikirim ke CSIRT via Telegram.

---

## `app/database/` — Persistensi Data

### `app/database/models.py`
SQLAlchemy ORM models: `IncidentTicket`, `AuditLog`, dsb. Mendefinisikan skema tabel PostgreSQL. Digunakan oleh Alembic untuk generate migrasi.

### `app/database/connection.py`
Inisialisasi SQLAlchemy engine dan session factory. Satu tempat untuk konfigurasi koneksi (pool size, timeout, dsb).

### `app/database/repository.py`
Repository pattern: semua query database dikapsulasi di sini (`create_ticket()`, `get_tickets()`, `update_ticket()`, dsb.). Modul lain tidak boleh menulis SQL/ORM query sendiri — selalu lewat repository.

### `app/database/migrations/env.py`
Konfigurasi Alembic untuk migrasi database. Memuat `.env` eksplisit agar `DATABASE_URL` terbaca saat `alembic upgrade head` dijalankan dari CLI.

### `app/database/migrations/versions/f326b3b5253b_initial_tables.py`
Migrasi pertama: membuat tabel awal (`incident_tickets`, `audit_logs`). Dijalankan sekali saat setup.

---

## `app/rag/` — Retrieval-Augmented Generation

Pipeline RAG: dokumen → chunk → embed → simpan di Qdrant → retrieve saat query.

### `app/rag/ingestion.py`
Memuat dokumen dari file (PDF → `PyPDFLoader`, STIX JSON → parser custom) dan menyimpan embedding ke Qdrant. Fungsi `ingest_attack_stix()` khusus menangani format graf STIX MITRE ATT&CK (attack-pattern, course-of-action, relationship).

### `app/rag/chunker.py`
Memecah dokumen panjang menjadi chunk dengan overlap menggunakan `RecursiveCharacterTextSplitter`. Ukuran chunk dikonfigurasi — terlalu kecil kehilangan konteks, terlalu besar noise retrieval.

### `app/rag/embedder.py`
Wrapper untuk `text-embedding-3-small` OpenAI. Mengkonversi teks menjadi vektor float. Digunakan saat ingest (embed dokumen) dan saat query (embed pertanyaan).

### `app/rag/retriever.py`
Mengambil chunk paling relevan dari Qdrant berdasarkan similarity vektor. Output: daftar `Document` dengan konten dan metadata. Hasilnya masuk ke `mitigation.py` sebagai konteks LLM.

### `app/rag/reranker.py`
Opsional: re-ranking hasil retrieval menggunakan cross-encoder atau skor LLM. Meningkatkan presisi — dari top-10 retrieval jadi top-3 yang paling relevan. Meningkatkan faithfulness RAG.

---

## `app/security/` — Lapisan Keamanan Input/Output

Setiap pesan pengguna melewati lapisan ini sebelum masuk ke pipeline agen. Fail-closed: jika guardrail gagal, request diblokir.

### `app/security/guardrails.py`
Koordinator keamanan: menjalankan semua check keamanan secara berurutan (sanitize → validate → PII redact → prompt injection check). Return `(is_safe, reason)`. Dipanggil di awal `graph.py`.

### `app/security/sanitizer.py`
Membersihkan input dari karakter berbahaya, HTML tags, dan kontrol karakter sebelum diproses lebih lanjut.

### `app/security/validator.py`
Memvalidasi input: panjang maksimum, format yang diizinkan, karakter yang dilarang. Menolak input yang jelas-jelas tidak valid sebelum menyentuh LLM.

### `app/security/pii_redactor.py`
Mendeteksi dan meredaksi PII (Personally Identifiable Information): nama, nomor telepon, email, IP address, sebelum teks dikirim ke OpenAI API. Wajib karena data pengguna tidak boleh keluar ke third-party.

### `app/security/prompt_injection.py`
Mendeteksi upaya prompt injection: instruksi tersembunyi dalam input pengguna yang mencoba mengubah perilaku LLM ("ignore previous instructions", dsb.).

---

## `app/telegram/` — Bot Handler

### `app/telegram/bot.py`
Handler bot Telegram menggunakan `python-telegram-bot`. Menerima pesan dari pengguna, meneruskan ke FastAPI via HTTP, dan menampilkan respons balik ke chat. Menangani `/start`, pesan teks, dan file upload.

### `app/telegram/templates.py`
Template pesan Telegram (format Markdown/HTML). Memisahkan teks UI dari logika handler — jika teks perlu diubah, tidak perlu sentuh `bot.py`.

---

## `app/utils/` — Helper Lintas Modul

### `app/utils/llm_client.py`
Singleton wrapper untuk OpenAI client. Mengelola API key, retry logic, dan timeout. Semua agen memanggil LLM lewat sini — tidak ada yang instantiate `openai.OpenAI()` sendiri.

### `app/utils/llm_parser.py`
Parsing output LLM menjadi Python dict/object. Menangani kasus LLM mengembalikan JSON tidak valid (dengan fallback atau retry). Semua output LLM harus melewati parser ini.

### `app/utils/prompt_loader.py`
Memuat template prompt dari file `config/prompts/*.txt` dan mengganti placeholder (`{variable}`) dengan nilai aktual. Prompt tidak boleh hardcode di dalam kode agen.

### `app/utils/audit.py`
Mencatat event penting ke tabel `audit_logs` (tiket dibuat, status diupdate, eskalasi terjadi). Menggunakan `asyncio.to_thread()` agar tidak memblokir event loop async.

### `app/utils/logger.py`
Konfigurasi logging terpusat. Semua modul menggunakan `logging.getLogger(__name__)` — tidak ada `print()` di kode produksi.

---

## `config/prompts/` — Template Prompt LLM

Prompt dipisah dari kode agar bisa diubah tanpa deploy ulang dan mudah di-version control.

| File | Digunakan oleh | Tujuan |
|------|---------------|--------|
| `orchestrator.txt` | `orchestrator.py` | Memutuskan apakah input butuh pipeline penuh atau cukup dijawab langsung |
| `identifier.txt` | `identifier.py` | Mengklasifikasi jenis insiden, severity, dan kebutuhan eskalasi |
| `mitigation.txt` | `mitigation.py` | Menghasilkan rekomendasi mitigasi berdasarkan konteks RAG |

---

## `knowledge_base/` — Sumber Dokumen RAG

| File/Folder | Isi |
|-------------|-----|
| `documents/` | PDF yang diingest ke Qdrant (NIST SP 800-61 r2 & r3) |
| `enterprise-attack.json` | MITRE ATT&CK Enterprise STIX bundle (graf teknik serangan + mitigasi) |
| `metadata/` | JSON metadata dokumen (judul, versi, tanggal) untuk Qdrant payload |

---

## `scripts/` — Utilitas CLI

Script satu kali pakai atau maintenance. Tidak masuk ke distribusi produksi.

| File | Tujuan |
|------|--------|
| `ingest_knowledge.py` | Menjalankan ingestion semua dokumen ke Qdrant (setup awal / re-ingest) |
| `run_bot.py` | Menjalankan bot Telegram secara standalone (tanpa uvicorn) |
| `e2e_test.py` | Tes end-to-end: kirim pesan simulasi dan cek tiket terbuat |
| `test_identifier.py` | Tes manual agen identifier dengan contoh kasus |
| `test_mitigation.py` | Tes manual agen mitigation dengan query langsung |
| `test_pipeline.py` | Tes manual seluruh pipeline dari input sampai notifikasi |

---

## `tests/` — Pytest Test Suite

Mencerminkan struktur `app/` agar mudah dinavigasi. Setiap modul punya test file sendiri.

### `tests/test_agents/`
| File | Yang diuji |
|------|-----------|
| `test_graph.py` | Alur graf LangGraph: node terpanggil urut, state terisi benar |
| `test_identifier.py` | Klasifikasi insiden: output JSON valid, field lengkap |
| `test_mitigation.py` | Rekomendasi: context retrieval, format output |
| `test_notifier.py` | Pengiriman notifikasi Telegram (mock) |
| `test_orchestrator.py` | Keputusan routing orchestrator |
| `test_ticket_manager.py` | Pembuatan tiket: status awal PENDING_REVIEW, data tersimpan |

### `tests/test_database/`
| File | Yang diuji |
|------|-----------|
| `test_repository.py` | CRUD tiket, query filter, update status |

### `tests/test_rag/`
| File | Yang diuji |
|------|-----------|
| `test_chunker.py` | Ukuran chunk, overlap, batas karakter |
| `test_ingestion.py` | Ingest PDF dan STIX, jumlah dokumen yang dihasilkan |
| `test_reranker.py` | Urutan hasil reranking |
| `test_retriever.py` | Relevansi hasil retrieval untuk query contoh |

### `tests/test_security/`
| File | Yang diuji |
|------|-----------|
| `test_guardrails.py` | Input berbahaya diblokir, input valid lolos |
| `test_pii_redactor.py` | Email/telepon/IP terdeteksi dan diredaksi |
| `test_prompt_injection.py` | Pola injection umum terdeteksi |
| `test_sanitizer.py` | Karakter berbahaya dibersihkan |
| `test_validator.py` | Validasi panjang dan format input |

### `tests/test_telegram/`
| File | Yang diuji |
|------|-----------|
| `test_bot.py` | Handler pesan, routing ke API, format respons |

### `tests/evaluation/`
Script evaluasi kuantitatif untuk metrik skripsi (bukan pytest biasa):

| File | Metrik |
|------|--------|
| `eval_rag.py` | Context Relevance, Answer Relevance, Faithfulness (target ≥ 0.75/0.80/0.85) |
| `eval_tcr.py` | Task Completion Rate — berapa % skenario selesai tanpa error (target ≥ 80%) |
| `eval_report.py` | Kualitas laporan yang dihasilkan (kelengkapan field, format) |

---

## File Konfigurasi & Infrastruktur

| File | Tujuan |
|------|--------|
| `docker-compose.yml` | Mendefinisikan container: PostgreSQL, Redis, Qdrant. FastAPI/bot/dashboard dijalankan lokal. |
| `Dockerfile` | Image Docker untuk FastAPI (opsional, saat full Docker deploy) |
| `alembic.ini` | Konfigurasi Alembic (path migrasi, logging). URL DB dibaca dari env, bukan dari file ini. |
| `requirements.txt` | Semua dependency Python dengan versi pin |
| `pytest.ini` | Konfigurasi pytest: test path, marker, coverage |
| `.env.example` | Template variabel environment — salin ke `.env` dan isi nilainya |
| `.env` | Variabel aktual (tidak di-commit ke git) |

---

## Diagram Alur Data Singkat

```
Pengguna (Telegram)
    │
    ▼
bot.py ──HTTP──► routes.py (FastAPI)
                    │
                    ▼
              guardrails.py  ← blokir jika tidak aman
                    │
                    ▼
              graph.py (LangGraph)
               ├── orchestrator.py  → putuskan routing
               ├── identifier.py   → klasifikasi + severity
               ├── mitigation.py   → RAG retrieval + rekomendasi
               ├── ticket_manager.py → simpan ke PostgreSQL
               └── notifier.py     → kirim ke Telegram CSIRT
```

---

*Untuk detail arsitektur lebih dalam, lihat `docs/MASTERPLAN.md` dan `docs/PHASE_GUIDE.md`.*
