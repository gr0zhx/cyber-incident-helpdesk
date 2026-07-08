# Panduan Fase Implementasi & Checkpoint
## Sistem Helpdesk Keamanan Siber Multi-Agent

**Tujuan Dokumen:** Panduan langkah demi langkah untuk membangun sistem secara bertahap. Setiap fase adalah **checkpoint** yang berdiri sendiri — bisa di-*resume* di sesi editor baru.

**Cara Penggunaan:**
1. Buka sesi kerja baru
2. Berikan konteks: *"Saya sedang mengerjakan Fase X dari proyek helpdesk keamanan siber multi-agent. Berikut dokumen fase-fasenya: [paste bagian fase yang relevan]. Status saat ini: [selesai/belum dari checklist]."*
3. Kerjakan sampai semua checklist fase tersebut ✅
4. Commit & push sebelum tutup sesi
5. Lanjut ke fase berikutnya di sesi baru

---

## Ringkasan Fase

| Fase | Nama | Estimasi | Dependensi |
|------|------|----------|------------|
| 0 | Persiapan Lingkungan & Struktur Proyek | 1–2 hari | — |
| 1 | Database & Model Data | 1–2 hari | Fase 0 |
| 2 | Pipeline RAG (Ingesti & Retrieval) | 3–4 hari | Fase 1 |
| 3 | Agen Tunggal: Identificator Insiden | 2–3 hari | Fase 1 |
| 4 | Agen Tunggal: Mitigation Advisor + RAG | 3–4 hari | Fase 2, 3 |
| 5 | Agen Ticket Manager & Notifier | 2–3 hari | Fase 1, 4 |
| 6 | Orchestrator & Graf LangGraph | 3–4 hari | Fase 3, 4, 5 |
| 7 | Lapisan Keamanan (Guardrails) | 2–3 hari | Fase 6 |
| 8 | Integrasi Bot Telegram | 2–3 hari | Fase 6, 7 |
| 9 | Integrasi End-to-End & Docker | 2–3 hari | Fase 8 |
| 10 | Evaluasi & Pengujian | 3–5 hari | Fase 9 |

**Total Estimasi: 24–36 hari kerja**

---

## FASE 0: Persiapan Lingkungan & Struktur Proyek

### Tujuan
Menyiapkan seluruh fondasi proyek — environment, struktur folder, konfigurasi, dan dependensi — agar semua fase selanjutnya bisa langsung koding tanpa setup ulang.

### Yang Harus Dikerjakan

**0.1 — Inisialisasi Repositori**
- Buat repositori Git
- Buat `.gitignore` untuk Python (termasuk `.env`, `__pycache__/`, `*.pyc`, `.venv/`, `data/`)
- Buat `README.md` dengan deskripsi proyek

**0.2 — Struktur Folder**
Buat struktur folder berikut:
```
cybersec-helpdesk/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point FastAPI (kosong dulu)
│   ├── config.py                # Konfigurasi dari env vars
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── identifier.py
│   │   ├── mitigation.py
│   │   ├── ticket_manager.py
│   │   ├── notifier.py
│   │   ├── graph.py             # Definisi LangGraph
│   │   └── state.py             # IncidentState TypedDict
│   ├── security/
│   │   ├── __init__.py
│   │   ├── guardrails.py
│   │   ├── sanitizer.py
│   │   ├── validator.py
│   │   ├── pii_redactor.py
│   │   └── prompt_injection.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── connection.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   └── templates.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── audit.py
├── knowledge_base/
│   ├── documents/               # Taruh PDF/DOCX sumber di sini
│   └── metadata/
├── config/
│   ├── prompts/                 # Template prompt setiap agen
│   │   ├── orchestrator.txt
│   │   ├── identifier.txt
│   │   └── mitigation.txt
│   └── guardrails/              # Konfigurasi NeMo (nanti Fase 7)
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_security/
│   ├── test_rag/
│   └── evaluation/
│       └── scenarios.json       # Skenario evaluasi
├── scripts/
│   └── ingest_knowledge.py      # Script ingesti dokumen (nanti Fase 2)
├── .env.example
├── .gitignore
├── docker-compose.yml           # Kerangka awal
├── Dockerfile                   # Kerangka awal
├── requirements.txt
└── README.md
```

**0.3 — Dependencies (requirements.txt)**
```
# Core
fastapi==0.115.*
uvicorn==0.34.*
python-dotenv==1.1.*

# LLM & Agents
langchain==0.3.*
langgraph==0.3.*
langchain-openai==0.3.*
openai==1.76.*

# Vector DB
qdrant-client==1.13.*

# Database
sqlalchemy==2.0.*
psycopg2-binary==2.9.*
alembic==1.15.*

# Telegram
python-telegram-bot==21.*

# RAG
pypdf==5.*
langchain-text-splitters==0.3.*

# Security
# nemo-guardrails==0.11.*  # Aktifkan di Fase 7

# Utilities
pydantic==2.11.*
redis==5.3.*
structlog==25.*

# Testing
pytest==8.*
pytest-asyncio==0.26.*
```

**0.4 — Konfigurasi (app/config.py)**
Buat file konfigurasi yang membaca dari environment variables:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: "gpt-4o")
- `EMBEDDING_MODEL` (default: "text-embedding-3-small")
- `DATABASE_URL` (default: "postgresql://USER:PASSWORD@HOST:5432/DBNAME")
- `REDIS_URL` (default: "redis://localhost:6379")
- `QDRANT_URL` (default: "http://localhost:6333")
- `TELEGRAM_BOT_TOKEN`
- `CSIRT_CHAT_ID` (ID grup Telegram CSIRT)
- `LOG_LEVEL` (default: "INFO")

**0.5 — IncidentState (app/agents/state.py)**
Definisikan `IncidentState` sebagai `TypedDict` sesuai masterplan:
```python
from typing import TypedDict, Optional

class IncidentState(TypedDict):
    raw_input: str
    sanitized_input: str
    reporter_id: str
    reporter_name: str
    reporter_contact: str
    timestamp_received: str
    session_id: str
    intent: str
    requires_clarification: bool
    clarification_message: str
    incident_type: str
    severity: str
    confidence_score: float
    classification_reasoning: str
    retrieved_chunks: list[dict]
    mitigation_recommendation: str
    citations: list[dict]
    rag_confidence: float
    ticket_id: str
    ticket_status: str
    escalation_level: str
    notification_sent: bool
    notification_recipients: list[str]
    notification_timestamp: str
    processing_errors: list[str]
    agent_trace: list[dict]
```

