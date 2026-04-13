# Web Interface — Design Spec

**Tanggal**: 2026-04-13
**Topik**: Interface alternatif berbasis web untuk helpdesk Pusdatin (pelaporan pelapor + admin dashboard terpadu)
**Status**: Draft

## 1. Latar Belakang

Proyek saat ini punya dua interface terpisah: **Telegram bot** untuk pelapor dan **Streamlit dashboard** untuk admin. Spec ini mendesain interface ketiga berbasis web yang menggabungkan kedua peran dalam satu aplikasi FastAPI, sebagai alternatif yang dapat diakses tanpa Telegram dan lebih fleksibel untuk pengembangan UX.

**Tujuan**:
- Pelapor dapat melapor insiden via browser tanpa Telegram.
- Admin CSIRT punya dashboard terpadu dengan auth proper (bukan anon Streamlit).
- Reuse sepenuhnya pipeline LangGraph existing tanpa duplikasi logika.

**Non-tujuan**:
- Mengganti Telegram bot atau Streamlit dashboard.
- Mengubah `IncidentState` atau arsitektur agent.
- Menjadi produk production-grade (tetap prototipe skripsi D-IV/S-1).

## 2. Arsitektur

### 2.1 Pendekatan: Twin App (Single FastAPI)

Web UI ditambahkan ke FastAPI app yang sama (`app/main.py`) via route group baru di `app/web/`. Endpoint REST existing (`/api/v1/*`) tidak disentuh. Pipeline LangGraph dipanggil **in-process** via `helpdesk_graph.ainvoke()` — bukan HTTP self-call.

**Alasan**:
- LangGraph pipeline stateful, pemanggilan langsung lebih efisien.
- Single deployment unit, tidak perlu koordinasi multi-service.
- Dependency injection FastAPI bisa dipakai untuk DB session + graph.

### 2.2 Struktur Direktori

```
app/web/
├── __init__.py
├── app.py                       # create_web_router() + mount static
├── config.py                    # WebConfig (SESSION_SECRET, UPLOAD_DIR, dll)
├── dependencies.py              # get_current_admin(), get_reporter_session(), get_csrf_token()
├── middleware/
│   ├── session.py               # SessionMiddleware (signed, HttpOnly, Secure, SameSite=Lax, 8h)
│   ├── csrf.py                  # Double-submit cookie
│   ├── security_headers.py      # CSP, X-Frame-Options, nosniff, Referrer-Policy
│   └── rate_limit.py            # slowapi: login 5/min, chat 20/min, upload 10/min
├── routes/
│   ├── landing.py               # GET /
│   ├── pelapor.py               # /lapor/*
│   ├── admin_auth.py            # /admin/login, /admin/logout
│   ├── admin_inbox.py           # /admin/inbox, /admin/tiket/*
│   ├── admin_rag.py             # /admin/rag/*
│   └── admin_report.py          # /admin/report/*
├── services/
│   ├── chat_service.py          # Wraps helpdesk_graph + Redis chat history
│   ├── auth_service.py          # bcrypt via passlib, lockout counter
│   ├── upload_service.py        # python-magic MIME validation + UUID filename
│   ├── rag_service.py           # Wraps app/rag/ingestion
│   └── report_service.py        # Wraps app/dashboard/report_generator
├── forms/
│   ├── pelapor.py               # Pydantic form models
│   └── admin.py
├── templates/
│   ├── base.html                # Layout utama, Jinja autoescape ON
│   ├── _macros.html             # csrf_input(), badge(), dll
│   ├── landing.html
│   ├── pelapor/
│   │   ├── identitas.html
│   │   ├── chat.html
│   │   ├── _message.html
│   │   ├── _tiket_card.html
│   │   ├── _attachment_pill.html
│   │   └── _error_bubble.html
│   ├── admin/
│   │   ├── login.html
│   │   ├── inbox.html
│   │   ├── _tiket_row.html
│   │   ├── tiket_detail.html
│   │   ├── rag.html
│   │   └── report.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
└── static/
    ├── css/style.css
    ├── js/htmx.min.js           # vendored, tidak CDN
    └── img/

web_uploads/                     # DI LUAR static/, tidak auto-served
└── {YYYY-MM}/{uuid}.{ext}
```

### 2.3 Stack Pilihan

