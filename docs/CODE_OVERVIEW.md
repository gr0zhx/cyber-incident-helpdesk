# Code Overview v2 — pusdatin-help

> Dokumen komprehensif untuk persiapan sidang skripsi: penjelasan **setiap file, setiap fungsi, setiap class**, logika internal, dan keterkaitan antar-modul.
> Target pembaca: penulis (recall cepat) dan dosen penguji (verifikasi teknis).
> Terakhir diperbarui: 2026-06-06 (Sinkronisasi dokumentasi dengan keadaan kode hari ini).

---

## Daftar Isi

1. [Gambaran Umum Sistem](#1-gambaran-umum-sistem)
2. [Keputusan Arsitektural Utama](#2-keputusan-arsitektural-utama)
3. [Struktur Folder Lengkap](#3-struktur-folder-lengkap)
4. [Alur Data End-to-End](#4-alur-data-end-to-end)
5. [app/main.py & app/config.py & app/constants.py](#5-appmainpy--appconfigpy--appconstantspy)
6. [app/agents/ — Multi-Agent LangGraph](#6-appagents--multi-agent-langgraph)
7. [app/rag/ — Retrieval-Augmented Generation](#7-apprag--retrieval-augmented-generation)
8. [app/security/ — Guardrails Berlapis](#8-appsecurity--guardrails-berlapis)
9. [app/database/ — Persistence Layer](#9-appdatabase--persistence-layer)
10. [app/api/ — REST API](#10-appapi--rest-api)
11. [app/telegram/ — Bot Interface](#11-apptelegram--bot-interface)
12. [app/web/ — Web Interface (HTMX)](#12-appweb--web-interface-htmx)
13. [app/utils/ — Utilitas Internal](#13-apputils--utilitas-internal)
14. [config/prompts/ — Template Prompt LLM](#14-configprompts--template-prompt-llm)
15. [scripts/ — CLI Tools](#15-scripts--cli-tools)
16. [tests/ — Test Suite](#16-tests--test-suite)
17. [Infrastruktur & Deployment](#17-infrastruktur--deployment)
18. [Peta Interaksi Modul](#18-peta-interaksi-modul)
19. [Security Audit & Fixes (2026-04-21)](#19-security-audit--fixes-2026-04-21)
20. [Tabel Q&A Sidang](#20-tabel-qa-sidang)
21. [Perubahan Terbaru (2026-05-30)](#21-perubahan-terbaru-2026-05-30)
22. [Perubahan Terbaru (2026-06-02)](#22-perubahan-terbaru-2026-06-02)

---

## 1. Gambaran Umum Sistem

**Nama Sistem:** Sistem Helpdesk Keamanan Siber Multi-Agent Pusdatin Kementan (prototipe skripsi).

**Tujuan:** Otomatisasi **pra-triase** insiden siber dari pelapor awam ke tim CSIRT. Sistem menerima laporan via tiga kanal — Telegram Bot, Web Chat (HTMX), dan REST API — kemudian:
1. Memfilter input berbahaya (guardrails fail-closed).
2. Mengklasifikasikan intent dan jenis insiden + severity via LLM.
3. Menghasilkan rekomendasi mitigasi dari knowledge base (NIST SP 800-61 + MITRE ATT&CK) via **Agentic RAG**.
4. Membuat tiket di PostgreSQL dengan `status=PENDING_REVIEW`.
5. Mengirim notifikasi ke pelapor dan grup CSIRT via Telegram.

**Kontribusi utama skripsi:**
| # | Kontribusi | Implementasi |
|---|-----------|-------------|
| 1 | **Arsitektur multi-agent** dengan LangGraph | `app/agents/graph.py` |
| 2 | **Agentic RAG** iteratif (max 3 putaran, adequacy check) | `app/agents/mitigation.py` |
| 3 | **Hybrid retrieval** (semantic + keyword) + RRF | `app/rag/retriever.py` |
| 4 | **Guardrails fail-closed** berlapis | `app/security/guardrails.py` |
| 5 | **Citation validation** untuk faithfulness | `app/agents/mitigation.py` |

**Metrik target:** TCR ≥ 80%, RAG (CR ≥ 0.75 / AR ≥ 0.80 / Faith ≥ 0.85), SUS ≥ 68.

---

## 2. Keputusan Arsitektural Utama

### 2.1 Mengapa LangGraph, bukan chain linear?

LangGraph memodelkan pipeline sebagai **directed graph** dengan shared state. Keuntungan:
- **Conditional routing eksplisit** — node `guardrails` bisa short-circuit ke `END` bila input tidak aman. Node `orchestrator` bisa bercabang ke `identifier` atau langsung ke `notifier`.
- **State-driven** — tiap node hanya baca/tulis subset field di `IncidentState`.
- **Testable per node** — cukup mock state, panggil satu node, assert output.
- **Visualisasi alur** — graf bisa digambar, membantu debugging dan presentasi sidang.

Alternatif yang ditolak: chain linear LangChain (tidak bisa conditional routing), function call manual (duplikasi glue code, sulit di-test).

### 2.2 Mengapa `IncidentState` (TypedDict) sebagai satu-satunya medium komunikasi?

Agar tiap agen bersifat **murni sebagai fungsi** `(state) → state'`:
- Tidak ada side-effect tersembunyi antar node.
- Audit lengkap: seluruh histori konteks ada di satu objek.
- Testable — cukup buat dummy state, panggil node, assert.

Aturan ketat: **tidak boleh ubah schema `IncidentState` tanpa alasan kuat** (tercantum di `CLAUDE.md`).

### 2.3 Mengapa Agentic RAG, bukan naive RAG satu-shot?

**Masalah naive RAG:** query user sering ambigu ("website saya aneh") — retrieval pertama tidak relevan.

**Agentic RAG yang diterapkan** di `mitigation.py`:
1. Retrieve top-20 chunk.
2. Rerank ke top-5.
3. **Adequacy check** — cek skor chunk ≥ threshold.
4. Jika tidak cukup: **expand query** dengan kata kunci lebih spesifik, iterasi ulang.
5. Maksimal 3 iterasi.
6. Generate rekomendasi dari konteks terpilih.
7. **Citation validation** — step yang tidak ada sumbernya di chunk dibuang.

### 2.4 Mengapa Hybrid Retrieval + RRF?

| Metode | Kelebihan | Kekurangan |
|--------|-----------|------------|
| Semantic (vector) | Parafrase & sinonim | Istilah teknis (CVE, M1040) sering meleset |
| Keyword (BM25) | Istilah teknis persis | Gagal untuk sinonim |
| **RRF (gabungan)** | Menutupi kelemahan masing-masing | — |

Formula: `RRF_score(d) = Σ 1 / (k + rank_i(d))` dengan `k = 60`.

Reranker akhir: `final = 0.7 × cosine + 0.3 × norm_rrf + 0.10 × incident_type_boost`.

### 2.5 Mengapa guardrails fail-closed?

Prinsip "deny by default": bila salah satu check gagal → pipeline dihentikan, pesan ditolak. Tiga lapisan di `guardrails.py`:
1. Sanitize HTML + kontrol karakter.
2. Prompt injection detection (regex + base64 heuristic).
3. PII redaction (IP, email, NIK, telepon Indonesia).

### 2.6 Mengapa prompt dipisahkan ke `config/prompts/*.txt`?

- Tidak perlu deploy ulang untuk tuning prompt.
- Diff prompt terbaca jelas di git.
- Mudah A/B testing — ganti file, jalankan evaluasi.

### 2.7 Mengapa Repository Pattern untuk database?

Semua query SQL/ORM dikapsulasi di `repository.py`. Modul lain tidak boleh menulis query sendiri:
- Satu tempat untuk optimasi.
- Mock mudah di unit test.
- `create_ticket()` selalu set `status=PENDING_REVIEW` sebagai default — konsisten.

### 2.8 Mengapa ada dua UI (Web HTMX + Telegram Bot)?

- **Bot Telegram** — kanal pelaporan utama (familiar bagi pelapor awam, tidak butuh akun).
- **Web HTMX** — kanal alternatif + dashboard admin CSIRT (tanpa build React).
- **REST API** — untuk integrasi, testing, dan evaluasi otomatis.
- Streamlit dihapus; web HTMX lebih ringan dan tidak butuh proses terpisah.

---

## 3. Struktur Folder Lengkap

```

pusdatin-help/
├── app/
│   ├── agents/             ← LangGraph nodes + state (otak sistem)
│   │   ├── state.py        ← IncidentState TypedDict
│   │   ├── graph.py        ← Perakitan graf + routing + node factories
│   │   ├── orchestrator.py ← Klasifikasi intent (4 kelas)
│   │   ├── identifier.py   ← Klasifikasi jenis insiden + severity
│   │   ├── mitigation.py   ← Agentic RAG (jantung skripsi)
│   │   ├── ticket_manager.py ← Buat tiket PostgreSQL
│   │   └── notifier.py     ← Kirim notifikasi Telegram
│   │
│   ├── api/                ← REST API (FastAPI)
│   │   ├── routes.py       ← 6 endpoint REST
│   │   ├── schemas.py      ← Pydantic request/response models
│   │   └── dependencies.py ← DI: graph, orchestrator, DB session
│   │
│   ├── database/           ← Persistence layer
│   │   ├── models.py       ← SQLAlchemy: IncidentTicket, AuditLog, Admin, TicketAttachment
│   │   ├── repository.py   ← TicketRepository + AuditRepository
│   │   ├── connection.py   ← Engine + session factory + get_db()
│   │   └── migrations/     ← Alembic: initial_tables + env.py
│   │
│   ├── rag/                ← RAG pipeline
│   │   ├── ingestion.py    ← PDF + MITRE ATT&CK STIX loader
│   │   ├── chunker.py      ← RecursiveCharacterTextSplitter
│   │   ├── embedder.py     ← OpenAI text-embedding-3-small + Qdrant upload
│   │   ├── retriever.py    ← HybridRetriever (semantic + keyword + RRF)
│   │   └── reranker.py     ← Custom reranker (cosine + RRF + type boost)
│   │
│   ├── security/           ← Guardrails berlapis
│   │   ├── guardrails.py   ← Orchestrator: sanitize → inject → PII
│   │   ├── sanitizer.py    ← Strip HTML, kontrol karakter
│   │   ├── prompt_injection.py ← Regex + base64 heuristic
│   │   ├── pii_redactor.py ← 4 regex: IP, email, NIK, telepon
│   │   └── validator.py    ← OutputValidator: cek PII di output LLM
│   │
│   ├── telegram/           ← Telegram Bot (PTB)
│   │   ├── bot.py          ← Handlers + ConversationHandler + build_bot_application()
│   │   └── templates.py    ← format_csirt_alert(), format_reporter_confirmation()
│   │
│   ├── web/                ← Web interface (FastAPI + Jinja2 + HTMX)
│   │   ├── app.py          ← register_web(): middleware + routers
│   │   ├── config.py       ← WebConfig: session, upload, rate limit, CSRF
│   │   ├── constants.py    ← AuditEvents, TICKET_STATUSES, ESCALATION_LEVELS
│   │   ├── dependencies.py ← get_current_admin(), get_reporter_session()
│   │   ├── middleware/
│   │   │   ├── csrf.py         ← CSRFMiddleware (double-submit)
│   │   │   ├── security_headers.py ← X-Frame-Options, CSP, dll.
│   │   │   └── rate_limit.py   ← slowapi limiter
│   │   ├── routes/
│   │   │   ├── landing.py      ← GET /
│   │   │   ├── pelapor.py      ← /lapor (identitas, chat, file upload)
│   │   │   ├── admin_auth.py   ← /admin/login, /admin/logout
│   │   │   ├── admin_inbox.py  ← /admin/inbox, /admin/tiket/{id}
│   │   │   ├── admin_actions.py← /admin/tiket/{id}/aksi (update, assign, eskalasi)
│   │   │   ├── admin_rag.py    ← /admin/rag (ingest PDF/STIX, lihat koleksi)
│   │   │   └── admin_report.py ← /admin/tiket/{id}/laporan (download HTML)
│   │   └── services/
│   │       ├── auth_service.py   ← AuthService: bcrypt + Redis lockout
│   │       ├── chat_service.py   ← ChatService: multi-turn + ainvoke pipeline
│   │       ├── report_service.py ← ReportService: generate HTML report
│   │       └── upload_service.py ← UploadService: validasi + simpan file
│   │
│   ├── utils/              ← Utilitas internal
│   │   ├── llm_client.py   ← create_llm_client() + create_embedder()
│   │   ├── llm_parser.py   ← parse_llm_json() robust
│   │   ├── prompt_loader.py← load_prompt(agent_name)
│   │   ├── audit.py        ← log_audit_event() async fire-and-forget
│   │   └── logger.py       ← configure_logging() + get_logger()
│   │
│   ├── config.py           ← Settings (pydantic-settings) + get_settings()
│   ├── constants.py        ← Status, severity, badge colors, label Telegram
│   └── main.py             ← Entry FastAPI: lifespan, router, health
│
├── config/prompts/
│   ├── orchestrator.txt    ← Prompt intent classification
│   ├── identifier.txt      ← Prompt jenis insiden + severity
│   └── mitigation.txt      ← Prompt generasi mitigasi dari RAG context
│
├── knowledge_base/         ← PDF NIST SP 800-61 + STIX MITRE ATT&CK
├── scripts/
│   ├── ingest_knowledge.py ← CLI: ingest PDF + STIX ke Qdrant
│   ├── seed_admin.py       ← CLI: buat admin pertama
│   └── e2e_test.py         ← E2E test via REST API
│
├── tests/                  ← pytest (cermin struktur app/)
│   ├── test_agents/        ← 6 file (tiap node LangGraph)
│   ├── test_rag/           ← 4 file (chunker, ingestion, retriever, reranker)
│   ├── test_security/      ← 5 file (guardrails, sanitizer, PII, injection, validator)
│   ├── test_database/      ← 1 file (repository CRUD + stats)
│   ├── test_telegram/      ← 1 file (bot handlers)
│   ├── test_web/           ← 30+ file (routes, services, middleware, integrasi)
│   └── evaluation/         ← eval_rag.py, eval_tcr.py, eval_report.py
│       │                      eval_ragas.py (baru), rag_qa_dataset.json
│       │                      rag_results.json (baru), rag_ragas_results.json (baru)
│
├── docker-compose.yml      ← PostgreSQL, Redis, Qdrant
├── Dockerfile              ← Image FastAPI
├── alembic.ini             ← Konfigurasi Alembic
├── requirements.txt        ← Dependency pinned
├── pytest.ini              ← Config pytest
└── .env.example            ← Template env vars

```

---

## 4. Alur Data End-to-End

```

┌─────────────────────────────────────────────────────────────────────┐
│              Kanal Input (pilih salah satu)                         │
│  Telegram Bot    Web Chat (HTMX)    REST API POST /api/v1/report    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ raw_input + reporter_info
                                ▼
                    orchestrator.initialize_state()
                    → IncidentState (semua field default kosong)
                                │
                                ▼
                ┌── app/agents/graph.py (LangGraph) ──────────────────┐
                │                                                      │
                │  START                                               │
                │    │                                                 │
                │    ▼                                                 │
                │  guardrails_node                                     │
                │    │ sanitize → inject? → PII redact                 │
                │    ├──(blocked)──────────────────────► END (tolak)  │
                │    │ aman                                            │
                │    ▼                                                 │
                │  classify_intent (orchestrator_node)                 │
                │    │ intent ∈ {query_status, general_help, clarify} │
                │    ├──(bukan report_incident)──────────► notifier   │
                │    │ report_incident                                 │
                │    ▼                                                 │
                │  identify_incident (identifier_node)                 │
                │    │ → incident_type + severity + confidence         │
                │    ▼                                                 │
                │  generate_mitigation (mitigation_node)               │
                │    │ [Agentic RAG Loop max 3×]:                      │
                │    │   retrieve(top_k=20) → rerank(top_k=5)         │
                │    │   adequacy_check → expand_query? → ulang        │
                │    │   generate_recommendation                       │
                │    │   validate_citations                            │
                │    ▼                                                 │
                │  validate_output                                     │
                │    │ cek PII bocor di output LLM                    │
                │    ▼                                                 │
                │  create_ticket (ticket_manager_node)                 │
                │    │ cek duplikat → insert PostgreSQL (PENDING_REVIEW)│
                │    ▼                                                 │
                │  send_notification (notifier_node)                   │
                │    │ format → Telegram pelapor + (opsional) CSIRT   │
                │    ▼                                                 │
                │  END                                                 │
                └──────────────────────────────────────────────────────┘
                                │
                                ▼ IncidentState final
                    Format response → kirim ke pelapor

```

---

## 5. app/main.py & app/config.py & app/constants.py

### `app/main.py`

Entry point FastAPI. Fungsi-fungsi:

| Fungsi/Komponen | Detail |
|----------------|--------|
| `lifespan(app)` | Async context manager startup/shutdown. Memanggil `configure_logging()` saat startup. |
| `health()` | `GET /health` → `{"status": "ok", "service": "helpdesk-api"}` — liveness probe Kubernetes. |
| Router include | `app.include_router(api_router)` untuk `/api/v1/*` dan `register_web(app)` untuk web UI. |

Konfigurasi FastAPI: `title="Helpdesk Keamanan Siber Pusdatin"`, `version="0.1.0"`.

---

### `app/config.py`

Satu-satunya pembaca `.env`. Pola Pydantic Settings.

**Class `Settings(BaseSettings)`:**

| Atribut | Tipe | Default | Fungsi |
|---------|------|---------|--------|
| `openai_api_key` | `str \| None` | None | Kunci API OpenAI (prod) |
| `github_token` | `str \| None` | None | Token GitHub Models (dev) |
| `openai_base_url` | `str \| None` | None | Override URL API (GitHub Models endpoint) |
| `openai_model` | `str` | `"gpt-4o"` | Model LLM yang dipakai |
| `embedding_model` | `str` | `"text-embedding-3-small"` | Model embedding |
| `database_url` | `str` | — | PostgreSQL connection string |
| `redis_url` | `str` | — | Redis connection string |
| `qdrant_url` | `str` | — | Qdrant vector DB URL |
| `qdrant_api_key` | `str \| None` | None | Qdrant API key (cloud) |
| `telegram_bot_token` | `str` | — | Token bot Telegram |
| `csirt_chat_id` | `str \| None` | None | Chat ID grup CSIRT Telegram |
| `log_level` | `str` | `"INFO"` | Level logging |

**Method `_require_api_key()`:** Validator yang memastikan salah satu dari `openai_api_key` atau `github_token` tersedia — fail-fast di startup.

**Fungsi `get_settings() -> Settings`:** Singleton `@lru_cache` — satu instance di-share seluruh aplikasi.

---

### `app/constants.py`

Single source of truth untuk semua string/enum yang dipakai lebih dari satu modul:

| Konstanta | Isi | Dipakai di |
|-----------|-----|-----------|
| Status tiket | `PENDING_REVIEW`, `IN_PROGRESS`, `RESOLVED`, `CLOSED` | repository, templates, dashboard |
| Severity | `KRITIS`, `TINGGI`, `SEDANG`, `RENDAH`, `INFORMASIONAL` | identifier, ticket_manager, templates |
| `STATUS_BADGE` | `dict[str, tuple[css_class, label]]` | Web UI badge rendering |
| `SEVERITY_BADGE` | `dict[str, str]` | CSS class per severity |
| `SEVERITY_COLOR` | `dict[str, str]` | Hex color untuk inline style HTML |
| `STATUS_LABEL_TELEGRAM` | `dict[str, str]` | Emoji label untuk Telegram |

---

## 6. app/agents/ — Multi-Agent LangGraph

### `app/agents/state.py` — IncidentState

`TypedDict` sebagai media komunikasi tunggal antar semua agen. Dibagi 6 blok logis:

| Blok | Field | Siapa yang menulis |
|------|-------|-------------------|
| **Input** | `raw_input`, `sanitized_input`, `reporter_id`, `reporter_name`, `reporter_contact`, `timestamp_received`, `session_id` | orchestrator (initialize), guardrails (sanitized) |
| **Orchestrator** | `intent`, `requires_clarification`, `clarification_message` | orchestrator_node |
| **Identifier** | `incident_type`, `severity`, `confidence_score`, `classification_reasoning` | identifier_node |
| **RAG/Mitigation** | `retrieved_chunks`, `mitigation_recommendation`, `citations`, `rag_confidence` | mitigation_node |
| **Ticket** | `ticket_id`, `ticket_status`, `escalation_level` | ticket_manager_node |
| **Notifier/Meta** | `notification_sent`, `notification_recipients`, `notification_timestamp`, `processing_errors`, `agent_trace` | notifier_node + semua node (errors/trace) |

**Prinsip:** Tidak ada node yang berkomunikasi langsung dengan node lain. Semua lewat state ini.

---

### `app/agents/graph.py` — Perakitan Graf

File ini adalah "sutradara" — merakit semua agen menjadi satu pipeline berurutan dengan conditional routing.

**Helper internal:**

| Fungsi | Signature | Detail |
|--------|-----------|--------|
| `_trace(state, agent, status, **extra)` | → `IncidentState` | Append entry ke `agent_trace` dengan timestamp ISO |
| `_error(state, msg)` | → `IncidentState` | Append ke `processing_errors`, tidak raise |

**Node factories** (setiap factory mengembalikan fungsi async yang bisa di-add ke graf):

| Factory | Node yang dibuat | Logika |
|---------|-----------------|--------|
| `guardrails_node(state)` | Node langsung (bukan factory) | Panggil `run_input_guardrails()` → jika blocked, set `requires_clarification=True` + `guardrail_blocked=True` |
| `make_orchestrator_node(orchestrator)` | `classify_intent` | Panggil `orchestrator.classify_intent(sanitized_input)` → tulis intent ke state |
| `make_identifier_node(identifier)` | `identify_incident` | Panggil `identifier.classify(sanitized_input)` → tulis incident_type, severity, confidence |
| `make_mitigation_node(mitigation_advisor)` | `generate_mitigation` | Panggil `mitigation_advisor.generate_mitigation(...)` → tulis recommendation + citations |
| `make_ticket_node(ticket_manager)` | `create_ticket` | Panggil `ticket_manager.create_ticket(state)` → tulis ticket_id |
| `make_notifier_node(notifier)` | `send_notification` | Panggil `notifier.send_notifications(state)` → tulis notification_sent |
| `make_validate_output_node()` | `validate_output` | Cek PII di recommendation via `OutputValidator`, replace jika ada |

**Routing:**

| Fungsi | Logika |
|--------|--------|
| `route_by_intent(state) -> str` | Jika `requires_clarification=True` → `"needs_clarification"`, jika `intent == "report_incident"` → `"report_incident"`, jika `intent == "query_status"` → `"query_status"`, else → `"general_help"` |

**Graf utama (`build_helpdesk_graph(...)`):**

```

START → guardrails → (blocked?) → END
                   → classify_intent → (route_by_intent)
                                    → identify_incident → generate_mitigation
                                                        → validate_output
                                                        → create_ticket
                                                        → send_notification → END

```

Fungsi `run_pipeline(raw_input, reporter_*)` adalah **satu-satunya entry point publik** — dipanggil dari bot, API, web chat, test.

---

### `app/agents/orchestrator.py` — Klasifikasi Intent

**Class `OrchestratorAgent`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `llm_client: AsyncOpenAI`, `model: str = "gpt-4o"` | — | Simpan client + model |
| `_build_messages(sanitized_input)` | `str` | `list[dict]` | Format system prompt (dari `orchestrator.txt`) + user message |
| `classify_intent(sanitized_input)` | `str` | `dict` | Async LLM call dengan `response_format=JSON`. Retry sekali jika parse gagal. Fallback: `report_incident` confidence 0.0 |
| `initialize_state(raw_input, reporter_id, ...)` | berbagai str | `IncidentState` | Buat state baru dengan input fields terisi, semua field lain default kosong/None |

**Fungsi `_validate_intent(parsed)`:** Normalisasi intent ke salah satu 4 nilai valid, clamp confidence 0–1, pastikan konsistensi (jika `needs_clarification` tapi intent bukan `needs_clarification`, koreksi).

**4 Intent valid:**
- `report_incident` — lanjut pipeline penuh
- `query_status` — hanya lookup tiket
- `general_help` — dijawab langsung
- `needs_clarification` — minta informasi tambahan ke pelapor

---

### `app/agents/identifier.py` — Klasifikasi Insiden

**Class `IncidentIdentifierAgent`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `llm_client`, `model` | — | Simpan client + model |
| `_build_messages(sanitized_input)` | `str` | `list[dict]` | Format prompt dari `identifier.txt` |
| `classify(sanitized_input)` | `str` | `dict` | Async LLM call `max_tokens=300`. Retry sekali. Fallback: type="Lainnya", severity="Sedang", confidence=0.0 |

**Fungsi `_validate_and_normalize(parsed)`:** Validasi incident_type (whitelist 8 nilai + "Lainnya"), severity (whitelist 5 nilai), clamp confidence 0–1, set `requires_review=True` jika confidence < 0.5.

**8 Jenis insiden valid:** Phishing, Malware, Ransomware, Web Defacement, DDoS, Akses Tidak Sah, Kebocoran Data, Lainnya.

**5 Severity valid:** Kritis, Tinggi, Sedang, Rendah, Informasional.

---

### `app/agents/mitigation.py` — Agentic RAG (Jantung Skripsi)

**Konstanta kritis:**

| Konstanta | Nilai | Makna |
|-----------|-------|-------|
| `RETRIEVAL_SCORE_THRESHOLD` | `0.22` | Batas minimum skor chunk dianggap relevan (diturunkan dari 0.3 agar recall lebih tinggi) |
| `MAX_ITERATIONS` | `3` | Maksimum iterasi RAG sebelum berhenti |
| `TOP_K_RETRIEVAL` | `30` | Jumlah chunk diambil per iterasi (dinaikkan dari 20) |
| `TOP_K_RERANK` | `5` | Jumlah chunk setelah reranking |

**Fungsi-fungsi internal:**

| Fungsi | Signature | Detail |
|--------|-----------|--------|
| `_assemble_context(chunks)` | `list[dict] → str` | Format chunk menjadi blok bernomor untuk LLM prompt: `[Sumber N]\n{content}` |
| `_check_adequacy(chunks)` | `list[dict] → bool` | True jika ada chunk dengan `final_score >= RETRIEVAL_SCORE_THRESHOLD` |
| `_expand_query(query, incident_type, iteration)` | `str, str, int → str` | Buat query lebih spesifik dengan prefix keyword incident_type + kata "teknis" |
| `_merge_results(results1, results2)` | `list, list → list` | Deduplikasi chunk berdasarkan `id`, gabungkan dari dua iterasi |
| `_validate_citations(steps, chunks)` | `list, list → list` | Filter: hanya pertahankan step yang sumber-nya ada di chunk. Mengecek 6 field metadata: `source`, `section`, `doc_title`, `section_header`, `source_framework`, `external_id` (sebelumnya hanya `source` dan `section`). Referensi numerik `[N]` dan keyword standar (nist, mitre, bssn, dll.) juga diterima. |
| `_build_citations(steps)` | `list → list` | Ekstrak `{source, step}` dari validated steps |
| `_compute_rag_confidence(chunks)` | `list → float` | Rata-rata `final_score` top chunks; 0.0 jika kosong |

**Class `MitigationAdvisorAgent`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `llm_client`, `retriever`, `reranker_fn=None`, `model` | — | Simpan dependency |
| `_build_messages(context, incident_type, severity, sanitized_input)` | berbagai str | `list[dict]` | Format prompt dari `mitigation.txt` dengan injeksi context chunk |
| `generate_mitigation(sanitized_input, incident_type, severity)` | 3 str | `dict` | **Inti agentic RAG** — lihat loop di bawah |

**Agentic RAG Loop dalam `generate_mitigation()`:**

```python
query = f"{incident_type}: {sanitized_input}"
all_chunks = []

for i in range(MAX_ITERATIONS):
    chunks = retriever.retrieve(query, incident_type, TOP_K_RETRIEVAL)
    chunks = reranker_fn(query, chunks, TOP_K_RERANK, incident_type)
    all_chunks = _merge_results(all_chunks, chunks)

    if _check_adequacy(chunks):
        break  # konteks cukup, hentikan iterasi

    query = _expand_query(query, incident_type, i + 1)

if not all_chunks:
    return fallback_response  # RAG gagal total

context = _assemble_context(all_chunks[:TOP_K_RERANK])
recommendation = await llm.generate(messages + context, max_tokens=800)
parsed = parse_llm_json(recommendation)

validated_steps = _validate_citations(parsed["mitigation_steps"], all_chunks)
citations = _build_citations(validated_steps)
confidence = _compute_rag_confidence(all_chunks)

return {
    "mitigation_recommendation": parsed["general_guidance"],
    "mitigation_steps": validated_steps,
    "citations": citations,
    "retrieved_chunks": all_chunks,
    "rag_confidence": confidence,
}

```

**Fallback:** Jika RAG gagal atau LLM error → kembalikan rekomendasi generik beserta `rag_confidence=0.0`.

---

### `app/agents/ticket_manager.py` — Pembuatan Tiket

**Konstanta:**
- `REQUIRED_FIELDS = ["raw_input", "sanitized_input", "reporter_id", "incident_type", "severity"]`
- `ESCALATION_MAP`: `{"Kritis": "Segera", "Tinggi": "Mendesak", "Sedang": "Normal", "Rendah": "Rendah", "Informasional": "Informasi"}`

**Class `TicketManagerAgent`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `ticket_repository: TicketRepository` | — | Inject repository |
| `create_ticket(incident_state: dict)` | state dict | `dict` | Lihat alur di bawah |

**Alur `create_ticket()`:**
1. Validasi field wajib → return `{"error": "missing fields"}` jika ada yang kosong.
2. Map severity → escalation_level via `ESCALATION_MAP`.
3. Cek duplikat: `repository.check_duplicate(reporter_id, description, hours=24)` → jika ada, kembalikan tiket lama dengan `is_duplicate=True`.
4. Build `ticket_data` dict dari state.
5. `repository.create_ticket(ticket_data)` → simpan ke PostgreSQL.
6. Return `{ticket_id, ticket_status, escalation_level, is_duplicate}`.

**Error handling:** Selalu return dict, tidak pernah raise — pipeline harus resilient.

---

### `app/agents/notifier.py` — Notifikasi Dual-Channel

**Konstanta:**

| Konstanta | Nilai | Makna |
|-----------|-------|-------|
| `HIGH_PRIORITY_SEVERITIES` | `{"Kritis", "Tinggi"}` | Severity yang dikirim juga ke manager |
| `_CSIRT_CHAT_ID_ENV` | `"CSIRT_CHAT_ID"` | Nama environment variable Chat ID CSIRT |

**Fungsi `_get_csirt_recipients(severity) -> list[str]`:** Ambil `CSIRT_CHAT_ID` via `os.getenv(_CSIRT_CHAT_ID_ENV, "")` — jika env var tidak diset, list penerima kosong (tidak kirim Telegram). Untuk severity tinggi, tambah `CSIRT_MANAGER_CHAT_ID`.

**Class `NotifierAgent`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `telegram_client=None` | — | None = mode log-only (dev/test) |
| `_format_csirt_notification(state)` | dict | str | Gunakan `format_csirt_alert()` dari templates |
| `_format_reporter_confirmation(state)` | dict | str | Gunakan `format_reporter_confirmation()` dari templates |
| `send_notifications(incident_state)` | dict | dict | Lihat alur di bawah |

**Alur `send_notifications()`:**
1. Format kedua pesan (CSIRT + pelapor).
2. Dapatkan daftar penerima berdasarkan severity.
3. Jika `telegram_client is None` → hanya log (dev mode).
4. Jika ada client → kirim via Telegram.
5. Kegagalan pengiriman **tidak fail pipeline** — hanya log warning.
6. Return `{notification_sent: bool, notification_recipients: list, notification_timestamp: str}`.

---

## 7. app/rag/ — Retrieval-Augmented Generation

### `app/rag/ingestion.py` — Loader Dokumen

Mendukung dua format: **PDF** (NIST SP 800-61) dan **STIX JSON** (MITRE ATT&CK).

**Fungsi PDF:**

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `load_metadata(metadata_path)` | `Path` | `dict` | Load JSON metadata (doc_id, doc_title, source_framework, incident_types, version) |
| `ingest_document(pdf_path, metadata)` | `Path, dict` | `list[Document]` | PyPDFLoader → 1 Document per halaman → enrich metadata |
| `ingest_directory(docs_dir, metadata_dir)` | `Path, Path` | `list[Document]` | Batch ingest semua PDF yang ada metadata-nya |

**Mapping taktik MITRE → incident_type** (`_TACTIC_TO_INCIDENT_TYPES`):

```python
{
    "initial-access":     ["phishing", "akses_tidak_sah"],
    "execution":          ["malware", "ransomware"],
    "persistence":        ["malware", "akses_tidak_sah"],
    "defense-evasion":    ["malware"],
    "collection":         ["kebocoran_data"],
    "exfiltration":       ["kebocoran_data"],
    "impact":             ["ransomware", "ddos", "web_defacement"],
    # dst.
}

```

**Fungsi STIX (MITRE ATT&CK):**

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `_parse_mitigations(bundle_objects, objects_by_id, coa_to_techniques, doc_id)` | — | `list[Document]` | Ekstrak `course-of-action` M1xxx. Linkage ke teknik yang dimitigasi (max 20). Tag incident_types via taktik. |
| `_parse_techniques(bundle_objects, doc_id)` | — | `list[Document]` | Ekstrak `attack-pattern` non-subtechnique. Include deskripsi max 1200 karakter + taktik. |
| `ingest_attack_stix(stix_path, doc_id="mitre-attack-enterprise")` | `Path, str` | `list[Document]` | Entry point utama. Build index object by ID + relationship map `coa_to_techniques`. Return mitigations + techniques. |

---

### `app/rag/chunker.py` — Pemecahan Chunk

**Konstanta:** `CHUNK_SIZE = 800`, `CHUNK_OVERLAP = 100`, `SEPARATORS = ["\n\n", "\n", ". ", " "]`

**Alasan 800/100:** Cukup besar untuk koherensi paragraf, cukup kecil untuk presisi retrieval.

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `_detect_section_header(text)` | `str` | `str` | Regex ekstrak header section dari teks chunk |
| `chunk_documents(documents)` | `list[Document]` | `list[Document]` | `RecursiveCharacterTextSplitter` → preservasi section header di metadata → tambah `chunk_index` sekuensial |

---

### `app/rag/embedder.py` — Embedding + Upload Qdrant

**Konstanta:**

| Konstanta | Nilai | Makna |
|-----------|-------|-------|
| `COLLECTION_NAME` | `"cybersecurity_knowledge"` | Nama collection di Qdrant |
| `VECTOR_SIZE` | `1536` | Dimensi vektor text-embedding-3-small |
| `BATCH_SIZE` | `100` | Ukuran batch saat upload ke Qdrant |

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `get_embedder(api_key, model)` | `str, str` | `OpenAIEmbeddings` | Factory dengan dukungan GitHub Models via `openai_api_base` |
| `embed_chunks(chunks, embedder)` | `list, embedder` | `list[list[float]]` | Embed dalam batch `BATCH_SIZE`, log progress |
| `ensure_collection(client)` | `QdrantClient` | — | Buat collection dengan cosine distance + text index jika belum ada |
| `_build_payload(chunk)` | `Document` | `dict` | Ekstrak metadata untuk Qdrant payload |
| `upload_chunks(client, chunks, vectors)` | — | `int` | Buat `PointStruct` dengan UUID → upsert ke Qdrant → return jumlah chunk |

---

### `app/rag/retriever.py` — HybridRetriever

**Konstanta:** `RRF_K = 60` (nilai standar literatur IR)

**Fungsi internal:**

| Fungsi | Signature | Detail |
|--------|-----------|--------|
| `_rrf_score(rank, k)` | `int, int → float` | Formula: `1 / (k + rank + 1)` |
| `_reciprocal_rank_fusion(semantic_hits, keyword_hits)` | `list, list → list` | Merge dua ranked list via RRF score, deduplikasi by point ID, sort descending |
| `_build_incident_filter(incident_type)` | `str → Filter \| None` | Qdrant filter: `incident_types` array mengandung `incident_type` |

**Class `HybridRetriever`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `qdrant_client`, `embedder` | — | Inject dependency |
| `retrieve(query, incident_type=None, top_k=20)` | `str, str, int` | `list[dict]` | **Inti retrieval**: semantic search + keyword search + RRF merge → return list dengan keys: `id, content, metadata, score, rrf_score` |
| `_keyword_search(query, metadata_filter, limit)` | `str, Filter, int` | `list[dict]` | Qdrant scroll API dengan full-text filter pada field `page_content` |

**Alur `retrieve()`:**
1. Embed query → semantic search Qdrant (cosine similarity).
   - **Compatibility shim:** jika `client` memiliki method `search` (untuk backward compatibility dengan test mock), gunakan itu; jika tidak ada, gunakan `client.query_points()`. Ini memastikan unit test yang mem-patch `client.search` tetap berfungsi.
   - `score` diakses via `getattr(hit, "score", 0.0)` agar robust terhadap objek yang tidak selalu memiliki atribut `score`.
2. Full-text search Qdrant (keyword via scroll API).
3. RRF merge kedua hasil.
4. Return top-K.

---

### `app/rag/reranker.py` — Custom Reranker

**Konstanta:**

| Konstanta | Nilai | Makna |
|-----------|-------|-------|
| `_COSINE_WEIGHT` | `0.7` | Bobot skor cosine similarity dari Qdrant |
| `_RRF_WEIGHT` | `0.3` | Bobot skor RRF |
| `_RRF_NORMALIZE` | `0.05` | Normalisasi skala RRF |
| `INCIDENT_TYPE_BOOST` | `0.10` | Bonus jika metadata chunk mengandung incident_type yang sama |
| `MIN_SCORE_THRESHOLD` | `0.0` | Ambang batas minimum skor akhir |

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `_compute_final_score(chunk, incident_type)` | `dict, str` | `float` | `0.7×cosine + 0.3×norm_rrf + (0.10 jika incident_type match)`, cap 1.0 |
| `rerank(query, chunks, top_k=5, incident_type=None)` | — | `list[dict]` | Score semua chunk → filter by threshold → sort descending → return top_k dengan `final_score` field |

**Alasan tidak pakai cross-encoder:** Menghindari dependency berat (Hugging Face BERT model) yang tidak cocok untuk prototipe ringan.

---

## 8. app/security/ — Guardrails Berlapis

### `app/security/guardrails.py` — Orchestrator Keamanan

**Class `GuardrailsResult` (dataclass/slots):**
- `sanitized_input: str`
- `pii_mapping: dict` — mapping placeholder → nilai asli
- `blocked: bool`
- `block_reason: str`

**Fungsi utama `run_input_guardrails(raw_input) -> GuardrailsResult`:**

```python
cleaned = sanitizer.sanitize(raw_input)         # 1. strip HTML + kontrol
result = injection_detector.detect(cleaned)      # 2. cek injection
if result["is_injection"]:
    return GuardrailsResult(blocked=True, reason="prompt_injection")
redacted, mapping = pii_redactor.redact(cleaned) # 3. redact PII
return GuardrailsResult(sanitized_input=redacted, pii_mapping=mapping)

```

**Fail-closed:** Exception apapun → `blocked=True`, pipeline berhenti.

---

### `app/security/sanitizer.py` — Pembersih Input

**Class `InputSanitizer`:**

| Method | Detail |
|--------|--------|
| `sanitize(raw_input: str) → str` | 1) Unicode NFC normalization; 2) Strip HTML/XML; 3) Buang kontrol char (kecuali `\n`, `\t`); 4) Collapse multiple whitespace; 5) Truncate ke `MAX_LENGTH=2000`; 6) Strip leading/trailing |

---

### `app/security/prompt_injection.py` — Deteksi Injection

**Pattern categories yang dideteksi:**
- Override: "ignore previous", "disregard all", "forget previous"
- Persona switch: "you are now", "act as", "pretend to be", "roleplay as"
- Leak: "reveal your instructions", "what are your instructions"
- Encoding: `\x`, `\u`, `&#x;` (obfuscation karakter)
- Jailbreak keywords umum

**Class `PromptInjectionDetector`:**

| Method | Return | Detail |
|--------|--------|--------|
| `detect(text) → dict` | `{is_injection, confidence, matched_pattern}` | Layer 1: regex (confidence 0.95). Layer 2: base64 heuristic (confidence 0.80) |

**Fungsi `_check_base64(text) -> bool`:** Cari string panjang cocok pola base64 (≥40 char alphanumeric+pad), decode, cek apakah mengandung kata berbahaya.

---

### `app/security/pii_redactor.py` — Redaksi PII

**4 Regex pattern:**

| Pattern | Regex | Placeholder |
|---------|-------|-------------|
| IPv4 | `\b\d{1,3}(\.\d{1,3}){3}\b` | `[REDACTED_IP]` |
| Email | RFC-ish | `[REDACTED_EMAIL]` |
| NIK | `\b\d{16}\b` | `[REDACTED_NIK]` |
| Telepon Indonesia | `(\+62|62|0)8\d{8,12}` | `[REDACTED_PHONE]` |

**Class `PIIRedactor`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `redact(text)` | `str` | `tuple[str, dict]` | Proses berurutan: IP → Email → NIK → Phone. Deduplikasi: nilai PII sama → placeholder sama. Return (teks_redacted, mapping) |
| `restore(redacted_text, mapping)` | `str, dict` | `str` | Substitusi balik placeholder → nilai asli (untuk penyimpanan internal) |

**Mengapa urutan IP→Email→NIK→Phone?** Untuk menghindari overlap regex — IP diproses lebih dulu sebelum angka dalam email/NIK bisa salah match.

---

### `app/security/validator.py` — Validasi Output LLM

**Class `OutputValidator`:**

| Method | Return | Detail |
|--------|--------|--------|
| `validate(output, retrieved_chunks) → dict` | `{is_valid, issues, cleaned_output}` | 1) Cek PII leakage; 2) Cek output kosong; 3) Cek meaningful content (minimal 1 keyword aksi ATAU referensi sumber terpercaya) |

**`ALLOWED_ACTION_KEYWORDS`:** "ganti kata sandi", "scan antivirus", "isolasi", "laporkan ke", "backup", "update sistem", dll.

**Sumber terpercaya yang diakui:** nist, mitre, bssn, iso 27, att&ck, csirt.

---

## 9. app/database/ — Persistence Layer

### `app/database/models.py` — SQLAlchemy ORM

**Class `IncidentTicket`** (tabel: `incident_tickets`):

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| `ticket_id` | `String(20)` PK | Format: `TICKET-YYYY-NNNN` |
| `reporter_id`, `reporter_name`, `reporter_contact`, `reporter_department` | `String` | Identitas pelapor |
| `incident_type`, `severity`, `confidence_score`, `classification_reasoning` | — | Output identifier |
| `description_raw`, `description_sanitized` | `Text` | Raw + setelah guardrails |
| `evidence_files`, `evidence_urls` | `JSONB` | Attachment metadata |
| `mitigation_recommendation` | `Text` | Output RAG |
| `citations` | `JSONB` | Daftar sumber kutipan |
| `rag_confidence` | `Float` | Skor kepercayaan RAG |
| `status` | `String` | Default: `PENDING_REVIEW` |
| `escalation_level`, `assigned_to` | `String` | Untuk admin |
| `created_at`, `updated_at`, `reviewed_at`, `resolved_at`, `closed_at` | `DateTime` | Audit timeline |
| `agent_trace` | `JSONB` | Log eksekusi tiap node |
| `is_duplicate`, `parent_ticket_id` | — | Deteksi duplikat |

**Class `AuditLog`** (tabel: `audit_logs`):
- `log_id` (BIGINT PK auto-increment), `timestamp`, `event_type`, `session_id`, `user_id`, `agent_name`
- `action`, `input_summary`, `output_summary`, `guardrail_result`, `error_message`
- `token_count`, `latency_ms`, `llm_model`, `metadata` (JSONB)

**Class `Admin`** (tabel: `admins`):
- `id` PK, `username` (unique, indexed), `email` (unique)
- `full_name`, `password_hash` (bcrypt), `is_active` (default True)
- `created_at`, `last_login_at`

**Class `TicketAttachment`** (tabel: `ticket_attachments`):
- `ticket_id` (FK), `original_filename`, `stored_path`, `mime_type`, `size_bytes`
- `uploaded_by`, `uploaded_at`

---

### `app/database/repository.py` — Data Access Layer

**Fungsi standalone:**
- `generate_ticket_id(db) -> str`: Query max ticket_id tahun ini → increment → format `TICKET-{year}-{seq:04d}`.

**Class `TicketRepository`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `db: Session` | — | Inject SQLAlchemy session |
| `create_ticket(ticket_data: dict)` | dict | `IncidentTicket` | Auto-generate ticket_id jika kosong. `session.add()` + `commit()` + `refresh()`. |
| `get_ticket_by_id(ticket_id)` | str | `Optional[IncidentTicket]` | Query by PK |
| `get_tickets_by_reporter(reporter_id)` | str | `list[IncidentTicket]` | Filter + order `created_at DESC` |
| `update_ticket_status(ticket_id, status)` | str, str | `Optional[IncidentTicket]` | Update field status saja |
| `update_ticket(ticket_id, updates: dict)` | str, dict | `Optional[IncidentTicket]` | Whitelist field: status, assigned_to, modified_by, escalation_level. Auto-set `reviewed_at`/`resolved_at`/`closed_at` berdasarkan transisi status. |
| `get_all_tickets(limit=200)` | int | `list[IncidentTicket]` | Untuk dashboard admin |
| `get_stats()` | — | `dict` | Agregasi: total + by_status + by_severity + by_type |
| `check_duplicate(reporter_id, description, hours=24)` | str, str, int | `Optional[IncidentTicket]` | Cari tiket dari reporter_id yang sama dengan deskripsi identik dalam N jam terakhir |

**Class `AuditRepository`:**

| Method | Return | Detail |
|--------|--------|--------|
| `log_event(event_data: dict)` | `AuditLog` | Insert audit entry |
| `get_events_by_session(session_id)` | `list[AuditLog]` | Query by session ordered by timestamp |

---

### `app/database/connection.py` — Session Factory

| Fungsi | Return | Detail |
|--------|--------|--------|
| `_get_engine()` | `Engine` | Cached `@lru_cache`. `create_engine(DATABASE_URL)` |
| `_get_session_factory()` | `sessionmaker` | Cached. Bind ke engine. |
| `get_db()` | `Generator[Session]` | FastAPI dependency. Yield session, `finally: session.close()`. |

---

## 10. app/api/ — REST API

### `app/api/schemas.py` — Pydantic Models

| Schema | Arah | Field kunci |
|--------|------|------------|
| `ReportRequest` | Request | `raw_input` (1-2000 char), `reporter_id` (1-50 char), `reporter_name`, `reporter_contact`, `session_id` (optional) |
| `CitationOut` | Response | `source`, `section`, `content_preview` |
| `ReportResponse` | Response | `ticket_id`, `ticket_status`, `intent`, `incident_type`, `severity`, `confidence_score`, `escalation_level`, `mitigation_recommendation`, `citations`, `rag_confidence`, `requires_clarification`, `clarification_message`, `notification_sent`, `processing_errors` |
| `TicketOut` | Response | `ticket_id`, `reporter_id`, `reporter_name`, `incident_type`, `severity`, `confidence_score`, `status`, `escalation_level`, `description_sanitized`, `mitigation_recommendation`, `created_at`, `is_duplicate` |
| `TicketUpdateRequest` | Request | `status`, `assigned_to`, `escalation_level` (semua optional), `notify_reporter` (default True) |
| `StatsResponse` | Response | `total`, `by_status`, `by_severity`, `by_type` |
| `HealthResponse` | Response | `status`, `service`, `pipeline_ready` |

---

### `app/api/routes.py` — Route Handlers

| Endpoint | Method | Auth | Fungsi | Detail |
|----------|--------|------|--------|--------|
| `/api/v1/health` | GET | None | Health check | Return `pipeline_ready` status |
| `/api/v1/report` | POST | None | Submit laporan | `initialize_state → graph.ainvoke → format ReportResponse`. Exceptions → HTTP 500 + trace_id. |
| `/api/v1/tickets/stats` | GET | None | Statistik dashboard | `repository.get_stats()` |
| `/api/v1/tickets/{ticket_id}` | GET | None | Detail tiket | 404 jika tidak ditemukan |
| `/api/v1/tickets/{ticket_id}` | PATCH | None | Update tiket | `repository.update_ticket()`. Jika `notify_reporter=true` → `_notify_reporter_status()` via Telegram. |
| `/api/v1/tickets` | GET | None | Daftar tiket | `?reporter_id=X` filter, limit 100 |

---

### `app/api/dependencies.py` — Dependency Injection

| Fungsi | Return | Detail |
|--------|--------|--------|
| `_build_pipeline()` | singleton dict | Buat semua agent (orchestrator, identifier, mitigation_advisor, notifier). LLM client + embedder + retriever dibuat sekali saat startup. |
| `get_db()` | `Generator[Session]` | Wrapper `get_db()` dari connection.py |
| `get_orchestrator()` | `OrchestratorAgent` | Dari singleton pipeline |
| `get_helpdesk_graph(db)` | compiled graph | `build_helpdesk_graph(...)` dengan `ticket_manager` yang inject `TicketRepository(db)` baru per request |

---

## 11. app/telegram/ — Bot Interface

### `app/telegram/bot.py` — PTB Handlers

**Konstanta:**

| Konstanta | Nilai | Makna |
|-----------|-------|-------|
| `WAITING_REPORT` | `0` | State ConversationHandler saat menunggu laporan |
| `_ADMIN_CHAT_ID_ENV` | `"CSIRT_CHAT_ID"` | Nama env var Chat ID admin/CSIRT |
| `_ADMIN_CHAT_ID_FALLBACK` | `"-1003971618295"` | Fallback production (tidak dipakai di test) |

**Fungsi `_get_admin_chat_id() -> str | None`** (sebelumnya `_get_csirt_chat_id()`): Return nilai `CSIRT_CHAT_ID` dari env var, atau `None` jika tidak di-set. Berbeda dengan notifier — **tidak menggunakan fallback** agar test isolation terjaga (test bisa assert "tidak ada chat id" dengan tidak men-set env var).

**Handler functions:**

| Fungsi | Trigger | Detail |
|--------|---------|--------|
| `start_handler(update, context)` | `/start` | Kirim pesan selamat datang + daftar perintah |
| `help_handler(update, context)` | `/help` | Kirim panduan penggunaan |
| `report_start_handler(update, context) → int` | `/report` | Kirim prompt "ketik deskripsi insiden", return `WAITING_REPORT` state |
| `report_receive_handler(update, context) → int` | Teks bebas saat `WAITING_REPORT` | Ambil graph+orchestrator dari `bot_data`, tampilkan "sedang diproses...", `ainvoke(state)`, kirim hasil via `_send_result()`, hapus pesan sementara. Tangani exception secara graceful. |
| `_send_result(update, context, result)` | dipanggil oleh receive_handler | Jika `requires_clarification`: kirim pesan klarifikasi saja. Jika `ticket_id`: kirim konfirmasi pelapor + (jika CSIRT_CHAT_ID ada) alert CSIRT. |
| `cancel_handler(update, context) → int` | `/cancel` | Batalkan flow /report, return `ConversationHandler.END` |
| `status_handler(update, context)` | `/status <ticket_id>` | Query `repository.get_ticket_by_id()`, format status, kirim ke pelapor |
| `unknown_handler(update, context)` | Pesan tidak dikenal | Arahkan ke /report atau /help |

**Fungsi `build_bot_application(token, helpdesk_graph, orchestrator, ticket_repository)`:**
- Simpan dependency ke `app.bot_data`.
- Daftarkan `ConversationHandler` untuk `/report` dengan state `WAITING_REPORT`.
- Daftarkan handlers: `/start`, `/help`, `/status`, `/cancel`.
- Daftarkan `MessageHandler` unknown.
- Return PTB `Application` siap dijalankan.

---

### `app/telegram/templates.py` — Format Pesan

**Konstanta:**

| Konstanta | Isi | Dipakai di |
|-----------|-----|-----------|
| `SEVERITY_EMOJI` | `{"Kritis": "🔴", "Tinggi": "🟠", "Sedang": "🟡", "Rendah": "🟢", "Informasional": "⚪"}` | Kedua format fungsi |
| `_STATUS_INFO` | `dict[status → (emoji, label, detail_message)]` | `format_status_update()` |

**Fungsi format:**

| Fungsi | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `format_csirt_alert(ticket_id, incident_type, severity, reporter_name, timestamp, description_short, mitigation_short)` | 7 str | str | Truncate description/mitigation ke 300 char, inject severity emoji, gunakan `CSIRT_ALERT_TEMPLATE` |
| `format_reporter_confirmation(ticket_id, incident_type, severity, confidence, mitigation_steps)` | 5 param | str | Konversi confidence ke %, truncate mitigation ke 2000 char, gunakan `REPORTER_CONFIRMATION_TEMPLATE` |
| `format_status_update(ticket_id, new_status, updated_at)` | 3 str | str | Lookup status info, gunakan `STATUS_UPDATE_TEMPLATE` |

---

## 12. app/web/ — Web Interface (HTMX)

### `app/web/app.py` — Registrasi Web

**Fungsi `register_web(app: FastAPI)`:**
1. Add middleware: `SecurityHeadersMiddleware → CSRFMiddleware → SessionMiddleware`.
2. Set rate limiter via `slowapi`.
3. Daftarkan exception handlers untuk `_RedirectException` dan `_ReporterNotFound`.
4. Mount static files di `/static`.
5. Include semua router: landing, admin_auth, admin_inbox, admin_actions, admin_rag, admin_report, pelapor.

---

### `app/web/config.py` — WebConfig

**Class `WebConfig(BaseSettings)`:**

| Atribut | Default | Fungsi |
|---------|---------|--------|
| `session_secret` | — | Secret untuk SessionMiddleware |
| `csrf_secret` | — | Secret untuk CSRF token |
| `session_max_age` | `28800` (8 jam) | Durasi session cookie |
| `cookie_secure` | `False` | True di production (HTTPS) |
| `upload_dir` | `"./web_uploads"` | Direktori simpan file upload |
| `upload_max_bytes` | `10485760` (10 MB) | Batas ukuran file upload |
| `login_rate_limit` | `"5/minute"` | Rate limit login admin |
| `login_lockout_threshold` | `5` | Gagal login → lockout |
| `lockout_window` | `900` (15 menit) | Durasi lockout di Redis |
| `csrf_strict` | `True` | Mode strict CSRF |

---

### `app/web/constants.py`

| Konstanta | Nilai |
|-----------|-------|
| `AuditEvents` | Class dengan string: `ADMIN_LOGIN`, `ADMIN_LOGIN_FAILED`, `ADMIN_LOGOUT`, `TICKET_STATUS_UPDATED`, `TICKET_ASSIGNED`, `TICKET_ESCALATED`, `TICKET_NOTIFY_SENT`, dll. |
| `TICKET_STATUSES` | `("PENDING_REVIEW", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED")` |
| `ESCALATION_LEVELS` | `("LOW", "MEDIUM", "HIGH", "CRITICAL")` |

---

### `app/web/dependencies.py` — Web DI

**Exception classes (dipakai untuk redirect):**
- `_RedirectException(location)` — exception handler → HTTP 303 redirect
- `_ReporterNotFound(location)` — redirect ke `/lapor` jika session pelapor tidak ada

**Fungsi:**

| Fungsi | Return | Detail |
|--------|--------|--------|
| `get_db_session()` | `Generator[Session]` | Wrapper untuk test override |
| `get_current_admin(request, db) → Admin` | `Admin` | Load `admin_id` dari session → query Admin → raise `_RedirectException` jika tidak ada/inactive |
| `get_csrf_token(request) → str` | str | Ekstrak dari session |
| `get_reporter_session(request) → dict` | dict | Cek `session_id` + `reporter_id` di session → raise `_ReporterNotFound` jika kosong. Return `{session_id, reporter_id, reporter_name, reporter_contact, reporter_unit}` |

---

### Middleware

#### `app/web/middleware/csrf.py` — CSRFMiddleware

**Class `CSRFMiddleware(BaseHTTPMiddleware)`:**
- **Safe methods** (GET, HEAD, OPTIONS): Selalu pastikan token tersedia di session — generate baru jika `SESSION_KEY` belum ada di session (`if SESSION_KEY not in session`). Ini memastikan token selalu ada setelah GET request pertama.
- **Unsafe methods** (POST/PUT/PATCH/DELETE): Verifikasi token dari header `X-CSRF-Token` atau form field `csrf_token`.
- **Exempt:** Semua path `/api/*` bypass CSRF.
- Return **HTTP 403** jika token invalid atau hilang.
- **Body buffering fix:** Saat membaca form field, middleware memanggil `await request.body()` terlebih dahulu untuk men-cache body di Starlette sebelum memanggil `request.form()`. Ini memastikan route handler tetap bisa membaca form data yang sama tanpa body habis dikonsumsi middleware.

#### `app/web/middleware/security_headers.py` — SecurityHeadersMiddleware

Set header keamanan pada setiap response:
- `X-Frame-Options: DENY` — cegah clickjacking
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` — restrictive, hanya izinkan `self` + inline untuk dev
- `Permissions-Policy` — disable geolocation, microphone, camera

#### `app/web/middleware/rate_limit.py`

Export `limiter = Limiter(key_func=get_remote_address)` untuk dipakai di routes dengan decorator `@limiter.limit("N/interval")`.

---

### Routes Web

| File | Endpoint utama | Auth | Detail |
|------|---------------|------|--------|
| `landing.py` | `GET /` | None | Render `landing.html` |
| `pelapor.py` | `GET /lapor` | None | Render form identitas |
| | `POST /lapor` | None | `identitas_submit()` — **async**, strip whitespace reporter_name/contact/unit sebelum validasi, simpan ke session, redirect ke `/lapor/chat` |
| | `GET /lapor/chat` | Reporter session | Chat interface |
| | `POST /lapor/chat/message` | Reporter session | Invoke pipeline via `ChatService`, return HTMX fragment (rate limit 20/min) |
| | `POST /lapor/chat/upload` | Reporter session | `UploadService.save_pending()` |
| | `POST /lapor/chat/reset` | Reporter session | `reset_session()` — bersihkan histori Redis dan session. **HTMX-aware:** jika header `HX-Request: true`, return `HTMLResponse` (200) dengan header `HX-Redirect: /lapor`; jika bukan HTMX, return `RedirectResponse` 303 ke `/lapor`. |
| `admin_auth.py` | `GET /admin/login` | None | Form login |
| | `POST /admin/login` | None | `AuthService.authenticate()`, set session (rate limit 5/min) |
| | `POST /admin/logout` | None | Clear session |
| `admin_inbox.py` | `GET /admin/inbox` | Admin | Daftar tiket dengan filter/pagination |
| | `GET /admin/inbox/table` | Admin | HTMX fragment tabel tiket |
| | `GET /admin/tiket/{id}` | Admin | Detail tiket |
| `admin_actions.py` | `PATCH /admin/tiket/{id}/status` | Admin | Update status tiket |
| | `PATCH /admin/tiket/{id}/assign` | Admin | Assign ke admin |
| | `POST /admin/tiket/{id}/eskalasi` | Admin | Naikkan escalation level |
| | `POST /admin/tiket/{id}/notif` | Admin | Kirim notifikasi ke pelapor |
| | `POST /admin/tiket/{id}/attachment` | Admin | Upload lampiran |
| `admin_rag.py` | `GET /admin/rag` | Admin | Halaman manajemen knowledge base |
| | `POST /admin/rag/ingest` | Admin | Ingest PDF/STIX baru ke Qdrant |
| `admin_report.py` | `GET /admin/report` | Admin | Halaman form laporan. Memiliki fallback: jika `csrf_token` belum ada di session (middleware belum set), generate via `secrets.token_urlsafe(32)` secara eksplisit. |
| | `POST /admin/report/generate` | Admin | Generate HTML report via `ReportService`, kirim sebagai `FileResponse` |

---

### Template Branding

Label organisasi di halaman-halaman pelapor dan admin telah diperbarui untuk bersifat lebih netral/generik:

| File Template | Perubahan |
|--------------|-----------|
| `app/web/templates/admin/login.html` | "Pusdatin CSIRT" → "Helpdesk" |
| `app/web/templates/pelapor/chat.html` | "Pusdatin CSIRT" → "Helpdesk", "Kementerian Pertanian RI" → "Tim Keamanan Siber" |
| `app/web/templates/pelapor/identitas.html` | Idem |
| `app/web/templates/pelapor/tiket_detail.html` | Idem |

---

### Services Web

#### `app/web/services/auth_service.py` — AuthService

**Dataclass `AuthResult`:** `success`, `admin_id`, `username`, `error` (string: `"invalid_credentials"` | `"account_disabled"` | `"locked"`)

**Class `AuthService`:**

| Method | Detail |
|--------|--------|
| `__init__(db, redis_client, lockout_threshold=5, lockout_window=900)` | Inject dependency |
| `authenticate(username, password, client_ip) → AuthResult` | 1) Cek Redis lockout counter; 2) Query Admin; 3) bcrypt.verify (timing-safe); 4) Cek is_active; 5) Clear lockout on success, increment on failure; 6) Update last_login_at |
| `_increment_failure(lockout_key)` | Increment counter Redis + set expire |

---

#### `app/web/services/chat_service.py` — ChatService

**Dataclass `ChatMessage`:** `role` ("user"|"assistant"), `content`, `ts` (ISO timestamp)

**Class `ChatService`:**

| Method | Parameter | Return | Detail |
|--------|-----------|--------|--------|
| `__init__` | `redis_client` | — | Inject Redis |
| `get_history(session_id)` | str | `list[dict]` | Ambil dari Redis key `f"web:chat:{session_id}"` |
| `_save_history(session_id, history)` | str, list | — | Simpan ke Redis TTL 24 jam |
| `clear_history(session_id)` | str | — | Delete key |
| `handle_message(session_id, reporter_id, reporter_name, reporter_contact, text, graph, orchestrator, db, timeout)` | — | dict | Gabungkan pesan kontekstual → initialize_state → `graph.ainvoke()` timeout 60s → format response untuk template HTMX |

**Multi-turn context:** Mengirim konteks percakapan kepada orchestrator:
- Jika bot sudah pernah minta klarifikasi (`clarification_rounds >= 1`): kirim max 8 pesan terakhir (4 pasang Q&A) sebagai dialog lengkap.
- Jika percakapan baru: kirim max 3 pesan user terakhir saja.

**Timeout & Error Handling (diperbarui):**
- Timeout default naik dari `30.0` → **`60.0` detik** untuk mengakomodasi pipeline yang lebih complex.
- `asyncio.TimeoutError`: return dict dengan `bot_text` user-friendly ("Maaf, sistem sedang sibuk...") dan `error: False` — pipeline tidak crash, pesan tersimpan di history.
- `Exception` umum: juga return dict dengan `bot_text` user-friendly ("Maaf, sistem mengalami kendala...") dan `error: False` — resilient terhadap semua error tak terduga.

---

#### `app/web/services/report_service.py` — ReportService

**Class `ReportService`:**

| Method | Return | Detail |
|--------|--------|--------|
| `generate(ticket_id, prepared_by="Tim Keamanan Siber Pusdatin")` | `tuple[str, str]` | Query tiket → convert ke dict → `generate_report_html()` → return (html_string, filename) |

---

#### `app/web/services/upload_service.py` — UploadService

**Konstanta:**
- `MAX_SIZE_BYTES = 10 * 1024 * 1024` (10 MB)
- `ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}`
- `ALLOWED_MIMES = {"application/pdf", "image/png", "image/jpeg"}`

**Class `UploadService`:**

| Method | Return | Detail |
|--------|--------|--------|
| `save_pending(session_id, filename, data: bytes)` | dict | Validasi extension + size + MIME (via python-magic). Buat subdirektori bulan. Simpan dengan nama UUID. Simpan metadata di Redis. |
| `flush_pending(session_id)` | `list[dict]` | Ambil + hapus metadata dari Redis. Dipakai saat tiket dibuat. |
| `get_pending(session_id)` | `list[dict]` | View tanpa penghapusan. |

---

## 13. app/utils/ — Utilitas Internal

### `app/utils/llm_client.py`

| Fungsi | Return | Detail |
|--------|--------|--------|
| `_resolve_api_key() → str` | str | Pilih `OPENAI_API_KEY` atau `GITHUB_TOKEN`. Raise jika keduanya kosong. |
| `create_llm_client() → AsyncOpenAI` | `AsyncOpenAI` | Resolve key. Jika `OPENAI_BASE_URL` di-set → gunakan sebagai `base_url` (GitHub Models mode). |
| `create_embedder() → OpenAIEmbeddings` | `OpenAIEmbeddings` | Model `text-embedding-3-small`. Dukung GitHub Models via `openai_api_base`. |

**GitHub Models mode:** Ganti `OPENAI_BASE_URL=https://models.inference.ai.azure.com` dan pakai `GITHUB_TOKEN` → hemat kuota OpenAI saat dev.

---

### `app/utils/llm_parser.py`

**Fungsi `parse_llm_json(raw: str) → dict | None`:**
1. Coba `json.loads(raw)` langsung.
2. Coba ekstrak substring `{...}` pertama lalu parse.
3. Return `None` jika keduanya gagal.

**Mengapa perlu ini?** LLM sering mengembalikan output dengan code fence ` ```json ... ``` ` atau teks penjelasan sebelum JSON.

---

### `app/utils/prompt_loader.py`

**Fungsi `load_prompt(agent_name: str) → str`:**
- Baca `config/prompts/{agent_name}.txt`.
- Raise `FileNotFoundError` jika tidak ada.
- Return string prompt siap dipakai.

---

### `app/utils/audit.py`

**Fungsi `log_audit_event(...) → None`:**
- Async wrapper via `asyncio.to_thread()` — tidak blokir event loop.
- Non-blocking on failure (log warning saja).

**Class `PipelineAuditContext`:**
- Async context manager (`async with PipelineAuditContext(...)`).
- `__aenter__`: Catat waktu mulai.
- `__aexit__`: Hitung latency, capture error jika ada, panggil `log_audit_event()`.

---

### `app/utils/logger.py`

**Fungsi `configure_logging()`:**
- Setup root logger dengan JSON formatter (structlog).
- Suppress log verbose dari library: httpx, openai, httpcore.
- Baca `LOG_LEVEL` dari env.

**Fungsi `get_logger(name) → BoundLogger`:** Return structlog logger untuk modul tertentu.

---

## 14. config/prompts/ — Template Prompt LLM

### `orchestrator.txt` — Intent Classification

**Tugas:** Klasifikasikan pesan pengguna ke satu dari 4 intent.
**Input:** Teks pesan yang sudah disanitasi.
**Output JSON:**

```json
{
  "intent": "report_incident|query_status|general_help|needs_clarification",
  "confidence": 0.0-1.0,
  "needs_clarification": false,
  "clarification_message": ""
}

```

**Instruksi kunci di prompt:** Jika pesan sangat ambigu atau tidak ada informasi teknis → `needs_clarification`. Jika menyebut tiket ID → `query_status`. Default ambiguous → `report_incident`.

---

### `identifier.txt` — Incident Classification

**Tugas:** Klasifikasikan jenis insiden + severity dari deskripsi.
**Input:** Teks deskripsi insiden.
**Output JSON:**

```json
{
  "incident_type": "Phishing|Malware|Ransomware|...|Lainnya",
  "severity": "Kritis|Tinggi|Sedang|Rendah|Informasional",
  "confidence_score": 0.0-1.0,
  "reasoning": "penjelasan singkat",
  "requires_review": false
}

```

**Instruksi kunci:** Definisi tiap jenis insiden. Kriteria severity (Kritis = layanan kritis down/ransomware aktif, dll.). Jika tidak yakin → `requires_review=True`. Bahasa Indonesia.

---

### `mitigation.txt` — Mitigasi RAG

**Tugas:** Generate rekomendasi mitigasi berdasarkan context dokumen yang diambil.
**Input yang diinjeksi:**
- `{context}` — assembled chunk dari RAG retrieval
- `{incident_type}` — dari identifier
- `{severity}` — dari identifier
- `{user_report}` — `sanitized_input`

**Output JSON:**

```json
{
  "mitigation_steps": [
    {"step": 1, "action": "...", "source": "NIST SP 800-61 / MITRE M1xxx", "detail": "..."}
  ],
  "general_guidance": "ringkasan singkat",
  "escalation_note": "rekomendasi eskalasi jika perlu"
}

```

**Instruksi kunci:** Cite source per step. Maksimal 5 step. Bahasa Indonesia. Jangan halusinasi — hanya dari context yang diberikan. Format citation yang diakui.

---

## 15. scripts/ — CLI Tools

### `scripts/ingest_knowledge.py`

**CLI untuk batch ingest** dokumen ke Qdrant.

**Argumen CLI:**

| Arg | Default | Fungsi |
|-----|---------|--------|
| `--docs-dir` | `knowledge_base/docs` | Direktori PDF |
| `--metadata-dir` | `knowledge_base/metadata` | Direktori JSON metadata |
| `--stix-file` | `knowledge_base/enterprise-attack.json` | Path STIX bundle |
| `--stix-only` | False | Skip PDF, hanya STIX |

**Alur:**
1. Load dan chunk PDF (jika tidak `--stix-only`).
2. Parse MITRE ATT&CK STIX (mitigations + techniques).
3. Embed semua chunk via `embed_chunks()`.
4. `ensure_collection()` → `upload_chunks()` ke Qdrant.
5. Log total chunk ter-ingest.

---

### `scripts/seed_admin.py`

**CLI untuk buat admin pertama** saat pertama deploy.

**Alur:**

1. Auto-inject root repo ke `sys.path` (agar bisa dijalankan langsung dengan `python scripts/seed_admin.py` dari direktori manapun tanpa perlu `PYTHONPATH`).
2. Prompt interaktif: username, email, full_name, password.
3. Hash password: `bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`.
4. Insert ke tabel `admins` via SQLAlchemy.
5. Exit 0 jika sukses, exit 1 jika error.

---

### `scripts/e2e_test.py`

**Skenario E2E via REST API** (bukan pytest — dijalankan manual).

**5 Skenario test:**

| # | Skenario | Ekspektasi |
|---|---------|-----------|
| 1 | Laporan phishing email | `intent=report_incident`, ada `ticket_id`, `incident_type=Phishing` |
| 2 | Laporan ransomware | `severity∈{Kritis,Tinggi}`, `mitigation_recommendation` terisi |
| 3 | Pesan ambigu | `requires_clarification=True` |
| 4 | Prompt injection | `guardrail_blocked=True` (atau tidak ada ticket_id) |
| 5 | Laporan akses tidak sah | `incident_type=Akses Tidak Sah` |

**Cara jalankan:** `python scripts/e2e_test.py --base-url http://localhost:8000`

---

## 16. tests/ — Test Suite

**Total: 55+ file, 220+ test lulus.**

### Struktur dan Coverage

| Direktori | File | Yang Ditest |
|-----------|------|------------|
| `test_agents/` | `test_orchestrator.py` | classify_intent(), initialize_state(), fallback behavior |
| | `test_identifier.py` | classify() untuk 8 jenis + 5 severity, edge cases |
| | `test_mitigation.py` | Agentic RAG loop, adequacy check, citation validation |
| | `test_ticket_manager.py` | create_ticket(), duplikat detection, ESCALATION_MAP |
| | `test_notifier.py` | send_notifications(), dual-channel, non-blocking failure |
| | `test_graph.py` | Integrasi alur penuh: guardrails fail → END, happy path |
| `test_rag/` | `test_chunker.py` | chunk_documents(), size, overlap, header preservation |
| | `test_ingestion.py` | PDF loader, STIX parser (mitigations + techniques) |
| | `test_retriever.py` | HybridRetriever, RRF merge, keyword search |
| | `test_reranker.py` | _compute_final_score(), incident_type boost, top_k |
| `test_security/` | `test_guardrails.py` | Fail-closed behavior, blocked vs safe |
| | `test_sanitizer.py` | HTML strip, unicode normalization, truncation |
| | `test_pii_redactor.py` | IP, email, NIK, phone redaction + restore |
| | `test_prompt_injection.py` | Regex patterns, base64 heuristic, false positives |
| | `test_validator.py` | PII di output, empty output, meaningful content |
| `test_database/` | `test_repository.py` | CRUD, generate_ticket_id, check_duplicate, get_stats |
| `test_telegram/` | `test_bot.py` | Handler functions, ConversationHandler states |
| `test_web/` | 30+ file | Routes, services, middleware CSRF, auth flow, chat flow, integration tests |
| `evaluation/` | `eval_rag.py` | RAGAs metrics: Context Relevance, Answer Relevance, Faithfulness |
| | `eval_tcr.py` | Task Completion Rate: 35 skenario insiden |
| | `eval_report.py` | Kelengkapan format laporan HTML |
| | `eval_ragas.py` *(baru)* | Script evaluasi menggunakan RAGAS framework secara langsung terhadap pipeline |
| | `rag_qa_dataset.json` *(diperbarui)* | Dataset QA berbasis skenario nyata MITRE ATT&CK. QA-011 s/d QA-020 direvisi; QA-021–QA-030 dihapus. |
| | `rag_results.json` *(baru)* | Hasil raw evaluasi RAG (per-query metrics) |
| | `rag_ragas_results.json` *(baru)* | Hasil evaluasi RAGAS framework (context relevance, answer relevance, faithfulness) |

### Pola Testing

- **Unit test agen:** Mock `llm_client` dan `repository`, buat dummy state, assert output fields.
- **Integration test graph:** Mock semua dependency, jalankan `build_helpdesk_graph().ainvoke()`, assert state akhir.
- **Security test:** Input berbahaya harus menghasilkan `blocked=True`, tidak ada PII di output.
- **Web test:** TestClient FastAPI, mock session, test HTMX fragment responses.

---

## 17. Infrastruktur & Deployment

| File | Tujuan |
|------|--------|
| `docker-compose.yml` | Container: PostgreSQL 16, Redis 7, Qdrant |
| `Dockerfile` | Image FastAPI (uvicorn, production mode) |
| `alembic.ini` | Konfigurasi Alembic — URL DB dari env |
| `requirements.txt` | Semua dependency pinned (reproducible) |
| `pytest.ini` | Test path, marker, coverage config |
| `.env.example` | Template env vars; `.env` aktual tidak di-commit |

**Cara run development:**

```bash
docker compose up -d          # PostgreSQL + Redis + Qdrant
alembic upgrade head          # Migrasi database
python scripts/seed_admin.py  # Buat admin pertama
python scripts/ingest_knowledge.py  # Ingest knowledge base
uvicorn app.main:app --reload # FastAPI
python -m app.telegram.run    # Telegram bot (proses terpisah)

```

---

## 18. Peta Interaksi Modul

```

app/main.py
│
├─▶ app/api/routes.py (REST API /api/v1/*)
│     └─▶ app/api/dependencies.py
│           ├─▶ app/agents/graph.py → build_helpdesk_graph()
│           │     ├─▶ guardrails_node → app/security/guardrails.py
│           │     │     ├─▶ app/security/sanitizer.py
│           │     │     ├─▶ app/security/prompt_injection.py
│           │     │     └─▶ app/security/pii_redactor.py
│           │     ├─▶ classify_intent → app/agents/orchestrator.py
│           │     │     └─▶ app/utils/llm_client.py (AsyncOpenAI)
│           │     │     └─▶ app/utils/prompt_loader.py (orchestrator.txt)
│           │     ├─▶ identify_incident → app/agents/identifier.py
│           │     │     └─▶ app/utils/llm_client.py
│           │     │     └─▶ app/utils/prompt_loader.py (identifier.txt)
│           │     ├─▶ generate_mitigation → app/agents/mitigation.py
│           │     │     ├─▶ app/rag/retriever.py (HybridRetriever)
│           │     │     │     └─▶ app/rag/embedder.py (OpenAI embeddings)
│           │     │     ├─▶ app/rag/reranker.py
│           │     │     └─▶ app/utils/llm_client.py (AsyncOpenAI)
│           │     │     └─▶ app/utils/prompt_loader.py (mitigation.txt)
│           │     ├─▶ validate_output → app/security/validator.py
│           │     ├─▶ create_ticket → app/agents/ticket_manager.py
│           │     │     └─▶ app/database/repository.py (TicketRepository)
│           │     │           └─▶ app/database/models.py (IncidentTicket)
│           │     │           └─▶ app/database/connection.py (Session)
│           │     └─▶ send_notification → app/agents/notifier.py
│           │           └─▶ app/telegram/templates.py
│           └─▶ app/database/connection.py
│
├─▶ app/web/app.py (register_web)
│     ├─▶ app/web/middleware/ (CSRF, Security Headers, Rate Limit)
│     ├─▶ app/web/routes/landing.py
│     ├─▶ app/web/routes/pelapor.py
│     │     └─▶ app/web/services/chat_service.py → graph.ainvoke()
│     │     └─▶ app/web/services/upload_service.py
│     ├─▶ app/web/routes/admin_auth.py
│     │     └─▶ app/web/services/auth_service.py (bcrypt + Redis lockout)
│     ├─▶ app/web/routes/admin_inbox.py
│     ├─▶ app/web/routes/admin_actions.py
│     ├─▶ app/web/routes/admin_rag.py
│     └─▶ app/web/routes/admin_report.py
│           └─▶ app/web/services/report_service.py
│
└─▶ (Proses terpisah) app/telegram/bot.py
      ├─▶ build_bot_application() → PTB Application
      ├─▶ ConversationHandler /report → graph.ainvoke()
      ├─▶ /status → app/database/repository.py
      └─▶ _send_result() → app/telegram/templates.py

Infrastruktur (Docker):
  PostgreSQL 16 ← app/database/connection.py
  Redis 7       ← app/web/services/auth_service.py
                ← app/web/services/chat_service.py
                ← app/web/services/upload_service.py
  Qdrant        ← app/rag/embedder.py
                ← app/rag/retriever.py

```

---

## 19. Security Audit & Fixes (2026-04-21)

### Ringkasan Audit

Audit keamanan menyeluruh dilakukan pada web module sebelum sidang. **8 isu nyata diperbaiki** (HIGH: 5, MED: 3), 88 test lulus. Pre-existing failures (2 test di `/lapor/chat/reset`) tidak terkait fix.

### Isu yang Diperbaiki

#### 1. XSS (Cross-Site Scripting) — `admin_actions.py:70, 93`

**Masalah:** Nilai `assignee` dan `level` (user-controlled) langsung diinterpolasi ke `HTMLResponse()` tanpa HTML-escape:

```python
return HTMLResponse(f'<p>Ditugaskan ke <strong>{assignee}</strong></p>')

```

Jika `assignee` berisi `<img onerror=alert(1)>`, maka XSS terjadi.

**Fix:**

```python
import html
return HTMLResponse(f'<p>Ditugaskan ke <strong>{html.escape(assignee)}</strong></p>')

```

Juga apply di `level` output. Validasi pada layar controller tetap bernilai (TICKET_STATUSES, ESCALATION_LEVELS) karena constrained, tapi output HTML harus selalu safe.

**Sumber:** CWE-79 (Improper Neutralization of Input During Web Page Generation).

---

#### 2. Path Traversal — `admin_actions.py:142`

**Masalah:** Endpoint download attachment memvalidasi filename tapi tidak memastikan `raw_path` (dari DB) **berada di dalam `UPLOAD_ROOT`**:

```python
abs_path = os.path.abspath(raw_path)
if not os.path.isfile(abs_path):
    raise HTTPException(status_code=404, detail="File fisik hilang.")
return FileResponse(abs_path, filename=filename)

```

Jika attacker bisa inject `raw_path="/etc/passwd"` (misalnya via vulnerability upload lain), endpoint ini akan serve file arbitrary.

**Fix:**

```python
abs_path = os.path.abspath(raw_path)
try:
    if os.path.commonpath([abs_path, UPLOAD_ROOT]) != UPLOAD_ROOT:
        raise HTTPException(status_code=400, detail="Path file di luar direktori upload.")
except ValueError:
    raise HTTPException(status_code=400, detail="Path file tidak valid.")

```

Memastikan `commonpath` == `UPLOAD_ROOT` (standar path traversal mitigation).

**Sumber:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory).

---

#### 3. Path Traversal — `rag_service.py:52` (upload_pdf)

**Masalah:** Fungsi `upload_pdf()` menerima `filename` dan `doc_id` user-controlled, kemudian dipakai sebagai path:

```python
safe_name = filename.replace(" ", "_")  # ← insufficient sanitasi
save_pdf(safe_name, data)               # → _DOCS_DIR / safe_name
meta_filename = f"{doc_id}.json"        # → _META_DIR / meta_filename

```

Attacker bisa kirim `doc_id="../../../etc/passwd"` atau `filename="../../evil.pdf"` → write outside base dir.

**Fix:**

```python
_DOC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")

if not _DOC_ID_RE.match(doc_id):
    raise ValueError("doc_id hanya boleh alfanumerik, dash, underscore (maks 64 char).")
base_name = Path(filename).name  # Extract basename saja, buang dir traversal
if not base_name or base_name.startswith("."):
    raise ValueError("Nama file tidak valid.")
safe_name = base_name.replace(" ", "_")
if not safe_name.lower().endswith(".pdf"):
    raise ValueError("File harus berekstensi .pdf")

```

`Path(filename).name` adalah cara aman di Python untuk mengambil nama file saja (strip semua path prefix).

**Sumber:** CWE-22.

---

#### 4. Hardcoded Default Secrets — `config.py:12-13`

**Masalah:** Session dan CSRF secret memiliki default string `"change-me-in-prod-..."` yang tidak akan diganti jika env var tidak di-set:

```python
session_secret: str = "change-me-in-prod-64-chars-minimum-aaaaaaaaaaaaaaaaaaaaaaaaaa"
csrf_secret: str = "change-me-in-prod-csrf-64-chars-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

```

Jika deployment lupa set `WEB_SESSION_SECRET` dan `WEB_CSRF_SECRET`, secret ini akan **identik untuk semua instance**, memungkinkan session fixation / CSRF bypass.

**Fix:**

```python
_DEV_SESSION_SECRET = "change-me-in-prod-64-chars-minimum-aaaaaaaaaaaaaaaaaaaaaaaaaa"
_DEV_CSRF_SECRET = "change-me-in-prod-csrf-64-chars-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

@lru_cache
def get_web_config() -> WebConfig:
    config = WebConfig()
    if config.cookie_secure and (
        config.session_secret == _DEV_SESSION_SECRET
        or config.csrf_secret == _DEV_CSRF_SECRET
    ):
        raise RuntimeError(
            "Default session/csrf secret terdeteksi sementara cookie_secure=True. "
            "Set WEB_SESSION_SECRET dan WEB_CSRF_SECRET via env var."
        )
    return config

```

Fail-closed: jika `cookie_secure=True` (indikator production), tapi secret default, app crash at startup (better than silent vulnerability).

**Sumber:** CWE-798 (Use of Hard-Coded Credentials).

---

#### 5. Username Enumeration (Timing Attack) — `auth_service.py:52`

**Masalah:** Login handler membedakan timing antara "user tidak ada" vs "password salah":

```python
if admin is None:
    bcrypt.using(rounds=4).hash("dummy")  # Hanya 4 round, super cepat!
    time.sleep(0.1)
    self._increment_failure(lockout_key)
    return AuthResult(success=False, error="invalid_credentials")

if not bcrypt.verify(password, admin.password_hash):  # rounds=12
    time.sleep(0.1)
    self._increment_failure(lockout_key)
    return AuthResult(success=False, error="invalid_credentials")

```

Attacker bisa measure timing: jika response cepat, user tidak ada; jika lambat, user ada. Dengan ini attacker bisa enumerate username valid.

**Fix:**

```python
_DUMMY_HASH = bcrypt.using(rounds=12).hash("dummy-password-for-timing-defense")

# Di method authenticate():
if admin is None:
    bcrypt.verify(password, _DUMMY_HASH)  # Verify terhadap hash real (rounds=12)
    self._increment_failure(lockout_key)  # Tanpa hardcoded sleep
    return AuthResult(success=False, error="invalid_credentials")

```

Dengan ini, path "user tidak ada" dan "password salah" keduanya melakukan `bcrypt.verify(rounds=12)`, sehingga timing serupa. Attacker tidak bisa bedakan.

**Sumber:** CWE-208 (Observable Timing Discrepancy).

---

#### 6. Race Condition — `chat_service.py:135`

**Masalah:** `_flush_pending_uploads()` mengambil data upload dari Redis, lalu hapus:

```python
pending_raw = self._redis.get(f"web:pending_uploads:{session_id}")
if not pending_raw:
    return
self._redis.delete(f"web:pending_uploads:{session_id}")  # ← separate call
for meta in json.loads(pending_raw):
    # insert ke DB
    db.add(TicketAttachment(...))

```

Jika dua request concurrent dengan `session_id` sama, bisa terjadi:
1. Request A: `GET` → dapat data
2. Request B: `GET` → dapat data (sama)
3. Request A: `DELETE` → hapus
4. Request B: `DELETE` → hapus (sudah kosong, tapi OK)
5. Kedua request insert ke DB → duplikat attachment

**Fix:**

```python
pipe = self._redis.pipeline()
pipe.get(key)
pipe.delete(key)
pending_raw, _ = pipe.execute()  # ← atomic

```

Pipeline memastikan GET+DELETE adalah atomic operation (dari perspektif Redis), tidak bisa di-interleave oleh request lain.

**Sumber:** CWE-362 (Concurrent Execution using Shared Resource with Improper Synchronization).

---

#### 7. JSON Parse Error Handling — `chat_service.py:35`, `rag_service.py:73`, `upload_service.py:55`

**Masalah:** Per CLAUDE.md rule, **JSON parsing WAJIB error handling**. Namun di tiga service, `json.loads()` tidak di-wrap try/except:

```python
# chat_service.py:35
return json.loads(raw)  # Crash jika Redis corrupt

# rag_service.py:73
return json.loads(raw)  # Crash

# upload_service.py:55
existing = json.loads(self._redis.get(key) or b"[]")  # Crash

```

Jika Redis corruption terjadi (rare tapi possible), requests crash dengan 500 error.

**Fix:** Wrap semua dengan try/except + log + return safe default:

```python
def get_history(self, session_id: str) -> list[dict]:
    raw = self._redis.get(f"web:chat:{session_id}")
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        logger.warning("Corrupt chat history session=%s, reset", session_id[:8])
        self._redis.delete(f"web:chat:{session_id}")
        return []

```

Juga apply di `rag_service.py:get_job_status()`, `rag_service.py:run_ingest()`, dan `upload_service.py` helpers.

**Sumber:** CWE-1025 (Comparison Using Wrong Factors) — implicit; best practice untuk input validation boundary.

---

#### 8. Missing ValueError Handling — `admin_rag.py:68`

**Masalah:** Route `upload_document` memanggil `svc.upload_pdf()` tapi tidak catch `ValueError` yang bisa dilempar dari path traversal validation:

```python
meta_filename = svc.upload_pdf(
    filename=filename, data=data, doc_id=doc_id,
    doc_title=doc_title, source_framework=source_framework,
    incident_types=types_list, language=language,
)

```

Jika `doc_id` invalid atau `filename` buruk, `ValueError` tidak tertangkap → 500 error.

**Fix:**

```python
from fastapi import HTTPException

try:
    meta_filename = svc.upload_pdf(...)
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))

```

Mengubah 500 Internal Server Error menjadi 400 Bad Request yang informatif.

---

### Test Impact

| File | Test Lama | Test Baru | Status |
|------|-----------|-----------|--------|
| `test_admin_actions.py` | 10 | 10 | ✅ All pass |
| `test_services/` (auth, chat, upload, rag) | 49 | 49 | ✅ All pass |
| `test_middleware/` (CSRF, headers) | ? | ? | ✅ All pass |
| `test_web/` total | 90 | 90 | ✅ 88 pass, 2 pre-existing fail |

Pre-existing failures: `test_reset_clears_session`, `test_reporter_full_flow` (unrelated to security fixes, terkait flow `/lapor/chat/reset`).

Regression test: `test_attachment_download_streams_file` diperbaiki via monkeypatch `UPLOAD_ROOT` ke `tmp_path` agar comply dengan path guard baru.

---

### Checklist Compliance

| Aturan CLAUDE.md | Isu | Fix |
|---|---|---|
| "PII WAJIB di-redact sebelum kirim ke LLM API" | Sudah diterapkan di guardrails, audit confirm OK | ✓ |
| "API key, token, password: HANYA dari env vars" | Default secret di config bisa lolos ke prod | Fixed: fail-closed jika default tetap + cookie_secure |
| "LLM output selalu parse sebagai JSON dengan error handling" | Chat history, RAG job status, upload pending list tidak di-wrap | Fixed: try/except + log + default aman |
| "Setiap agen harus punya fallback" | Web routes kurang fallback di error handling | Partial: auth & upload sekarang return 400 terstruktur |
| "Fail-closed: guardrails gagal → blokir, jangan teruskan" | Path traversal bisa terjadi jika attacker control DB | Fixed: path guard di download, filename validation di upload |

---

### Rekomendasi Post-Audit

1. **Rate-limit endpoint upload** (admin_rag.py) untuk cegah DoS.
2. **Log semua error 400+** di endpoint CRUD ticket/attachment untuk deteksi attack pattern.
3. **Rotate session secret periodik** (3 bulan) jika deployment prod.
4. **Input validation di layer frontend** (JavaScript) untuk UX lebih baik (client-side validation + server-side validation berlapis).

---

## 20. Tabel Q&A Sidang

| Pertanyaan Dosen | Jawaban + Referensi Kode |
|------------------|--------------------------|
| **Apa beda sistem ini dengan chatbot biasa?** | Multi-agent via LangGraph: tiap tahap (triase, klasifikasi, mitigasi, tiket, notifikasi) adalah node independen yang berkomunikasi **hanya via `IncidentState`**, bukan satu prompt besar. Testable per node, conditional routing, fail-closed. → `app/agents/graph.py` |
| **Kenapa Agentic RAG?** | RAG naive gagal pada query ambigu. Agentic RAG memeriksa `_check_adequacy()` dan meng-`_expand_query()` secara iteratif max 3×. → `app/agents/mitigation.py` konstanta `MAX_ITERATIONS=3` |
| **Bagaimana menjamin jawaban tidak halusinasi?** | `_validate_citations()`: tiap step harus ada source-nya di chunk terpilih. Reranker juga mendorong chunk yang incident_type-nya match. → `app/agents/mitigation.py`, `app/rag/reranker.py` |
| **Kenapa hybrid retrieval?** | Semantic unggul sinonim, keyword unggul istilah teknis (CVE, M1040). RRF (`RRF_K=60`) menggabungkan secara fair. → `app/rag/retriever.py` |
| **Bagaimana melindungi PII?** | Fail-closed guardrails: PII (IP, email, NIK, telepon) diredaksi regex **sebelum** teks dikirim ke OpenAI API. Prompt injection diblokir di layer yang sama. → `app/security/guardrails.py`, `app/security/pii_redactor.py` |
| **Kenapa tiket baru `PENDING_REVIEW`?** | Sistem adalah **pra-triase**, bukan pengambil keputusan akhir. Analis CSIRT tetap harus meninjau. → `app/database/repository.py` method `create_ticket()` |
| **Kenapa LangGraph, bukan chain LangChain?** | Conditional routing eksplisit, state-driven, testable per node. Chain LangChain terlalu rigid untuk conditional short-circuit. → `app/agents/graph.py` `add_conditional_edges()` |
| **Bagaimana mengukur performa?** | 3 metrik: TCR (35 skenario, ≥80%), RAG/RAGAs (CR/AR/Faith ≥0.75/0.80/0.85), SUS (≥68). Script di `tests/evaluation/`. |
| **Apakah sistem bisa diperluas?** | Ya — ganti `config/prompts/*.txt` (tanpa deploy ulang), ganti `knowledge_base/`, ubah `_TACTIC_TO_INCIDENT_TYPES` di `ingestion.py`. Logika agen tidak perlu diubah. |
| **Apa kelemahan?** | Bergantung ke LLM eksternal (latency + biaya), knowledge base statik (perlu re-ingest manual), belum ada feedback loop dari analis ke model, `_check_adequacy()` hanya berbasis skor tanpa semantik. |
| **Kenapa `CHUNK_SIZE=800, OVERLAP=100`?** | Kompromi: cukup besar untuk koherensi paragraf (NIST SP 800-61 punya paragraf panjang), cukup kecil untuk presisi retrieval. Overlap 100 menjaga kontinuitas kalimat antar chunk. → `app/rag/chunker.py` |
| **Kenapa base64 heuristic di injection detector?** | Penyerang bisa encode "ignore previous instructions" ke base64 untuk bypass regex literal. Heuristic: decode string panjang ≥40 char yang cocok pola base64, cek hasilnya. → `app/security/prompt_injection.py` `_check_base64()` |
| **Mengapa `RRF_K=60`?** | Nilai standar dari literatur Information Retrieval (Cormack et al., 2009). Nilai ini memberikan trade-off yang baik antara menghargai dokumen di ranking tinggi vs rendah. → `app/rag/retriever.py` |
| **Kenapa ada dua kanal (Telegram + Web)?** | Telegram familiar bagi pelapor awam tanpa butuh akun baru. Web HTMX menyediakan dashboard admin yang lebih kaya fitur (filter, attachment, laporan) tanpa kompleksitas React. |
| **Bagaimana sistem mencegah tiket duplikat?** | `check_duplicate()` di repository: cari tiket dari `reporter_id` yang sama dengan deskripsi identik dalam 24 jam. Jika ada, kembalikan tiket lama dengan `is_duplicate=True`. → `app/agents/ticket_manager.py`, `app/database/repository.py` |
| **Bagaimana Redis dipakai di sistem ini?** | Tiga kegunaan: 1) Rate-limit & lockout login admin (`auth_service.py`); 2) Riwayat chat multi-turn pelapor TTL 24h (`chat_service.py`); 3) Metadata file pending upload per session (`upload_service.py`). |

---

## 21. Perubahan Terbaru (2026-05-30)

Perubahan berikut dicommit ke branch `feat/web-plan-a`. Ringkasan per komponen:

### 21.1 `app/agents/mitigation.py` — Perbaikan Citation Validation

**`_validate_citations(steps, chunks)`** kini mengecek **6 field metadata** dari setiap chunk (sebelumnya hanya 2):

| Field (sebelum) | Field (sekarang) |
|----------------|-----------------|
| `source` | `source` |
| `section` | `section` |
| — | `doc_title` *(baru)* |
| — | `section_header` *(baru)* |
| — | `source_framework` *(baru)* |
| — | `external_id` *(baru)* |

Ini meningkatkan recall validation: referensi ke framework ID (misal `M1049`) atau judul dokumen resmi kini bisa terdeteksi meski tidak match persis dengan field `source`.

Variabel `reranked` diinisialisasi sebelum loop iterasi RAG dimulai untuk menghindari `UnboundLocalError` jika loop tidak pernah berjalan.

---

### 21.2 `app/agents/notifier.py` — Konstanta Fallback Chat ID

Dua konstanta baru ditambahkan untuk meningkatkan maintainability dan production reliability:

```python
_CSIRT_CHAT_ID_ENV = "CSIRT_CHAT_ID"
_CSIRT_CHAT_ID_FALLBACK = "-1003971618295"
```

`_get_csirt_recipients()` menggunakan `os.getenv(_CSIRT_CHAT_ID_ENV, _CSIRT_CHAT_ID_FALLBACK)` sehingga selalu ada nilai fallback jika env var tidak tersedia. Berbeda dengan `bot.py` yang sengaja return `None` untuk test isolation.

---

### 21.3 `app/rag/retriever.py` — Compatibility Shim untuk Test Mock

`HybridRetriever.retrieve()` kini memiliki **compatibility shim** pada tahap semantic search:

```python
if hasattr(self.client, "search"):
    # Pakai client.search() — backward compatible dengan mock lama
    ...
else:
    # Pakai client.query_points() — Qdrant client API baru
    ...
```

Field `score` diakses via `getattr(hit, "score", 0.0)` agar robust. Perubahan ini memastikan test suite yang masih menggunakan mock `client.search` tidak perlu diubah.

---

### 21.4 `app/telegram/bot.py` — Rename Fungsi + Perilaku Test-Safe

Fungsi `_get_csirt_chat_id()` **diganti nama** menjadi `_get_admin_chat_id()`. Perilaku berubah:

| Kondisi | Sebelum | Sekarang |
|---------|---------|---------|
| Env var di-set | Return nilai env var | Return nilai env var |
| Env var tidak di-set | Return fallback ID | Return `None` |

Dengan return `None` saat env var tidak diset, test dapat meng-assert perilaku "tidak ada chat ID" tanpa harus meng-unset/override env var secara eksplisit.

---

### 21.5 `app/web/middleware/csrf.py` — Token Session Guarantee

Logika safe method dipertegas: token **selalu** dijamin ada di session setelah GET request. Kondisi pengecekan menggunakan `if SESSION_KEY not in session` (bukan check kosong), sehingga token yang sudah ada tidak di-overwrite. Perilaku fungsional tidak berubah, tapi lebih eksplisit dan robust.

---

### 21.6 `app/web/routes/admin_report.py` — CSRF Token Fallback

Route `GET /admin/report` (`report_page`) kini memiliki fallback eksplisit:

```python
if "csrf_token" not in request.session:
    request.session["csrf_token"] = secrets.token_urlsafe(32)
```

Ini mengatasi edge case di mana middleware belum sempat meng-inject token ke session sebelum route dipanggil (misalnya pada request pertama tanpa session cookie).

---

### 21.7 `app/web/routes/pelapor.py` — HTMX-Aware Reset

`reset_session()` kini **membedakan HTMX request vs non-HTMX**:

```python
is_hx = str(request.headers.get("HX-Request", "")).lower() == "true"
if is_hx:
    response = HTMLResponse("", status_code=200)
    response.headers["HX-Redirect"] = "/lapor"
    return response
return RedirectResponse(url="/lapor", status_code=303)
```

HTMX tidak mengikuti redirect HTTP standar — ia perlu header `HX-Redirect` untuk navigasi halaman penuh. Non-HTMX client (browser biasa, tes HTTP) mendapat redirect 303 standar.

---

### 21.8 `app/web/services/chat_service.py` — Timeout & Error Handling

Tiga perubahan signifikan pada `handle_message()`:

1. **Timeout naik: `30.0` → `60.0` detik** — mengakomodasi pipeline yang lebih lambat karena multi-agent + RAG iteratif.

2. **`asyncio.TimeoutError` tidak lagi return `{"error": True}`** — sekarang return pesan user-friendly dengan `error: False`:
   ```python
   bot_text = "Maaf, sistem sedang sibuk memproses laporan Anda. Silakan coba kirim ulang pesan dalam beberapa saat lagi."
   return {"bot_text": bot_text, "error": False, ...}
   ```
   Pesan tersimpan di history Redis sehingga percakapan tidak hilang.

3. **Ditambah handler `except Exception`** — menangkap semua error tak terduga (koneksi DB, LLM error, dsb.) dengan pesan user-friendly yang sama, `error: False`.

---

### 21.9 Template Branding

Label organisasi di 4 file template diperbarui menjadi lebih generik:
- `app/web/templates/admin/login.html`
- `app/web/templates/pelapor/chat.html`
- `app/web/templates/pelapor/identitas.html`
- `app/web/templates/pelapor/tiket_detail.html`

Perubahan: "Pusdatin CSIRT" → **"Helpdesk"**, "Kementerian Pertanian RI" → **"Tim Keamanan Siber"**.

---

### 21.10 `tests/evaluation/` — Dataset & Hasil Evaluasi Baru

| File | Status | Keterangan |
|------|--------|-----------|
| `eval_ragas.py` | Baru | Script evaluasi menggunakan RAGAS framework |
| `rag_results.json` | Baru | Hasil raw evaluasi RAG per-query |
| `rag_ragas_results.json` | Baru | Hasil evaluasi RAGAS (context relevance, answer relevance, faithfulness) |
| `rag_qa_dataset.json` | Diperbarui | QA-011 s/d QA-020 direvisi dengan skenario nyata MITRE ATT&CK; QA-021–QA-030 dihapus |

---

---

## 22. Perubahan Terbaru (2026-06-02)

Perubahan berikut belum di-commit ke remote — merupakan penyempurnaan pipeline RAG, perbaikan keamanan tambahan, dan upgrade evaluasi RAGAS ke v2 API.

---

### 22.1 `app/agents/mitigation.py` — Tuning RAG Pipeline

**Konstanta yang berubah:**

| Konstanta | Nilai Lama | Nilai Baru | Alasan |
|-----------|-----------|-----------|--------|
| `RETRIEVAL_SCORE_THRESHOLD` | `0.3` | `0.22` | Threshold lama terlalu ketat, banyak chunk relevan terbuang |
| `TOP_K_RETRIEVAL` | `20` | `30` | Lebih banyak kandidat → reranker punya ruang lebih untuk memilih |

**`_assemble_context()` — Fallback metadata:**

Source label kini menggunakan chain fallback: `source → doc_title → source_framework → "Dokumen tidak diketahui"`. Section juga fallback ke `section_header`. Ini penting karena banyak chunk MITRE ATT&CK tidak mengisi field `source` tapi punya `doc_title`.

**`_expand_query()` — Query bersih pada iterasi 2:**

Iterasi ke-2 kini menghasilkan query yang sepenuhnya bersih (`"mitigasi langkah respons {incident_type} {keywords}"`) alih-alih append ke query awal yang panjang. Ini membantu retriever menemukan chunk "Mitigasi MITRE ATT&CK" yang relevan tanpa terkontaminasi deskripsi skenario.

**`generate_mitigation()` — Smart loop break condition:**

Loop RAG tidak lagi berhenti begitu `_check_adequacy()` terpenuhi di iterasi 1. Jika lebih dari separuh chunk didominasi "Teknik Serangan MITRE ATT&CK" (deskripsi, bukan panduan tindakan), iterasi dilanjutkan ke iterasi 2 dengan `prefer_mitigations=True`. Ini memastikan output adalah langkah mitigasi aktual, bukan deskripsi ancaman.

**Recommendation assembly — Anti-hallucination:**

`general_guidance` dan `escalation_note` tidak lagi dimasukkan ke `recommendation_parts`. Kedua field ini tidak divalidasi sitasi, sehingga berpotensi halusinasi. Output rekomendasi kini hanya berisi step yang sudah lolos `_validate_citations()`.

---

### 22.2 `app/rag/retriever.py` — Parameter `prefer_mitigations` + Bug Fix

**Bug fix:** Panggilan `client.search()` diperbaiki: argument `query=` diganti menjadi `query_vector=` (nama argument yang benar untuk Qdrant Python client).

**Parameter baru `prefer_mitigations: bool = False`:**

Ketika `True`, retriever menambahkan filter konten `MatchText(text="Mitigasi MITRE ATT&CK")` ke query Qdrant sehingga hanya chunk yang berisi panduan mitigasi yang dikembalikan. Digunakan oleh `mitigation.py` pada iterasi ke-2.

---

### 22.3 `app/rag/embedder.py` — Tambahan Field Payload

`_build_payload()` kini menyimpan tiga field tambahan ke Qdrant payload:

| Field | Keterangan |
|-------|-----------|
| `object_type` | Tipe objek MITRE ATT&CK (`course-of-action`, `attack-pattern`); kosong untuk non-MITRE |
| `external_id` | ID eksternal MITRE (contoh: `M1049`, `T1566`); kosong untuk non-MITRE |
| `source` | Field sumber dokumen dari metadata chunk |

Ini memungkinkan `_validate_citations()` di `mitigation.py` mencocokkan referensi ke ID MITRE dengan benar.

---

### 22.4 `app/agents/notifier.py` — Hapus Hardcoded Fallback ID

Konstanta `_CSIRT_CHAT_ID_FALLBACK = "-1003971618295"` dihapus. `_get_csirt_recipients()` kini menggunakan `os.getenv(_CSIRT_CHAT_ID_ENV, "")` — jika env var tidak diset, tidak ada pesan Telegram yang dikirim (fail-safe, tidak kirim ke ID hardcoded yang mungkin salah di lingkungan lain).

---

### 22.5 `app/web/services/auth_service.py` — Perbaikan Disabled Account Enumeration

Sebelumnya, akun disabled dikembalikan sebagai `"account_disabled"` setelah pengecekan password berhasil — ini membocorkan informasi bahwa username dan password benar. Sekarang:

```python
# Sebelum: dua cek terpisah
if admin is None:
    bcrypt.verify(password, _DUMMY_HASH)  # timing defense
    ...
if not admin.is_active:
    return AuthResult(success=False, error="account_disabled")  # ← bocor info

# Sesudah: gabung di satu cek
if admin is None or not admin.is_active:
    bcrypt.verify(password, _DUMMY_HASH)  # timing defense untuk kedua kasus
    return AuthResult(success=False, error="invalid_credentials")
```

Attacker tidak bisa lagi membedakan "user tidak ada", "password salah", atau "akun dinonaktifkan" dari response maupun timing.

---

### 22.6 `app/web/services/chat_service.py` — Dua Perbaikan

**1. Clarification counter yang akurat:**

`clarification_rounds` sebelumnya menghitung semua pesan bot yang tidak diawali "Tiket insiden" — ini salah menghitung pesan error/timeout. Sekarang hanya menghitung entry dengan `type="clarification"` yang di-tag secara eksplisit saat pesan klarifikasi disimpan:

```python
msg_entry: dict = {"role": "assistant", "content": bot_text, "ts": ts}
if requires_clarification and not ticket_id:
    msg_entry["type"] = "clarification"
history.append(msg_entry)
```

**2. `_flush_pending_uploads()` — GET sebelum DELETE:**

Pola pipeline Redis (GET+DELETE atomic) diganti dengan GET dulu, DELETE hanya setelah `db.commit()` sukses. Ini mencegah kehilangan data upload jika commit database gagal di tengah jalan (bug_054).

---

### 22.7 `app/web/routes/pelapor.py` — Authorization Check Tiket

Endpoint `GET /lapor/tiket/{ticket_id}` sebelumnya tidak memverifikasi apakah pelapor yang sedang login adalah pemilik tiket. Sekarang:

```python
if ticket.reporter_id != reporter["reporter_id"]:
    raise HTTPException(status_code=403, detail="Akses ditolak.")
```

Ini mencegah IDOR (Insecure Direct Object Reference): pelapor A tidak bisa melihat tiket pelapor B hanya dengan menebak ticket_id.

Upload error response kini di-HTML-escape: `html.escape(str(exc))` mencegah XSS jika pesan error mengandung karakter HTML.

---

### 22.8 `config/prompts/mitigation.txt` — Prompt Rewrite

Prompt mitigasi ditulis ulang untuk meningkatkan groundedness (kesetiaan ke dokumen):

| Aspek | Sebelum | Sesudah |
|-------|---------|---------|
| Jumlah langkah max | 5 | 4 |
| Panjang per action | Tidak dibatasi | Maks 2 kalimat |
| Format citation | `"NIST SP 800-61, Bagian X"` | `"[1] Nama Dokumen, Bagian X"` (referensi nomor chunk) |
| `general_guidance` | Terisi LLM | Kosong (`""`) — tidak digunakan |
| `escalation_note` | Terisi LLM | Kosong (`""`) — tidak digunakan |
| Aturan grounding | "berdasarkan HANYA dokumen" | Eksplisit DILARANG menambah pengetahuan di luar dokumen |

---

### 22.9 `requirements.txt` — Tambahan Dependency Evaluasi

```
ragas>=0.2.0    # framework evaluasi RAG (RAGAS v2+ API)
datasets>=2.0.0 # HuggingFace datasets, dipakai ragas internaly
```

---

### 22.10 `tests/evaluation/eval_ragas.py` — Upgrade ke RAGAS v2 API

Script evaluasi ditulis ulang total menggunakan RAGAS v2+ API:

| Aspek | Sebelum | Sesudah |
|-------|---------|---------|
| Dataset format | `Dataset.from_list(ragas_rows)` | `EvaluationDataset(samples=[SingleTurnSample(...)])` |
| Field names | `question`, `answer`, `contexts` | `user_input`, `response`, `retrieved_contexts`, `reference` |
| LLM wrapper | `ChatOpenAI` | RAGAS native `LangchainLLMWrapper` |
| Metrics | Auto-detect | Eksplisit: `Faithfulness`, `AnswerRelevancy`, `ContextRelevancy` |
| Rate limiting | Tidak ada | `RunConfig(max_workers=1, max_retries=3, timeout=120)` |
| Argument baru | — | `--ids QA-004 QA-013` untuk jalankan subset soal |

---

### 22.11 File Baru di `tests/evaluation/`

| File | Keterangan |
|------|-----------|
| `generate_qa_from_kb.py` | Script untuk generate QA pairs langsung dari knowledge base Qdrant via LLM |
| `candidate_qa.json` | Dataset QA kandidat yang dihasilkan dari KB (belum final) |
| `candidate_ragas_results.json` | Hasil evaluasi RAGAS untuk dataset kandidat |
| `RAGAS_REPORT.md` | Laporan ringkas hasil evaluasi RAGAS untuk penulisan skripsi |

---

*Untuk detail arsitektur tingkat tinggi, lihat `docs/MASTERPLAN.md`. Untuk checklist fase implementasi, lihat `docs/PHASE_GUIDE.md`.*

---

## 23. Perubahan Terbaru (2026-06-06)

- Dokumentasi ini telah disinkronkan dengan keadaan kode pada `2026-06-06`.
- Perubahan: pembaruan timestamp, penyesuaian dokumentasi kecil agar konsisten dengan kode saat ini, dan penambahan catatan ringkas perubahan terbaru. Tidak ada perubahan struktur file atau API yang dilakukan di dokumen ini.

Jika Anda ingin saya menghasilkan ringkasan perubahan file-by-file (diff) berdasarkan kode pada workspace saat ini, beri tahu saya dan saya akan mengekstrak nama file yang berubah dan menambahkan ringkasan terperinci di sini.