**0.6 — Docker Compose Kerangka Awal**
Buat `docker-compose.yml` minimal dengan servis: `db` (PostgreSQL 16), `redis` (Redis 7 Alpine), `qdrant` (latest).
Belum perlu servis `api` dan `telegram-bot` dulu.

**0.7 — File .env.example**
Buat template semua env vars yang dibutuhkan.

### Kriteria Selesai (Checklist)
```
[ ] Repositori Git sudah terinisialisasi
[ ] Struktur folder lengkap dengan semua __init__.py
[ ] requirements.txt sudah lengkap dan bisa di-pip install
[ ] app/config.py bisa membaca semua env vars
[ ] app/agents/state.py berisi IncidentState TypedDict lengkap
[ ] docker-compose.yml bisa docker compose up (PostgreSQL, Redis, Qdrant jalan)
[ ] .env.example sudah ada dengan semua variabel
[ ] FastAPI app bisa jalan (uvicorn app.main:app) meskipun hanya return {"status": "ok"}
[ ] Semua file sudah di-commit ke Git
```

### Cara Verifikasi
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Jalankan infrastruktur
docker compose up -d

# 3. Cek servis
docker compose ps  # Semua harus "running"

# 4. Jalankan FastAPI
uvicorn app.main:app --reload
# Buka http://localhost:8000 → harus return {"status": "ok"}

# 5. Cek Qdrant
curl http://localhost:6333/collections  # Harus return JSON
```

### Konteks untuk Sesi Berikutnya
> "Fase 0 sudah selesai. Struktur proyek, config, IncidentState, dan Docker Compose sudah siap. Infrastruktur (PostgreSQL, Redis, Qdrant) bisa dijalankan. Sekarang lanjut ke Fase 1: Database & Model Data."

---

## FASE 1: Database & Model Data

### Tujuan
Membangun skema database untuk tiket insiden dan audit log, termasuk model SQLAlchemy, migrasi Alembic, dan operasi CRUD dasar.

### Yang Harus Dikerjakan

**1.1 — Model SQLAlchemy (app/database/models.py)**
Implementasikan model berdasarkan skema di masterplan:
- `IncidentTicket` — seluruh field sesuai skema SQL di Bagian 9.1 masterplan
- `AuditLog` — seluruh field sesuai skema SQL di Bagian 9.3 masterplan
- Pastikan menggunakan `JSONB` untuk field `evidence_files`, `evidence_urls`, `citations`, `agent_trace`, `metadata`

**1.2 — Koneksi Database (app/database/connection.py)**
- Buat `async_engine` dan `async_session` menggunakan SQLAlchemy async
- Atau gunakan synchronous jika lebih simpel untuk prototipe
- Fungsi `get_db()` sebagai dependency injection untuk FastAPI

**1.3 — Migrasi Alembic**
```bash
alembic init app/database/migrations
```
- Konfigurasi `alembic.ini` agar membaca `DATABASE_URL` dari env
- Buat migrasi awal: `alembic revision --autogenerate -m "initial tables"`
- Jalankan migrasi: `alembic upgrade head`

**1.4 — Repository / CRUD (app/database/repository.py)**
Implementasikan fungsi-fungsi dasar:
```python
class TicketRepository:
    def create_ticket(self, ticket_data: dict) -> IncidentTicket
    def get_ticket_by_id(self, ticket_id: str) -> Optional[IncidentTicket]
    def get_tickets_by_reporter(self, reporter_id: str) -> list[IncidentTicket]
    def update_ticket_status(self, ticket_id: str, status: str) -> IncidentTicket
    def check_duplicate(self, reporter_id: str, description: str, hours: int = 24) -> Optional[IncidentTicket]

class AuditRepository:
    def log_event(self, event_data: dict) -> AuditLog
    def get_events_by_session(self, session_id: str) -> list[AuditLog]
```

**1.5 — Generator Ticket ID**
Buat fungsi `generate_ticket_id()` yang menghasilkan format `TICKET-YYYY-NNNN`:
- Tahun dari timestamp saat ini
- Nomor urut auto-increment per tahun (ambil dari database)

**1.6 — Unit Test Dasar**
```python
# tests/test_database/test_repository.py
def test_create_ticket()
def test_get_ticket_by_id()
def test_generate_ticket_id_format()
def test_check_duplicate()
```

### Kriteria Selesai (Checklist)
```
[ ] Model SQLAlchemy IncidentTicket dengan semua field dari masterplan
[ ] Model SQLAlchemy AuditLog dengan semua field dari masterplan
[ ] Migrasi Alembic berhasil dijalankan, tabel terbuat di PostgreSQL
[ ] TicketRepository bisa create, read, update tiket
[ ] AuditRepository bisa log dan read event
[ ] generate_ticket_id() menghasilkan format TICKET-YYYY-NNNN yang benar
[ ] check_duplicate() berfungsi dengan benar
[ ] Unit test semuanya pass
[ ] Commit ke Git
```

### Cara Verifikasi
```bash
# Jalankan migrasi
alembic upgrade head

# Verifikasi tabel
docker compose exec db psql -U postgres -d helpdesk -c "\dt"
# Harus muncul: incident_tickets, audit_logs