**FastAPI + Jinja2 + HTMX**:
- Single language (Python), tidak ada build pipeline JS.
- HTMX vendored di `static/js/htmx.min.js` — offline capable.
- Server-rendered HTML fragment untuk reaktivitas, request-response (bukan streaming token — pipeline batch).
- Cocok untuk UI chat + dashboard tanpa overhead SPA.

**Alasan tidak pakai React/Vue SPA**: double effort untuk solo skripsi, butuh JSON API terpisah + state management client-side yang tidak perlu untuk chat request-response + CRUD tabel.

### 2.4 Defense-in-Depth Keamanan

| Threat | Mitigasi |
|---|---|
| CSRF | Double-submit cookie + token hidden di form + validator middleware |
| Session hijack | Cookie HttpOnly, Secure, SameSite=Lax, signed via itsdangerous, TTL 8h |
| XSS | Jinja autoescape ON, CSP header, no `|safe` di user input |
| Clickjacking | `X-Frame-Options: DENY` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Brute force login | slowapi rate limit 5/min per IP + Redis lockout 15 menit setelah 5x gagal |
| Password compromise | bcrypt via passlib cost 12 |
| File upload malicious | Extension whitelist (PNG/JPG/PDF) + python-magic MIME validation (bukan `Content-Type`) + max 10 MB + UUID filename |
| Prompt injection | Reuse `app/security/prompt_injection.py` sebelum pipeline |
| PII leak ke LLM | Reuse `app/security/pii_redactor.py` |
| SQL injection | SQLAlchemy ORM, no raw SQL |
| Open redirect | Whitelist `next` param di login (hanya path internal) |
| Audit trail | Setiap admin action dicatat ke `audit_log` table |
| Secrets exposure | Hanya dari env vars (SESSION_SECRET, CSRF_SECRET, dll) |
| Fail-closed | Guardrails gagal → tolak request, jangan forward ke pipeline |

### 2.5 Developer Convenience

- Type hints wajib di services & dependencies
- Hot reload via `uvicorn --reload`
- Test pyramid: unit → integration (TestClient) → E2E opsional (Playwright)
- Dev flag `CSRF_STRICT=0` untuk bypass saat debugging (hanya di dev)
- Flash messages via session untuk feedback UX
- Semua template punya base layout konsisten

## 3. Data Model

### 3.1 Tabel Baru

**`admins`** (PostgreSQL via SQLAlchemy):

```python
class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
```

**`ticket_attachments`**:

```python
class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("incident_tickets.ticket_id"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(128), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
```

Migration Alembic baru: `xxxx_add_admins_and_attachments.py`.

### 3.2 Tabel Existing (Tidak Diubah)

- `incident_tickets` — tidak disentuh
- `audit_log` — reuse, tambahan event types baru (lihat Section 4.9)
- `IncidentState` (LangGraph) — **tidak diubah** (aturan CLAUDE.md)

### 3.3 Redis Keys Baru

| Key | TTL | Fungsi |
|---|---|---|
| `web:chat:{session_id}` | 24h (refresh per pesan) | List JSON message history pelapor |
| `web:pending_uploads:{session_id}` | 1h | List file metadata yang sudah diupload tapi belum ter-attach ke tiket |
| `admin:lockout:{username}` | 15 menit | Counter gagal login untuk lockout |
| `rag:job:{job_id}` | 1h | Status background job RAG ingest/reindex |

### 3.4 File Storage

- Upload disimpan di `web_uploads/{YYYY-MM}/{uuid}.{ext}`
- **Tidak** di-serve otomatis oleh `StaticFiles` — download via endpoint admin-gated
- Cleanup manual (prototipe skripsi, bukan production)

### 3.5 Seed Script

`scripts/seed_admin.py` — CLI tool untuk buat admin pertama (interactive prompt username/password).

## 4. Chat Flow Pelapor

### 4.1 Route Map

| Route | Method | Fungsi |
|---|---|---|
| `/` | GET | Landing page |
| `/lapor` | GET | Form identitas pelapor |
| `/lapor` | POST | Simpan identitas → set cookie → redirect `/lapor/chat` |
| `/lapor/chat` | GET | Halaman chat utama (render history Redis) |
| `/lapor/chat/message` | POST (HTMX) | Kirim pesan teks → panggil pipeline → return fragment `_message.html` |
| `/lapor/chat/upload` | POST (HTMX) | Upload file → return fragment attachment pill |
| `/lapor/chat/reset` | POST | Clear Redis history + reset cookie |
| `/lapor/tiket/{id}` | GET | Halaman status tiket (read-only untuk pelapor) |

