# 🛡️ Sistem Helpdesk Keamanan Siber Multi-Agent

> Chatbot Telegram berbasis AI untuk otomatisasi pra-triase laporan insiden keamanan siber di lingkungan Pusdatin Kementerian Pertanian.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Academic-yellow.svg)](#)

## Tentang Proyek

Proyek ini merupakan **Tugas Akhir (Skripsi)** pada Program Rekayasa Kriptografi, Politeknik Siber dan Sandi Negara. Sistem menerima laporan insiden keamanan siber dalam bahasa alami dari pegawai melalui Telegram, lalu secara otomatis:

1. **Mengidentifikasi** jenis insiden dan tingkat keparahan
2. **Mengambil** dokumen SOP/referensi yang relevan (RAG)
3. **Menghasilkan** rekomendasi mitigasi awal berbasis dokumen sumber
4. **Membuat** tiket terstruktur di database
5. **Mengirim** notifikasi ke tim CSIRT

Semua output bersifat **advis** — keputusan akhir tetap di tangan tim CSIRT (human-in-the-loop).

## Arsitektur

```
Pegawai Kementan
    │
    ▼
[Telegram Bot] → [Sanitasi & Guardrails] → [Orchestrator Agent]
                                                │
                    ┌───────────────────────────┤
                    ▼                           ▼
            [Identificator]            [Mitigation Advisor]
            Klasifikasi insiden        RAG → Rekomendasi + Sitasi
                    │                           │
                    └───────────┬───────────────┘
                                ▼
                        [Ticket Manager]
                        Buat tiket di DB
                                │
                                ▼
                          [Notifier]
                    Kirim ke CSIRT + Pelapor
```

**Tech Stack:** Python · FastAPI · LangGraph · GPT-4o · Qdrant · PostgreSQL · Redis · Telegram Bot

## Quick Start

### Prasyarat

- Python 3.11+
- Docker & Docker Compose
- API Key OpenAI
- Token Bot Telegram (dari @BotFather)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/gr0zhx/pusdatin-help.git
cd cybersec-helpdesk

# 2. Buat file environment
cp .env.example .env
# Edit .env → isi OPENAI_API_KEY dan TELEGRAM_BOT_TOKEN

# 3. Jalankan infrastruktur
docker compose up -d

# 4. Install dependencies
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 5. Jalankan migrasi database
alembic upgrade head

# 6. Ingest basis pengetahuan
python scripts/ingest_knowledge.py --docs-dir knowledge_base/documents/

# 7. Jalankan API server
uvicorn app.main:app --reload

# 8. Jalankan bot Telegram (terminal terpisah)
python -m app.telegram.bot
```

### Atau Jalankan Semuanya via Docker

```bash
cp .env.example .env
# Edit .env
./scripts/setup.sh
docker compose up
```

## Penggunaan

### Melaporkan Insiden

Kirim pesan ke bot Telegram:

```
/report Saya menerima email mencurigakan dari akun yang mengaku CEO,
berisi link ke halaman login palsu yang meminta memasukkan password.
```

Bot akan membalas:

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

### Cek Status Tiket

```
/status TICKET-2026-0047
```

## Evaluasi

Sistem dievaluasi menggunakan tiga metrik utama:

| Metrik | Target |
|--------|--------|
| Task Completion Rate (TCR) | ≥ 80% |
| RAG Quality (RAGAS: Context Relevance, Answer Relevance, Faithfulness) | ≥ 0.75 / 0.80 / 0.85 |
| System Usability Scale (SUS) | ≥ 68 |

Jalankan evaluasi:

```bash
# Evaluasi Task Completion Rate
python tests/evaluation/eval_tcr.py

# Evaluasi RAG
python tests/evaluation/eval_rag.py
```

## Jenis Insiden yang Didukung

| Jenis | Contoh |
|-------|--------|
| Phishing | Email palsu, link login palsu, permintaan data sensitif |
| Malware | Program mencurigakan terinstall, perilaku aneh pada komputer |
| Ransomware | File terenkripsi, permintaan tebusan, popup pembayaran |
| Web Defacement | Tampilan website berubah, konten diganti |
| DDoS | Server tidak bisa diakses, layanan lambat |
| Akses Tidak Sah | Login dari lokasi tidak dikenal, akses tanpa izin |
| Kebocoran Data | Data internal ditemukan di luar organisasi |
| Lainnya | Insiden yang tidak masuk kategori di atas |

## Dokumentasi

- **Masterplan Teknis:** `docs/MASTERPLAN.md` — arsitektur lengkap, desain agen, pipeline RAG, skema data
- **Panduan Fase:** `docs/PHASE_GUIDE.md` — 11 fase implementasi dengan checklist
- **PRD:** `docs/PRD.md` — kebutuhan produk, fitur, kriteria sukses
- **Diagram:** `docs/ARCHITECTURE_DIAGRAMS.md` — diagram Mermaid arsitektur sistem

## Pengembangan

### Untuk Kontributor / Claude Code

Baca `CLAUDE.md` di root proyek — berisi semua konteks, aturan koding, dan referensi yang dibutuhkan.

### Menjalankan Test

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check app/
ruff format app/
```

## Referensi

- NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide
- MITRE ATT&CK Framework
- LangGraph Documentation
- OWASP Top 10 for LLM Applications

## Penulis

**Agry Zharfa** — NPM 2221101769  
Program Rekayasa Kriptografi — Rekayasa Perangkat Lunak Kripto  
Politeknik Siber dan Sandi Negara  

Pembimbing Materi: Girinoto, S.Si., M.Si.

---

*Proyek ini dikembangkan sebagai bagian dari Tugas Akhir dan ditujukan untuk keperluan penelitian akademis.*