# Jalankan test
pytest tests/test_database/ -v
```

### Konteks untuk Sesi Berikutnya
> "Fase 0 dan 1 sudah selesai. Database PostgreSQL siap dengan tabel incident_tickets dan audit_logs. Model SQLAlchemy dan repository CRUD sudah berfungsi. Lanjut ke Fase 2: Pipeline RAG."

---

## FASE 2: Pipeline RAG (Ingesti & Retrieval)

### Tujuan
Membangun pipeline lengkap dari ingesti dokumen (NIST, MITRE ATT&CK) → chunking → embedding → penyimpanan di Qdrant → retrieval hybrid (semantik + keyword) → re-ranking.

### Yang Harus Dikerjakan

**2.1 — Persiapan Dokumen Pengetahuan**
- Taruh file PDF NIST SP 800-61 dan dokumen MITRE ATT&CK di `knowledge_base/documents/`
- Buat file metadata JSON untuk setiap dokumen di `knowledge_base/metadata/`:
```json
{
  "doc_id": "nist-800-61-rev2",
  "doc_title": "Computer Security Incident Handling Guide",
  "source_framework": "NIST",
  "version": "Rev. 2",
  "language": "en",
  "incident_types": ["phishing", "malware", "ransomware", "general"]
}
```

**2.2 — Ingesti Dokumen (app/rag/ingestion.py)**
- Baca PDF menggunakan `pypdf` atau `langchain.document_loaders.PyPDFLoader`
- Ekstrak teks per halaman
- Gabungkan metadata (doc_id, source_framework, page_number) ke setiap halaman

**2.3 — Chunking (app/rag/chunker.py)**
- Implementasikan `RecursiveCharacterTextSplitter` dari LangChain:
  - `chunk_size`: 800 (token)
  - `chunk_overlap`: 100
  - `separators`: ["\n\n", "\n", ". ", " "]
- Setiap chunk menyimpan metadata: `doc_id`, `doc_title`, `section_header` (jika bisa dideteksi), `page_number`, `source_framework`, `chunk_index`

**2.4 — Embedding (app/rag/embedder.py)**
- Gunakan `OpenAIEmbeddings(model="text-embedding-3-small")`
- Fungsi `embed_chunks(chunks: list[Document]) -> list[list[float]]`
- Implementasikan batching (100 chunk per batch) untuk menghormati rate limit

**2.5 — Penyimpanan ke Qdrant**
- Buat collection `cybersecurity_knowledge` di Qdrant:
  - Vector size: 1536
  - Distance: Cosine
- Simpan chunk beserta metadata sebagai payload
- Filter metadata yang didukung: `source_framework`, `incident_type`, `language`

**2.6 — Script Ingesti (scripts/ingest_knowledge.py)**
Buat script CLI yang menjalankan seluruh pipeline:
```bash
python scripts/ingest_knowledge.py --docs-dir knowledge_base/documents/ --metadata-dir knowledge_base/metadata/
```
Output yang diharapkan:
```
Membaca 3 dokumen...
Chunking: 450 chunks dihasilkan
Embedding: 450 chunks di-embed
Upload ke Qdrant: 450 chunks tersimpan
Selesai!
```

**2.7 — Retriever Hybrid (app/rag/retriever.py)**
Implementasikan kelas `HybridRetriever`:
```python
class HybridRetriever:
    def __init__(self, qdrant_client, embedder):
        ...

    def retrieve(self, query: str, incident_type: str = None, top_k: int = 20) -> list[dict]:
        # 1. Semantic search (Qdrant vector search)
        # 2. Keyword search (BM25 atau Qdrant keyword filter)
        # 3. Reciprocal Rank Fusion (RRF) untuk merge hasil
        # 4. Filter metadata berdasarkan incident_type jika ada
        # Return: list of {content, metadata, score}
```

**2.8 — Re-Ranker (app/rag/reranker.py)**
- Untuk prototipe, gunakan re-ranking sederhana: LLM-based scoring atau cross-encoder ringan
- Jika resource terbatas, skip cross-encoder dan gunakan threshold skor dari retriever saja
- Fungsi `rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]`

**2.9 — Unit Test RAG**
```python
# tests/test_rag/test_retriever.py
def test_semantic_search_returns_results()
def test_hybrid_retrieval_merges_results()
def test_metadata_filter_by_incident_type()
def test_reranker_reduces_to_top_k()
```

### Kriteria Selesai (Checklist)
```
[ ] Minimal 1 dokumen (NIST SP 800-61) berhasil di-ingest
[ ] Chunking menghasilkan chunk dengan metadata yang benar
[ ] Embedding berhasil dijalankan dan chunk tersimpan di Qdrant
[ ] Script ingest_knowledge.py berjalan end-to-end tanpa error
[ ] Qdrant collection berisi chunk yang bisa di-query
[ ] HybridRetriever mengembalikan hasil yang relevan untuk query test
[ ] Re-ranker berfungsi (atau threshold-based filtering)
[ ] Unit test pass
[ ] Commit ke Git
```

### Cara Verifikasi
```bash
# Jalankan ingesti
python scripts/ingest_knowledge.py --docs-dir knowledge_base/documents/

# Cek collection di Qdrant
curl http://localhost:6333/collections/cybersecurity_knowledge
# Harus menunjukkan jumlah points > 0

# Test retrieval manual di Python shell
from app.rag.retriever import HybridRetriever
retriever = HybridRetriever(...)
results = retriever.retrieve("langkah mitigasi phishing email")
print(len(results), results[0]['content'][:200])
```

### Konteks untuk Sesi Berikutnya
> "Fase 0, 1, 2 sudah selesai. Database siap, pipeline RAG lengkap — dokumen NIST sudah di-ingest ke Qdrant, retriever hybrid berfungsi. Lanjut ke Fase 3: Agen Identificator Insiden."

---

## FASE 3: Agen Tunggal — Identificator Insiden

### Tujuan
Membangun agen pertama yang berdiri sendiri: agen yang menerima teks laporan insiden dan mengklasifikasikan jenis insiden + tingkat keparahan menggunakan few-shot prompting.

### Yang Harus Dikerjakan

**3.1 — Template Prompt (config/prompts/identifier.txt)**
Tulis prompt few-shot dengan:
- System prompt yang menjelaskan peran agen
- 8 contoh (satu per jenis insiden) dalam format input → output JSON
- Instruksi output JSON yang ketat:
```json
{
  "incident_type": "Phishing",
  "severity": "Tinggi",
  "confidence_score": 0.92,
  "reasoning": "Laporan menyebutkan email palsu yang mengaku CEO dengan link login palsu, tipikal spear phishing."
}
```

**3.2 — Implementasi Agen (app/agents/identifier.py)**
```python
class IncidentIdentifierAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.prompt_template = self._load_prompt()
        self.valid_types = [
            "Phishing", "Malware", "Ransomware", "Web Defacement",
            "DDoS", "Akses Tidak Sah", "Kebocoran Data", "Lainnya"
        ]
        self.valid_severities = [
            "Kritis", "Tinggi", "Sedang", "Rendah", "Informasional"
        ]

    async def classify(self, sanitized_input: str) -> dict:
        # 1. Format prompt dengan input
        # 2. Panggil LLM
        # 3. Parse JSON response
        # 4. Validasi: incident_type harus dari valid_types
        # 5. Validasi: severity harus dari valid_severities
        # 6. Jika confidence < 0.7, set flag review
        # 7. Return dict yang siap dimasukkan ke IncidentState