### 4.2 Session Pelapor

Cookie `reporter_session` (signed, HttpOnly, 8h TTL):

```json
{
  "session_id": "uuid",
  "reporter_id": "web:<uuid>",
  "reporter_name": "...",
  "reporter_contact": "...",
  "reporter_unit": "..."
}
```

`reporter_id` diprefix `web:` agar beda namespace dari Telegram `tg:<chat_id>`. Ini penting untuk filter query tiket per channel.

### 4.3 Alur Pesan (Request-Response)

```
User submit pesan → POST /lapor/chat/message (HTMX)
  ↓
ChatService.handle_message():
  1. Load history dari Redis (web:chat:{session_id})
  2. Append user message → save Redis (TTL refresh 24h)
  3. Build IncidentState via orchestrator.initialize_state(...)
  4. Flush pending uploads dari Redis (lihat 4.5)
  5. await helpdesk_graph.ainvoke(state)
  6. Extract response:
     - Jika requires_clarification → tampilkan clarification_message
     - Jika ticket_id terbentuk → attach pending uploads ke tiket → tampilkan tiket card
  7. Append assistant message → save Redis
  ↓
Return HTML fragment: [user bubble] + [assistant bubble] (+ optional tiket card)
```

**Loading indicator**: HTMX `hx-indicator` — "Asisten sedang menganalisis..." (pipeline normal 5-15 detik).

**Timeout**: `asyncio.wait_for(graph.ainvoke(state), timeout=30)` → return error fragment dengan trace id `[{session_id[:8]}]`.

### 4.4 Clarification Loop

Pipeline dapat return `requires_clarification=True`. UI:
- Tampilkan `clarification_message` sebagai bubble asisten biasa
- User reply normal → POST berikutnya menggabung konteks

**Open question**: `initialize_state` saat ini menerima single `raw_input`. Untuk multi-turn, `ChatService` akan concat last 3 user messages jadi konteks input, ATAU extend `IncidentState` dengan field `conversation_history`. Keputusan ditunda ke fase implementasi karena menyentuh state schema.

### 4.5 File Upload Flow

1. User klik 📎 → trigger `<input type="file">` hidden
2. HTMX `hx-post="/lapor/chat/upload"`, `hx-encoding="multipart/form-data"`
3. `UploadService.save_pending()`:
   - Validasi extension whitelist (PNG/JPG/PDF)
   - Validasi MIME asli via `python-magic`
   - Max size 10 MB
   - Simpan ke `web_uploads/{YYYY-MM}/{uuid}.{ext}`
   - Simpan metadata ke Redis `web:pending_uploads:{session_id}` (list)
   - **Belum** insert ke `ticket_attachments` (tiket belum ada)
4. Return fragment `_attachment_pill.html`
5. Saat tiket ter-create di akhir pipeline, flush pending → insert rows `ticket_attachments`

**Alasan two-step**: tiket baru muncul setelah pipeline selesai. Upload dulu → attach saat tiket terbentuk.

**python-magic platform handling** (`requirements.txt`):
```
python-magic; platform_system != "Windows"
python-magic-bin; platform_system == "Windows"
```

### 4.6 Template Fragments HTMX

```
templates/pelapor/
├── chat.html              # Halaman full (extends base.html)
├── _message.html          # Satu bubble (user/assistant)
├── _tiket_card.html       # Card ringkasan tiket
├── _attachment_pill.html  # Pill file terupload
└── _error_bubble.html     # Error state
```

Pattern: POST HTMX return fragment kecil. Full page hanya di GET `/lapor/chat`.

### 4.7 Rate Limit

slowapi per session_id:
- `/lapor/chat/message`: 20/menit
- `/lapor/chat/upload`: 10/menit
- Response 429 → HTMX bubble warning "Terlalu banyak pesan, tunggu sebentar"

### 4.8 Privacy

- Redis history auto-expire 24h
- Tombol "Mulai sesi baru" → clear Redis + reset cookie
- Nama/kontak tidak pernah masuk application log (hanya `session_id[:8]` sebagai trace id)
- PII redaction tetap jalan di pipeline (reuse `app/security/pii_redactor.py`)

## 5. Admin Flow

### 5.1 Route Map

