# Sistem Helpdesk Keamanan Siber Multi-Agent

> Sistem berbasis AI untuk otomatisasi pra-triase laporan insiden keamanan siber. Menerima laporan dalam bahasa alami melalui Telegram Bot dan Web Chat, lalu memproses secara otomatis menggunakan pipeline multi-agent.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Academic-yellow.svg)](#)

## Tentang Proyek

Sistem menerima laporan insiden keamanan siber dalam bahasa alami, lalu secara otomatis:

1. **Mengidentifikasi** jenis insiden dan tingkat keparahan
2. **Mengambil** dokumen referensi yang relevan via Agentic RAG (NIST SP 800-61, MITRE ATT&CK, BSSN)
3. **Menghasilkan** rekomendasi mitigasi awal berbasis dokumen sumber dengan citation validation
4. **Membuat** tiket terstruktur di database
5. **Mengirim** notifikasi ke tim CSIRT

Semua output bersifat **advis** — keputusan akhir tetap di tangan analis CSIRT (human-in-the-loop).

## Arsitektur

```
Pelapor
    │
    ▼
[Telegram Bot / Web Chat] → [Sanitasi & Guardrails] → [Orchestrator Agent]
                                                               │
                               ┌───────────────────────────────┤
                               ▼                               ▼
                       [Identifier Agent]           [Mitigation Advisor]
                       Klasifikasi insiden          Agentic RAG → Mitigasi + Sitasi
                               │                               │
                               └──────────────┬────────────────┘
                                              ▼
                                      [Ticket Manager]
                                      Buat tiket di DB
                                              │
                                              ▼
                                        [Notifier]
                                  Kirim ke CSIRT + Pelapor
```

**Tech Stack:** Python · FastAPI · LangGraph · GPT-4o · Qdrant · PostgreSQL · Redis · Telegram Bot · HTMX

## Quick Start

### Prasyarat

- Python 3.11+
- Docker & Docker Compose
- GitHub Token (GitHub Models) atau OpenAI API Key
- Token Bot Telegram (dari @BotFather)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/gr0zhx/pusdatin-help.git
cd pusdatin-help

# 2. Buat file environment
cp .env.example .env
# Edit .env → isi GITHUB_TOKEN (atau OPENAI_API_KEY) dan TELEGRAM_BOT_TOKEN

# 3. Jalankan infrastruktur
docker compose up -d

# 4. Install dependencies
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 5. Jalankan migrasi database
alembic upgrade head

# 6. Seed akun admin pertama
python scripts/seed_admin.py

# 7. Ingest basis pengetahuan
python scripts/ingest_knowledge.py --docs-dir knowledge_base/documents/

# 8. Jalankan API server
uvicorn app.main:app --reload

# 9. Jalankan bot Telegram (terminal terpisah)
python -m app.telegram.bot
```

## Penggunaan

### Melaporkan Insiden via Telegram

```
/report Saya menerima email mencurigakan yang mengaku dari direktur,
berisi link ke halaman login palsu yang meminta memasukkan password.
```

Bot akan membalas dengan tiket + rekomendasi mitigasi:

```
✅ Laporan Anda telah diterima.

📌 Tiket: TICKET-2026-0047
📋 Jenis Insiden: Phishing (Kepercayaan: 92%)
⚠️ Tingkat Keparahan: Tinggi

🔧 Langkah Mitigasi Awal:
1. Jangan klik link atau lampiran dalam email tersebut
   [Ref: NIST SP 800-61, Bagian 3.4.1]
2. Laporkan email ke tim IT dan tandai sebagai phishing
   [Ref: MITRE ATT&CK, M1017]
3. Ganti kata sandi akun email Anda segera
   [Ref: NIST SP 800-61, Bagian 3.4.2]

Tim Keamanan Siber telah diberitahu dan akan menindaklanjuti.
```

### Web Chat

Akses melalui browser di `/lapor` — isi formulir identitas lalu mulai percakapan dengan chatbot.

### Dashboard Admin CSIRT

Akses di `/admin/login` — kelola tiket, update status, triase CIA, generate laporan insiden.

## Jenis Insiden yang Didukung

| Jenis | Contoh |
| ----- | ------ |
| Phishing | Email palsu, link login palsu, permintaan data sensitif |
| Malware | Program mencurigakan terinstall, perilaku aneh pada komputer |
| Ransomware | File terenkripsi, permintaan tebusan, popup pembayaran |
| Web Defacement | Tampilan website berubah, konten diganti |
| DDoS | Server tidak bisa diakses, layanan lambat |
| Akses Tidak Sah | Login dari lokasi tidak dikenal, akses tanpa izin |
| Kebocoran Data | Data internal ditemukan di luar organisasi |
| Lainnya | Insiden yang tidak masuk kategori di atas |

## Evaluasi

Sistem dievaluasi menggunakan tiga metrik utama:

| Metrik | Target |
|--------|--------|
| Task Completion Rate (TCR) | ≥ 80% |
| RAG Quality — RAGAS (Context Relevance / Answer Relevance / Faithfulness) | ≥ 0.75 / 0.80 / 0.85 |
| System Usability Scale (SUS) | ≥ 68 |

```bash
# Evaluasi Task Completion Rate
python tests/evaluation/eval_tcr.py

# Evaluasi RAG (RAGAS)
python tests/evaluation/eval_ragas.py --dataset tests/evaluation/rag_qa_dataset_nist.json
```

## Dokumentasi

- **Code Overview:** `docs/CODE_OVERVIEW.md` — penjelasan setiap file, fungsi, dan logika internal
- **Masterplan Teknis:** `docs/MASTERPLAN.md` — arsitektur lengkap dan desain sistem
- **Panduan Kontribusi:** `CLAUDE.md` — konteks, aturan koding, dan referensi

## Pengembangan

```bash
# Jalankan test suite
pytest tests/ -v

# Linting
ruff check app/
ruff format app/
```

## Referensi

- NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide
- MITRE ATT&CK Enterprise Framework
- Peraturan BSSN Nomor 1 Tahun 2024
- LangGraph Documentation
- OWASP Top 10 for LLM Applications

---

*Proyek ini dikembangkan untuk keperluan penelitian akademis.*