```

**3.3 — Penanganan Error**
- Jika LLM mengembalikan format non-JSON → coba parse ulang, jika gagal → default "Lainnya" + "Sedang"
- Jika LLM timeout → retry 1x, jika gagal lagi → default + flag error
- Jika incident_type tidak valid → fallback ke "Lainnya"

**3.4 — Unit Test Identificator**
```python
# tests/test_agents/test_identifier.py
def test_classify_phishing_report()         # Input jelas → Phishing
def test_classify_ransomware_report()       # Input jelas → Ransomware
def test_classify_ambiguous_report()        # Input ambigu → confidence rendah
def test_classify_invalid_llm_response()    # Mock LLM error → fallback
def test_valid_types_enforced()             # Tipe di luar daftar → "Lainnya"
```

**3.5 — Test Manual Interaktif**
Buat script kecil `scripts/test_identifier.py` yang bisa dijalankan dari terminal:
```bash
python scripts/test_identifier.py "Saya menerima email dari CEO meminta transfer dana"
# Output: {"incident_type": "Phishing", "severity": "Tinggi", "confidence_score": 0.91, ...}
```

### Kriteria Selesai (Checklist)
```
[ ] Template prompt few-shot tersimpan di config/prompts/identifier.txt
[ ] IncidentIdentifierAgent bisa menerima teks dan mengembalikan klasifikasi JSON
[ ] Validasi jenis insiden dan severity berfungsi (hanya dari daftar yang valid)
[ ] Handling error untuk format non-JSON, timeout, dan tipe tidak valid
[ ] Flag review otomatis jika confidence < 0.7
[ ] Unit test pass untuk semua skenario
[ ] Script test manual berjalan dengan benar
[ ] Commit ke Git
```

### Cara Verifikasi
```bash
# Unit test
pytest tests/test_agents/test_identifier.py -v

# Test manual
python scripts/test_identifier.py "Komputer saya lambat dan ada popup minta bayar Bitcoin"
# Expected: Ransomware, Kritis

python scripts/test_identifier.py "Ada yang aneh"
# Expected: confidence rendah, flag review
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–3 sudah selesai. Agen Identificator Insiden berfungsi standalone — bisa klasifikasi 8 jenis insiden + severity dengan few-shot prompting. Lanjut ke Fase 4: Agen Mitigation Advisor + integrasi RAG."

---

## FASE 4: Agen Tunggal — Mitigation Advisor + RAG

### Tujuan
Membangun agen kedua yang menggunakan pipeline RAG dari Fase 2 untuk menghasilkan rekomendasi mitigasi berbasis dokumen sumber, lengkap dengan sitasi.

### Yang Harus Dikerjakan

**4.1 — Template Prompt (config/prompts/mitigation.txt)**
Tulis prompt RAG generation sesuai masterplan Lampiran A.3:
- System prompt sebagai penasihat respons insiden
- Aturan: setiap rekomendasi harus punya sitasi, maks 5 langkah, Bahasa Indonesia
- Format output JSON yang ketat

**4.2 — Implementasi Agen (app/agents/mitigation.py)**
```python
class MitigationAdvisorAgent:
    def __init__(self, llm_client, retriever, reranker):
        self.llm = llm_client
        self.retriever = retriever
        self.reranker = reranker

    async def generate_mitigation(
        self,
        sanitized_input: str,
        incident_type: str,
        severity: str
    ) -> dict:
        # 1. Formulate retrieval query dari input + incident_type
        # 2. Jalankan hybrid retrieval (top 20)
        # 3. Rerank ke top 5
        # 4. Assemble context string dari top 5 chunk
        # 5. Format prompt RAG dengan context + input
        # 6. Panggil LLM
        # 7. Parse response JSON
        # 8. Validasi: setiap step harus punya field "source"
        # 9. Hitung rag_confidence berdasarkan retrieval scores
        # Return: dict dengan mitigation_recommendation, citations, retrieved_chunks, rag_confidence
```

**4.3 — Logika Agentic RAG (Iteratif)**
Tambahkan loop iteratif di `generate_mitigation()`:
```python
# Iterasi 1: Query awal
results = self.retriever.retrieve(query, incident_type)
if self._check_adequacy(results) == False:
    # Iterasi 2: Query yang diperluas/diubah
    expanded_query = self._expand_query(query, incident_type)
    results_2 = self.retriever.retrieve(expanded_query)
    results = self._merge_results(results, results_2)
# Maks 3 iterasi
```

**4.4 — Validasi Sitasi**
Implementasikan fungsi yang memverifikasi bahwa setiap sitasi merujuk ke chunk yang benar-benar ada di retrieved_chunks. Jika ada klaim tanpa sitasi → hapus atau tandai.

**4.5 — Fallback Jika Tidak Ada Dokumen Relevan**
Jika semua retrieval score di bawah threshold (0.3):
```python
return {
    "mitigation_recommendation": "Sistem tidak menemukan panduan SOP yang relevan untuk jenis insiden ini. Silakan hubungi tim CSIRT secara langsung untuk penanganan lebih lanjut.",
    "citations": [],
    "rag_confidence": 0.0
}
```

**4.6 — Unit Test Mitigation Advisor**
```python
# tests/test_agents/test_mitigation.py
def test_generate_mitigation_phishing()       # Ada dokumen relevan → rekomendasi + sitasi
def test_generate_mitigation_with_citations() # Setiap step punya source
def test_agentic_rag_retry()                  # Query pertama jelek → retry berhasil
def test_fallback_no_relevant_docs()          # Tidak ada dokumen → pesan fallback
def test_citation_validation()                # Sitasi palsu → dihapus
```

**4.7 — Test Manual Interaktif**
```bash
python scripts/test_mitigation.py "Email phishing dari CEO" "Phishing" "Tinggi"
# Output: JSON dengan 3-5 langkah mitigasi + sitasi ke NIST/ATT&CK
```

### Kriteria Selesai (Checklist)
```
[ ] Template prompt RAG tersimpan di config/prompts/mitigation.txt
[ ] MitigationAdvisorAgent terintegrasi dengan HybridRetriever dan Reranker
[ ] Logika Agentic RAG (iterasi maks 3x) berfungsi
[ ] Setiap rekomendasi punya sitasi yang valid
[ ] Fallback message jika tidak ada dokumen relevan
[ ] Validasi sitasi menghapus klaim tanpa sumber
[ ] Unit test pass
[ ] Script test manual menghasilkan rekomendasi yang masuk akal
[ ] Commit ke Git
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–4 sudah selesai. Dua agen standalone berfungsi: Identificator (klasifikasi) dan Mitigation Advisor (RAG + rekomendasi dengan sitasi). Lanjut ke Fase 5: Agen Ticket Manager & Notifier."

---

## FASE 5: Agen Ticket Manager & Notifier

### Tujuan
Membangun dua agen terakhir: Ticket Manager yang merangkai data menjadi tiket dan menyimpan ke database, serta Notifier yang mengirim notifikasi.

### Yang Harus Dikerjakan

**5.1 — Agen Ticket Manager (app/agents/ticket_manager.py)**
```python
class TicketManagerAgent:
    def __init__(self, ticket_repository):
        self.repo = ticket_repository

    async def create_ticket(self, incident_state: dict) -> dict:
        # 1. Validasi semua field wajib ada di incident_state
        # 2. Generate ticket_id via generate_ticket_id()
        # 3. Tentukan escalation_level berdasarkan severity:
        #    Kritis → "Segera", Tinggi → "Mendesak",
        #    Sedang → "Standar", Rendah/Info → "Rutin"
        # 4. Cek duplikat (check_duplicate)
        # 5. Simpan ke database
        # 6. Return: ticket_id, ticket_status, escalation_level