| Route | Method | Auth | Fungsi |
|---|---|---|---|
| `/admin/login` | GET | public | Form login |
| `/admin/login` | POST | public | Verifikasi bcrypt → set cookie `admin_session` |
| `/admin/logout` | POST | admin | Clear cookie + audit log |
| `/admin/inbox` | GET | admin | Daftar tiket (filter status/severity/search) |
| `/admin/inbox/table` | GET (HTMX) | admin | Fragment tabel untuk filter/pagination |
| `/admin/tiket/{id}` | GET | admin | Detail tiket + attachments + timeline |
| `/admin/tiket/{id}/status` | POST (HTMX) | admin | Update status |
| `/admin/tiket/{id}/assign` | POST (HTMX) | admin | Assign ke admin lain |
| `/admin/tiket/{id}/escalation` | POST (HTMX) | admin | Update escalation level |
| `/admin/tiket/{id}/notify` | POST (HTMX) | admin | Kirim notifikasi Telegram ke pelapor |
| `/admin/tiket/{id}/attachment/{att_id}` | GET | admin | Download file (streaming, Content-Disposition) |
| `/admin/rag` | GET | admin | Dashboard knowledge base |
| `/admin/rag/upload` | POST | admin | Upload dokumen KB → trigger ingest background |
| `/admin/rag/reindex` | POST | admin | Reindex Qdrant collection |
| `/admin/report` | GET | admin | Halaman laporan |
| `/admin/report/generate` | POST | admin | Generate PDF/CSV |

### 5.2 Auth Flow

```
POST /admin/login {username, password, csrf_token}
  ↓
AuthService.authenticate():
  1. Ambil Admin by username (case-insensitive)
  2. passlib.verify(password, password_hash) — bcrypt cost 12
  3. Jika gagal: audit ADMIN_LOGIN_FAILED, sleep 100ms (anti-timing), return 401
  4. Jika sukses: update last_login_at, audit ADMIN_LOGIN
  5. Set cookie admin_session (signed, HttpOnly, Secure, SameSite=Lax, 8h)
     payload: {admin_id, username, issued_at, csrf_token}
  ↓
Redirect 303 → /admin/inbox (atau next param jika valid path internal)
```

**Rate limit**: 5/menit per IP. Setelah 5x gagal dalam 15 menit → lockout 15 menit via `admin:lockout:{username}`.

**Dependency `get_current_admin()`**:
- Baca cookie → verify signature → load Admin row → check `is_active`
- Invalid → redirect `/admin/login?next={current_path}` (whitelist path internal)
- Tidak aktif → clear cookie + redirect

### 5.3 Inbox UX

- **Filter bar** (HTMX): status, severity, search, date range
- **Tabel**: ticket_id, created_at, reporter_name, incident_type, severity, status, assigned_to
- **Pagination**: 25 per halaman
- Klik baris → navigasi full page `/admin/tiket/{id}`
- Filter via `hx-get="/admin/inbox/table"` `hx-trigger="change"` — hanya tabel re-render

### 5.4 Tiket Detail Page

Layout 2 kolom:

**Kiri (info)**:
- Header: ticket_id, created_at, status badge
- Reporter info (nama, kontak, unit, channel prefix)
- Incident: type, severity, confidence, escalation
- Raw input (collapsible)
- Mitigation recommendation (rendered)
- Citations RAG (source + section)
- Attachments list → tombol download

**Kanan (actions + timeline)**:
- Form update status (dropdown + HTMX inline)
- Form assign
- Form escalation level
- Tombol "Kirim notifikasi ke pelapor"
- Timeline audit log (filter `ticket_id`)

Setiap action HTMX: `hx-post` → server update DB → return fragment row timeline baru + swap badge.

### 5.5 Notifikasi Pelapor

| Prefix | Notifikasi |
|---|---|
| `tg:` | Reuse `_notify_reporter_status()` existing — kirim via Telegram Bot API |
| `web:` | Tidak bisa push (web tidak persistent). Status terbaru tampil saat pelapor buka `/lapor/tiket/{id}`. Email notification = future work. |

### 5.6 RAG Management

Reuse logika dari `app/dashboard/rag_manager.py` dan `rag_client.py` → pindah ke `app/web/services/rag_service.py`:
- List collection + jumlah chunks
- Upload PDF → validasi → simpan ke `knowledge_base/documents/` → trigger ingest
- Reindex: `ingestion.ingest_all(force=True)`
- Delete collection (konfirmasi ganda)

