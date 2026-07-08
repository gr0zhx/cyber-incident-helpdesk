# Panduan Ganti Prioritas Provider LLM

Sistem ini bisa jalan pakai dua provider untuk chat completion (bukan
embedding): **GitHub Models** (via `GITHUB_TOKEN`) atau **OpenAI** (via
`OPENAI_API_KEY`). Diatur lewat satu env var: `LLM_PROVIDER`.

## Kapan perlu ganti provider

- **GitHub Models kena rate limit** (tier gratis, limit request/menit cukup
  ketat) — misal pas beberapa responden SUS testing kirim laporan bersamaan.
- **Mau hemat kuota OpenAI** untuk kebutuhan lain, jadi default balik ke
  GitHub Models saat traffic sepi.
- **Eksperimen membandingkan hasil** dua model berbeda untuk evaluasi RAGAS.

## Cara pakai

Set `LLM_PROVIDER` di file `.env`:

```bash
# Default — GITHUB_TOKEN diutamakan, OPENAI_API_KEY jadi fallback otomatis
# kalau GITHUB_TOKEN kosong
LLM_PROVIDER=auto

# Paksa selalu pakai GitHub Models (error kalau GITHUB_TOKEN kosong)
LLM_PROVIDER=github

# Paksa selalu pakai OpenAI (error kalau OPENAI_API_KEY kosong)
LLM_PROVIDER=openai
```

Kedua key (`GITHUB_TOKEN` dan `OPENAI_API_KEY`) boleh sama-sama terisi di
`.env` — `LLM_PROVIDER` yang menentukan mana yang benar-benar dipakai untuk
chat completion, tidak perlu hapus/comment salah satu key tiap ganti pikiran.

## Setelah ganti nilai di .env

Restart proses yang menjalankan API supaya env var baru terbaca:

```bash
# lokal (uvicorn --reload TIDAK otomatis reload env var, harus restart manual)
# Ctrl+C lalu jalankan ulang:
uvicorn app.main:app --reload

# di VPS (docker compose)
docker compose up -d --build api telegram-bot
```

## Catatan

- **Embedding** (`text-embedding-3-small`, dipakai untuk ingest & retrieval
  RAG) tetap selalu lewat endpoint OpenAI standar, tidak terpengaruh
  `LLM_PROVIDER` — karena GitHub Models tidak menyediakan endpoint embedding
  ini. Kalau `OPENAI_API_KEY` kosong, sistem coba pakai `GITHUB_TOKEN` untuk
  embedding juga (perlu akun GitHub dengan akses ke model embedding OpenAI).
- Implementasi ada di [app/utils/llm_client.py](../app/utils/llm_client.py)
  fungsi `_resolve_key_and_base()`.