```

**5.2 — Agen Notifier (app/agents/notifier.py)**
```python
class NotifierAgent:
    def __init__(self, telegram_client=None):
        self.telegram = telegram_client  # Bisa None untuk testing

    async def send_notifications(self, incident_state: dict) -> dict:
        # 1. Format pesan notifikasi untuk CSIRT
        # 2. Format pesan konfirmasi untuk pelapor
        # 3. Tentukan routing berdasarkan severity
        # 4. Kirim via Telegram (atau log jika client None)
        # 5. Return: notification_sent, recipients, timestamp

    def _format_csirt_notification(self, state: dict) -> str:
        # Template: emoji severity + ticket_id + jenis + ringkasan

    def _format_reporter_confirmation(self, state: dict) -> str:
        # Template: konfirmasi + ticket_id + langkah mitigasi ringkas
```

**5.3 — Template Pesan (app/telegram/templates.py)**
Buat template pesan Telegram dalam Bahasa Indonesia:
```python
CSIRT_ALERT_TEMPLATE = """
🚨 [{severity}] Insiden Baru — {ticket_id}

📋 Jenis: {incident_type}
⚠️ Keparahan: {severity}
👤 Pelapor: {reporter_name}
🕐 Waktu: {timestamp}

📝 Ringkasan:
{description_short}

🔧 Rekomendasi Awal:
{mitigation_short}

📎 Detail lengkap tersedia di sistem tiket.
"""

REPORTER_CONFIRMATION_TEMPLATE = """
✅ Laporan Anda telah diterima.

📌 Tiket: {ticket_id}
📋 Jenis Insiden: {incident_type} (Kepercayaan: {confidence}%)
⚠️ Tingkat Keparahan: {severity}

🔧 Langkah Mitigasi Awal:
{mitigation_steps}

Tim Keamanan Siber telah diberitahu dan akan menindaklanjuti.
Simpan nomor tiket di atas untuk referensi.
"""
```

**5.4 — Unit Test**
```python
# tests/test_agents/test_ticket_manager.py
def test_create_ticket_success()
def test_escalation_level_mapping()
def test_duplicate_detection()
def test_missing_required_fields()

# tests/test_agents/test_notifier.py
def test_format_csirt_notification()
def test_format_reporter_confirmation()
def test_severity_routing()
```

### Kriteria Selesai (Checklist)
```
[ ] TicketManagerAgent bisa merangkai IncidentState → tiket di database
[ ] Ticket ID format TICKET-YYYY-NNNN benar
[ ] Escalation level otomatis sesuai severity
[ ] Deteksi duplikat berfungsi
[ ] NotifierAgent bisa format pesan CSIRT dan pelapor
[ ] Template pesan Telegram dalam Bahasa Indonesia
[ ] Routing notifikasi berdasarkan severity
[ ] Semua unit test pass
[ ] Commit ke Git
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–5 sudah selesai. Semua 4 agen standalone berfungsi: Identificator, Mitigation Advisor, Ticket Manager, Notifier. Lanjut ke Fase 6: Menyatukan semuanya dalam LangGraph Orchestrator."

---

## FASE 6: Orchestrator & Graf LangGraph

### Tujuan
Menyatukan semua agen ke dalam satu graf LangGraph yang dikelola oleh Orchestrator Agent. Ini adalah **jantung sistem** — di mana alur kerja end-to-end pertama kali berjalan.

### Yang Harus Dikerjakan

**6.1 — Template Prompt Orchestrator (config/prompts/orchestrator.txt)**
Prompt untuk klasifikasi intent: report_incident / query_status / general_help

**6.2 — Agen Orchestrator (app/agents/orchestrator.py)**
```python
class OrchestratorAgent:
    def __init__(self, llm_client):
        self.llm = llm_client

    async def classify_intent(self, sanitized_input: str) -> dict:
        # Return: {"intent": "...", "confidence": 0.XX, "needs_clarification": bool}

    def initialize_state(self, raw_input, reporter_info) -> IncidentState:
        # Buat IncidentState baru dengan field input terisi
```

**6.3 — Definisi Graf LangGraph (app/agents/graph.py)**
```python
from langgraph.graph import StateGraph, END
from app.agents.state import IncidentState

def build_helpdesk_graph(
    orchestrator, identifier, mitigation_advisor, ticket_manager, notifier
) -> StateGraph:

    graph = StateGraph(IncidentState)

    # Tambahkan node
    graph.add_node("classify_intent", orchestrator_node)
    graph.add_node("identify_incident", identifier_node)
    graph.add_node("generate_mitigation", mitigation_node)
    graph.add_node("create_ticket", ticket_node)
    graph.add_node("send_notification", notifier_node)

    # Tambahkan edge / routing
    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges("classify_intent", route_by_intent, {
        "report_incident": "identify_incident",
        "needs_clarification": END,  # Kirim balik ke user
        "query_status": END,         # Fase lanjutan
        "general_help": END,         # Fase lanjutan
    })

    graph.add_edge("identify_incident", "generate_mitigation")
    graph.add_edge("generate_mitigation", "create_ticket")
    graph.add_edge("create_ticket", "send_notification")
    graph.add_edge("send_notification", END)

    return graph.compile()
```

**6.4 — Node Functions**
Setiap node adalah fungsi async yang:
1. Menerima `IncidentState` saat ini
2. Memanggil agen yang sesuai
3. Memperbarui dan mengembalikan `IncidentState` yang diperbarui
4. Menambahkan entry ke `agent_trace`
5. Menangkap error dan menambahkan ke `processing_errors`