**Async background**: FastAPI `BackgroundTasks` untuk ingest/reindex. UI return "sedang diproses", status tracking via Redis `rag:job:{job_id}`. User refresh untuk lihat progress.

### 5.7 Report Generation

Reuse `app/dashboard/report_generator.py` → wrap di `ReportService`:
- Form: rentang tanggal + format (PDF/CSV)
- POST → generate → return file response langsung (streaming)
- Tidak simpan file permanen di disk (simplifikasi, tidak perlu cleanup cron)

### 5.8 CSRF Admin Actions

Semua POST/PATCH/DELETE admin butuh CSRF token (double-submit cookie):
- Token generate saat login, simpan di cookie `csrf_token` (readable) + session cookie (signed)
- HTMX auto-include via `hx-headers` dari meta tag di base template
- Middleware verify: header token == session token, mismatch → 403

### 5.9 Audit Log Events (Baru)

Extend `app/utils/audit.py`:

- `ADMIN_LOGIN` / `ADMIN_LOGIN_FAILED` / `ADMIN_LOGOUT`
- `TICKET_STATUS_UPDATED` (admin_id, old→new)
- `TICKET_ASSIGNED`
- `TICKET_ESCALATION_UPDATED`
- `NOTIFICATION_SENT` (channel: telegram/web)
- `FILE_UPLOADED` / `FILE_DOWNLOADED`
- `RAG_INGEST_STARTED` / `RAG_REINDEX_COMPLETED`
- `REPORT_GENERATED`

Entry: `admin_id`, `ticket_id` (jika relevan), `ip_address`, `timestamp`, `details` (JSON).

## 6. Visual Design

### 6.1 Tema

**Modern Minimalist Biru**:
- Primary: `#2563eb` (blue-600)
- Sidebar gelap: `#0f172a` (slate-900)
- Background: `#f8fafc` (slate-50)
- Teks utama: `#0f172a`
- Teks sekunder: `#64748b` (slate-500)
- Border: `#e5e7eb` (gray-200)
- Font: system sans-serif (`-apple-system, Segoe UI, Inter, sans-serif`)

### 6.2 Layout Konsisten

Semua halaman pakai **sidebar kiri gelap + main area**:

**Landing (anonymous)**:
- Sidebar: logo + statistik publik (total tiket, insiden minggu ini, resolution rate)
- Main: judul + 2 CTA (Lapor Insiden / Admin Login)

**Chat Pelapor**:
- Sidebar: info sesi pelapor (nama, unit, kontak) + statistik + tombol reset
- Main: header, chat log (bubble user biru, bubble bot putih), input bar dengan attach

**Admin (Inbox, Detail, RAG, Report)**:
- Sidebar: logo, nav items (Inbox/Tiket/KB/Laporan/Audit), admin card
- Main: topbar dengan breadcrumb + logout, konten spesifik halaman

### 6.3 Komponen

- **Badge severity**: HIGH merah, MEDIUM kuning, LOW hijau
- **Badge status**: PENDING biru, IN PROGRESS ungu, RESOLVED hijau
- **KPI card**: background putih, border tipis, label uppercase kecil, value besar bold
- **Button primary**: biru `#2563eb`, teks putih, radius 6px
- **Button outline**: transparan, border biru, teks biru
- **Bubble chat**: user alignself-end biru, bot align-self-start putih dengan border

### 6.4 Aksesibilitas

- Keyboard navigation (tab order logis)
- Contrast ratio minimum AA
- Label `for` di semua form input
- Responsive minimum 1366x768 (laptop Pusdatin umum)

## 7. Error Handling & Testing

### 7.1 Error Handling per Layer

| Layer | Error | Perilaku |
|---|---|---|
| Route | Validation Pydantic gagal | 422 fragment HTMX dengan pesan field |
| Route | CSRF mismatch | 403 + redirect sumber + flash error |
| Route | Session invalid/expired | Redirect ke login/lapor |
| Route | Rate limit 429 | Fragment bubble warning |
| ChatService | Pipeline exception | Log trace id → `_error_bubble.html` generik |
| ChatService | Timeout > 30s | `asyncio.wait_for` → error bubble |
| UploadService | MIME tidak valid | Fragment pesan "Format tidak didukung" |
| UploadService | Size > 10 MB | Fragment pesan "File terlalu besar" |
| AuthService | Password salah | Sleep 100ms → audit → pesan generik |
| AuthService | Account locked | "Akun terkunci sementara" |
| RAG background | Ingest gagal | Update Redis `rag:job:{id}` status=failed |
| Middleware | Unhandled 500 | `errors/500.html` dengan trace id, log full stack |

