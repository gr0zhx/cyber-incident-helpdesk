# CLAUDE.md

## Proyek

Sistem helpdesk keamanan siber multi-agent untuk pra-triase insiden di Pusdatin Kementan. Chatbot Telegram → klasifikasi insiden → rekomendasi mitigasi (RAG) → tiket → notifikasi CSIRT. Ini prototipe skripsi, bukan produk komersial.

## Tech Stack

Python 3.11+ · FastAPI · LangGraph · GPT-4o API · text-embedding-3-small · Qdrant · PostgreSQL 16 · Redis 7 · python-telegram-bot · Docker Compose

## Dokumen Referensi

- Arsitektur & desain teknis: `docs/MASTERPLAN.md`
- Fase implementasi & checklist: `docs/PHASE_GUIDE.md`
- Diagram: `docs/ARCHITECTURE_DIAGRAMS.md`

Baca dokumen di atas saat butuh detail arsitektur, skema data, atau prompt template. Jangan mengandalkan memori — selalu verifikasi dari dokumen.

## Aturan Koding

- Kode & variabel: **English**. Output UI & prompt LLM: **Bahasa Indonesia**.
- Type hints wajib untuk fungsi publik.
- Semua prompt template di `config/prompts/*.txt`, BUKAN hardcode.
- LLM output selalu parse sebagai JSON dengan error handling.
- Setiap agen harus punya fallback — pipeline tidak boleh crash.
- Agen berkomunikasi HANYA lewat `IncidentState` (di `app/agents/state.py`), tidak langsung.
- Jangan ubah field `IncidentState` tanpa alasan kuat.
- Tiket baru selalu `status: PENDING_REVIEW`.
- Test dengan `pytest`. Nama: `test_<module>.py`.

## Aturan Keamanan

- Fail-closed: guardrails gagal → blokir, jangan teruskan.
- PII WAJIB di-redact sebelum kirim ke LLM API.
- API key, token, password: HANYA dari env vars, JANGAN hardcode.
- File upload whitelist: PNG, JPG, PDF saja.

## Kriteria Sukses

- Task Completion Rate ≥ 80%
- RAG: Context Relevance ≥ 0.75, Answer Relevance ≥ 0.80, Faithfulness ≥ 0.85
- SUS ≥ 68

## Alur Kerja Sesi

1. Cek `docs/PHASE_GUIDE.md` → fase mana yang aktif, apa checklist-nya
2. Kerjakan task dari checklist
3. Jalankan test relevan
4. Commit dengan pesan deskriptif
5. Tulis ringkasan progress sebelum tutup sesi