```python
async def identifier_node(state: IncidentState) -> IncidentState:
    try:
        result = await identifier.classify(state["sanitized_input"])
        state["incident_type"] = result["incident_type"]
        state["severity"] = result["severity"]
        state["confidence_score"] = result["confidence_score"]
        state["classification_reasoning"] = result["reasoning"]
        state["agent_trace"].append({
            "agent": "identifier",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
    except Exception as e:
        state["processing_errors"].append(f"Identifier error: {str(e)}")
        state["incident_type"] = "Lainnya"
        state["severity"] = "Sedang"
        state["confidence_score"] = 0.0
    return state
```

**6.5 — Test End-to-End Pertama**
Buat script `scripts/test_pipeline.py`:
```python
# Input: teks laporan
# Output: IncidentState lengkap setelah melewati semua agen
# Tanpa Telegram, tanpa guardrails — murni pipeline agen
```

**6.6 — Test Skenario Error**
- Test ketika identifier gagal → pipeline tetap lanjut dengan default
- Test ketika RAG tidak menemukan dokumen → fallback message
- Test ketika database gagal → tiket di-queue, error di-log

### Kriteria Selesai (Checklist)
```
[ ] OrchestratorAgent bisa klasifikasi intent (3 jenis)
[ ] Graf LangGraph terdefinisi dengan semua node dan edge
[ ] Pipeline berjalan end-to-end: input teks → IncidentState lengkap
[ ] agent_trace terisi untuk setiap langkah
[ ] Error handling: setiap agen punya fallback, pipeline tidak crash
[ ] Routing kondisional berdasarkan intent berfungsi
[ ] Test end-to-end dengan minimal 3 skenario berbeda berhasil
[ ] Commit ke Git
```

### Cara Verifikasi
```bash
# Test end-to-end
python scripts/test_pipeline.py "Saya menerima email phishing dari CEO meminta transfer"
# Harus output: IncidentState lengkap dengan ticket_id, mitigation, dll.

python scripts/test_pipeline.py "Ada yang aneh di komputer saya"
# Harus: intent ambigu → klarifikasi ATAU classify dengan confidence rendah

python scripts/test_pipeline.py "Status tiket TICKET-2026-0001"
# Harus: intent = query_status
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–6 sudah selesai. Pipeline multi-agent end-to-end berjalan via LangGraph: input → orchestrator → identifier → mitigation advisor → ticket manager → notifier. Belum ada guardrails dan Telegram. Lanjut ke Fase 7: Lapisan Keamanan."

---

## FASE 7: Lapisan Keamanan (Guardrails)

### Tujuan
Menambahkan lapisan keamanan yang melindungi pipeline: sanitasi input, deteksi prompt injection, validasi output, penyuntingan PII.

### Yang Harus Dikerjakan

**7.1 — Input Sanitizer (app/security/sanitizer.py)**
```python
class InputSanitizer:
    MAX_LENGTH = 2000

    def sanitize(self, raw_input: str) -> str:
        # 1. Strip HTML tags
        # 2. Normalize encoding ke UTF-8
        # 3. Potong jika melebihi MAX_LENGTH
        # 4. Hapus karakter kontrol
        # Return: cleaned string
```

**7.2 — Deteksi Prompt Injection (app/security/prompt_injection.py)**
```python
class PromptInjectionDetector:
    def __init__(self):
        self.patterns = [...]  # Daftar regex pattern injeksi

    def detect(self, text: str) -> dict:
        # Layer 1: Regex pattern matching
        # Layer 2: (opsional untuk prototipe) Embedding similarity
        # Return: {"is_injection": bool, "confidence": float, "matched_pattern": str}
```

Daftar pattern minimal untuk prototipe:
- `ignore previous`, `ignore all`, `disregard`
- `you are now`, `act as`, `pretend to be`
- `system prompt`, `reveal your instructions`
- `\x`, `\u00`, base64 pattern

**7.3 — PII Redactor (app/security/pii_redactor.py)**
```python
class PIIRedactor:
    def redact(self, text: str) -> tuple[str, dict]:
        # 1. Deteksi dan ganti IP addresses → [IP_DISUNTING_N]
        # 2. Deteksi dan ganti email → [EMAIL_DISUNTING]
        # 3. Deteksi dan ganti NIK (16 digit) → [NIK_DISUNTING]
        # 4. Deteksi dan ganti nomor telepon → [TELP_DISUNTING]
        # Return: (redacted_text, mapping_dict)

    def restore(self, redacted_text: str, mapping: dict) -> str:
        # Kembalikan placeholder ke nilai asli (untuk tiket internal)
```

**7.4 — Output Validator (app/security/validator.py)**
```python
class OutputValidator:
    ALLOWED_ACTIONS = [
        "ganti kata sandi", "putuskan koneksi", "laporkan ke IT",
        "jangan klik link", "scan antivirus", "backup data",
        "hubungi CSIRT", "isolasi perangkat", "dokumentasikan kejadian",
        ...
    ]

    def validate(self, output: str, retrieved_chunks: list) -> dict:
        # 1. Cek apakah ada PII yang bocor di output
        # 2. Cek apakah sitasi valid (merujuk chunk yang ada)
        # 3. Return: {"is_valid": bool, "issues": list, "cleaned_output": str}
```

**7.5 — Integrasi ke Pipeline**
Modifikasi `app/agents/graph.py` untuk menambahkan node keamanan:
- Tambah node `sanitize_input` sebelum `classify_intent`
- Tambah node `check_guardrails` antara sanitasi dan orchestrator
- Tambah node `validate_output` antara mitigation dan ticket creation

**7.6 — Unit Test Keamanan**
```python
# tests/test_security/test_sanitizer.py
def test_strip_html_tags()
def test_max_length_enforcement()

# tests/test_security/test_prompt_injection.py
def test_detect_basic_injection()
def test_detect_encoding_obfuscation()
def test_normal_report_not_flagged()

# tests/test_security/test_pii_redactor.py
def test_redact_ip_address()
def test_redact_email()
def test_redact_nik()
def test_restore_original_values()
```

### Kriteria Selesai (Checklist)
```
[ ] InputSanitizer berfungsi (strip HTML, normalize, potong)
[ ] PromptInjectionDetector mendeteksi minimal 5 pola injeksi
[ ] Laporan normal TIDAK ditandai sebagai injeksi (false positive rendah)
[ ] PIIRedactor bisa redact IP, email, NIK, telepon + restore
[ ] OutputValidator bisa validasi sitasi dan cek PII di output
[ ] Node keamanan terintegrasi ke graf LangGraph
[ ] Pipeline tetap berjalan end-to-end dengan guardrails aktif
[ ] Unit test keamanan pass
[ ] Commit ke Git
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–7 sudah selesai. Pipeline multi-agent end-to-end berjalan dengan lapisan keamanan aktif: sanitasi → deteksi injeksi → pipeline agen → validasi output. Lanjut ke Fase 8: Integrasi Bot Telegram."