### 7.2 Prinsip

- **Fail-closed keamanan** (reuse logika existing)
- **Graceful degradation UI** — error per fragment, jangan crash full page
- **Trace ID** di semua error user-facing
- **No secrets in error message** — detail hanya di log
- **Audit trail** untuk setiap error auth/admin action

### 7.3 Testing Strategy

**Unit** (`tests/test_web/test_services/`):
- `test_chat_service.py` — mock `helpdesk_graph`, test Redis history save/load
- `test_auth_service.py` — bcrypt verify, lockout counter, timing-safe compare
- `test_upload_service.py` — MIME validation dengan real files fixture
- `test_rag_service.py` — mock ingestion
- `test_report_service.py` — wrapper logic

**Integration** (`tests/test_web/test_routes/`, via `fastapi.testclient.TestClient`):
- `test_pelapor_routes.py`: GET `/lapor/chat` redirect unauth, POST message dengan mock pipeline, upload invalid → 422, rate limit → 429
- `test_admin_routes.py`: login sukses/gagal, lockout setelah 5x, akses inbox tanpa auth → redirect, CSRF mismatch → 403, update status → DB + audit

**E2E opsional** (`tests/test_web/test_e2e/` via Playwright):
- Login admin → buka tiket → update status → verify inbox
- Pelapor chat → deteksi ransomware → tiket muncul di admin
- Jalankan on-demand, bukan CI utama

**Manual checklist**:
- Visual regression per halaman
- HTMX swap tanpa flicker
- Responsive 1366x768
- Keyboard navigation

### 7.4 Coverage Target

| Module | Target |
|---|---|
| `app/web/services/` | ≥ 80% |
| `app/web/routes/` | ≥ 70% |
| `app/web/middleware/` | ≥ 90% (kritis keamanan) |
| Templates | Visual check manual |

### 7.5 Fixtures & Mocks

- **Mock LLM**: reuse pattern dari `tests/test_agents/`
- **Mock Redis**: `fakeredis` library untuk unit test
- **Test DB**: SQLite in-memory per test atau PostgreSQL test instance via fixture scope
- **Fixture admin user**: seed di `conftest.py` dengan known password
- **File fixtures**: `tests/fixtures/files/` sample PNG/JPG/PDF valid + invalid (misal PDF yang sebenarnya script)

## 8. Open Questions

1. **Multi-turn clarification**: extend `IncidentState.conversation_history` atau concat history di `ChatService`? Menyentuh aturan CLAUDE.md — diskusi di fase implementasi.
2. **Report file storage**: streaming langsung atau simpan sementara? Keputusan: streaming langsung untuk simplifikasi.
3. **E2E test**: Playwright wajib atau opsional? Keputusan: opsional, manual test cukup untuk skripsi.
4. **Email notification** untuk pelapor web: future work, tidak di MVP.

## 9. Dependencies Baru

```
passlib[bcrypt]              # password hashing
itsdangerous                 # signed cookies (bawaan Starlette, eksplisit)
slowapi                      # rate limiting
python-multipart             # form upload (bawaan FastAPI, eksplisit)
python-magic; platform_system != "Windows"
python-magic-bin; platform_system == "Windows"
fakeredis                    # test only
playwright                   # test only, opsional
```

## 10. Deployment Notes

- Env vars baru: `SESSION_SECRET`, `CSRF_SECRET`, `UPLOAD_DIR` (default `./web_uploads`)
- Docker: update `app` service command tidak berubah — web router sudah built-in di `app.main`
- Volume mount baru untuk `web_uploads/` di docker-compose
- Tambah `.superpowers/` dan `web_uploads/` ke `.gitignore`

## 11. Estimasi Effort

~2-3 minggu kerja solo developer (skala prototipe skripsi):
- Week 1: Auth + session + middleware + admin CRUD dasar
- Week 2: Chat pelapor + upload + integrasi pipeline + HTMX fragments
- Week 3: RAG management + report + polish visual + testing

---

**Next step**: Invoke `writing-plans` skill untuk membuat implementation plan detail yang dapat dieksekusi step-by-step.