---

## FASE 8: Integrasi Bot Telegram

### Tujuan
Menghubungkan seluruh pipeline dengan antarmuka pengguna nyata: bot Telegram yang bisa menerima laporan dari pegawai dan membalas dengan hasil pra-triase.

### Yang Harus Dikerjakan

**8.1 — Setup Bot Telegram**
- Buat bot baru via @BotFather
- Simpan token di `.env`
- Konfigurasi command: `/start`, `/report`, `/status`, `/help`

**8.2 — Handler Bot (app/telegram/bot.py)**
```python
# Handler /start → pesan selamat datang
# Handler /report → mulai flow pelaporan
# Handler /status <ticket_id> → cari status tiket
# Handler /help → panduan penggunaan

# Conversation flow untuk /report:
# 1. User kirim /report
# 2. Bot tanya: "Silakan jelaskan insiden keamanan siber yang Anda alami."
# 3. User kirim deskripsi
# 4. Bot proses via pipeline LangGraph
# 5. Bot kirim konfirmasi + ticket_id + rekomendasi mitigasi
```

**8.3 — Integrasi Pipeline**
```python
async def handle_incident_report(update, context):
    user = update.effective_user
    text = update.message.text

    # 1. Jalankan pipeline LangGraph
    result = await helpdesk_graph.ainvoke({
        "raw_input": text,
        "reporter_id": str(user.id),
        "reporter_name": user.full_name,
        "reporter_contact": f"@{user.username}",
        ...
    })

    # 2. Kirim konfirmasi ke pelapor
    await update.message.reply_text(
        format_reporter_confirmation(result)
    )

    # 3. Kirim notifikasi ke grup CSIRT
    await context.bot.send_message(
        chat_id=CSIRT_CHAT_ID,
        text=format_csirt_notification(result)
    )
```

**8.4 — Daftar Putih Pengguna (Opsional untuk Prototipe)**
Untuk membatasi akses:
```python
ALLOWED_USERS = [123456789, 987654321]  # Telegram user IDs

def is_authorized(user_id: int) -> bool:
    return user_id in ALLOWED_USERS
```

**8.5 — Test Integrasi**
- Test kirim `/report` → bot merespons dengan konfirmasi
- Test kirim pesan random → bot arahkan ke `/help`
- Test kirim laporan ambigu → bot minta klarifikasi
- Test kirim prompt injection → bot tolak

### Kriteria Selesai (Checklist)
```
[ ] Bot Telegram aktif dan merespons /start, /report, /help
[ ] Flow percakapan /report berjalan: tanya → terima → proses → jawab
[ ] Pipeline LangGraph terpanggil dari handler bot
[ ] Pesan konfirmasi terkirim ke pelapor dalam Bahasa Indonesia
[ ] Notifikasi terkirim ke grup CSIRT Telegram
[ ] Handler /status bisa menampilkan info tiket
[ ] Bot menolak pengguna yang tidak berwenang (jika whitelist aktif)
[ ] Commit ke Git
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–8 sudah selesai. Bot Telegram aktif, terintegrasi dengan pipeline multi-agent + guardrails. Bisa terima laporan, proses, dan kirim notifikasi. Lanjut ke Fase 9: Integrasi End-to-End & Docker."

---

## FASE 9: Integrasi End-to-End & Docker

### Tujuan
Menyatukan seluruh komponen ke dalam deployment Docker yang bisa dijalankan dengan satu perintah. Pastikan semua komponen bekerja bersama.

### Yang Harus Dikerjakan

**9.1 — Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**9.2 — Docker Compose Lengkap**
Update `docker-compose.yml` dengan semua servis:
- `api` — FastAPI server
- `telegram-bot` — bot Telegram (proses terpisah)
- `db` — PostgreSQL
- `redis` — Redis
- `qdrant` — Qdrant

**9.3 — FastAPI Endpoints**
Tambahkan endpoint REST untuk:
```python
POST /api/v1/report          # Terima laporan insiden via API
GET  /api/v1/tickets/{id}    # Ambil detail tiket
GET  /api/v1/tickets         # Daftar tiket (dengan filter)
GET  /api/v1/health          # Health check
```

**9.4 — Structured Logging (app/utils/logger.py)**
Implementasikan logging terstruktur dengan `structlog`:
- Setiap log entry memiliki: timestamp, level, event, session_id, agent_name
- Log ke stdout dalam format JSON

**9.5 — Audit Trail (app/utils/audit.py)**
Integrasi audit logging ke semua agen:
```python
async def log_audit_event(session_id, agent_name, action, input_summary, output_summary, ...):
    # Simpan ke tabel audit_logs via AuditRepository
```

**9.6 — End-to-End Test**
Buat script `scripts/e2e_test.py` yang:
1. Kirim 5 skenario berbeda ke API/bot
2. Verifikasi tiket terbuat di database
3. Verifikasi audit log terisi
4. Verifikasi notifikasi dikirim (atau di-log)
5. Cetak summary pass/fail

**9.7 — Script Setup Awal**
Buat `scripts/setup.sh` yang:
```bash
#!/bin/bash
docker compose up -d
sleep 10  # Tunggu servis siap
alembic upgrade head
python scripts/ingest_knowledge.py --docs-dir knowledge_base/documents/
echo "Setup selesai! Jalankan bot dengan: docker compose up telegram-bot"
```

### Kriteria Selesai (Checklist)
```
[ ] docker compose up -d menjalankan semua 5 servis tanpa error
[ ] FastAPI endpoints berfungsi (test via curl/Postman)
[ ] Bot Telegram berjalan dalam container
[ ] Pipeline end-to-end: Telegram → Guardrails → Agen → DB → Notifikasi
[ ] Structured logging aktif (JSON ke stdout)
[ ] Audit trail tersimpan di database untuk setiap request
[ ] script/setup.sh berjalan dan sistem siap pakai
[ ] E2E test pass minimal 4/5 skenario
[ ] Commit ke Git
```

### Cara Verifikasi
```bash
# Full setup
chmod +x scripts/setup.sh && ./scripts/setup.sh

# Health check
curl http://localhost:8000/api/v1/health

# E2E test
python scripts/e2e_test.py

# Cek database
docker compose exec db psql -U postgres -d helpdesk \
  -c "SELECT ticket_id, incident_type, severity, status FROM incident_tickets;"
```

### Konteks untuk Sesi Berikutnya
> "Fase 0–9 sudah selesai. Sistem berjalan end-to-end dalam Docker: Telegram bot → Guardrails → Multi-Agent Pipeline → Database → Notifikasi. Lanjut ke Fase 10: Evaluasi & Pengujian."

---

## FASE 10: Evaluasi & Pengujian

### Tujuan
Menjalankan seluruh evaluasi yang direncanakan dalam proposal: Task Completion Rate, metrik RAG (RAGAS), dan persiapan System Usability Scale.

### Yang Harus Dikerjakan

**10.1 — Dataset Skenario Evaluasi (tests/evaluation/scenarios.json)**
Buat 30–50 skenario uji dalam format JSON:
```json
[
  {
    "id": "SC-001",
    "input": "Saya menerima email dari CEO meminta transfer dana segera dengan link login palsu",
    "expected_type": "Phishing",
    "expected_severity": "Tinggi",
    "category": "clear_report"
  },
  {
    "id": "SC-002",
    "input": "Komputer saya lambat dan ada popup minta bayar Bitcoin",
    "expected_type": "Ransomware",
    "expected_severity": "Kritis",
    "category": "clear_report"
  },
  ...
  {
    "id": "SC-030",
    "input": "Ada yang aneh di komputer saya",
    "expected_type": null,
    "expected_severity": null,
    "category": "ambiguous"
  }
]
```

**10.2 — Script Evaluasi TCR (tests/evaluation/eval_tcr.py)**
```python
# Untuk setiap skenario:
#   1. Kirim ke pipeline
#   2. Cek: incident_type terisi?
#   3. Cek: mitigation_recommendation terisi dengan sitasi?
#   4. Cek: ticket_id terbuat di database?
#   5. Cek: notifikasi berhasil?
# Jika semua 4 langkah berhasil → COMPLETE, jika tidak → INCOMPLETE
# Hitung TCR = jumlah COMPLETE / total skenario × 100%
```

Output:
```
=== Evaluasi Task Completion Rate ===
Total skenario: 30
Berhasil lengkap: 26
Parsial: 3
Gagal: 1

TCR = 86.7% ✅ (target: ≥ 80%)
```

**10.3 — Script Evaluasi RAG (tests/evaluation/eval_rag.py)**
Buat dataset Q&A pasangan untuk evaluasi RAGAS:
```json
[
  {
    "question": "Apa langkah pertama yang harus dilakukan saat menerima email phishing?",
    "ground_truth": "Jangan klik link atau lampiran, laporkan ke tim IT/CSIRT",
    "context_source": "NIST SP 800-61, Section 3.4"
  }
]
```

Implementasikan evaluasi:
- **Context Relevance:** Apakah chunk yang diambil relevan?
- **Answer Relevance:** Apakah jawaban menjawab pertanyaan?
- **Faithfulness:** Apakah jawaban konsisten dengan konteks?

Gunakan library `ragas` jika tersedia, atau hitung manual dengan LLM-as-judge.

**10.4 — Persiapan SUS**
- Buat kuesioner SUS dalam Google Forms (10 pertanyaan standar, Bahasa Indonesia)
- Buat panduan penggunaan singkat untuk peserta uji
- Siapkan 5 skenario yang akan diujikan ke pegawai

**10.5 — Laporan Evaluasi**
Buat script yang menghasilkan ringkasan evaluasi:
```
=== RINGKASAN EVALUASI SISTEM ===

1. Task Completion Rate
   TCR: XX.X%
   Detail per jenis insiden: [tabel]

2. Evaluasi RAG (RAGAS)
   Context Relevance: X.XX
   Answer Relevance: X.XX
   Faithfulness: X.XX

3. Catatan
   - Skenario yang gagal: [daftar]
   - Alasan kegagalan: [daftar]
   - Rekomendasi perbaikan: [daftar]
```

### Kriteria Selesai (Checklist)
```
[ ] Dataset evaluasi 30+ skenario tersedia
[ ] Script evaluasi TCR berjalan dan menghasilkan angka TCR
[ ] Script evaluasi RAG berjalan dan menghasilkan 3 metrik RAGAS
[ ] Dataset Q&A untuk evaluasi RAG minimal 20 pasangan
[ ] Kuesioner SUS siap (Google Forms atau printout)
[ ] Laporan evaluasi tergenerate otomatis
[ ] Semua hasil terdokumentasikan
[ ] Commit ke Git (FINAL)
```

---

## Ringkasan Checklist Keseluruhan

Gunakan tabel ini untuk tracking progress:

```
Fase  Nama                                Status
────  ──────────────────────────────────  ──────
  0   Persiapan Lingkungan & Struktur     [ ]
  1   Database & Model Data               [ ]
  2   Pipeline RAG (Ingesti & Retrieval)  [ ]
  3   Agen Identificator Insiden          [ ]
  4   Agen Mitigation Advisor + RAG       [ ]
  5   Agen Ticket Manager & Notifier      [ ]
  6   Orchestrator & Graf LangGraph       [ ]
  7   Lapisan Keamanan (Guardrails)       [ ]
  8   Integrasi Bot Telegram              [ ]
  9   Integrasi End-to-End & Docker       [ ]
 10   Evaluasi & Pengujian                [ ]
```

---

## Tips Penggunaan

### Memulai Sesi Baru
Selalu berikan konteks ini di awal sesi:

```
Saya sedang mengerjakan proyek helpdesk keamanan siber multi-agent.
Tech stack: Python, FastAPI, LangGraph, Qdrant, PostgreSQL, GPT-4o, Telegram Bot.

Status progress: Fase [X] sudah selesai, sekarang mengerjakan Fase [Y].

Yang sudah berfungsi:
- [daftar komponen yang sudah jadi]

Yang sedang dikerjakan:
- [task spesifik dari checklist fase Y yang belum selesai]

Struktur proyek ada di folder: [path]
```

### Jika Ada Error
```
Fase [X], task [X.Y] gagal dengan error berikut:
[paste error]
File yang terlibat: [path file]
Yang sudah dicoba: [langkah yang sudah dilakukan]
```

### Sebelum Tutup Sesi
Selalu minta alat bantu kerja untuk:
1. Pastikan semua file tersimpan
2. Jalankan test yang relevan
3. Commit ke Git dengan pesan deskriptif
4. Cetak ringkasan apa yang sudah selesai dan apa yang belum

---

*Dokumen ini adalah panduan hidup — update checklist seiring progress pengerjaan.*
