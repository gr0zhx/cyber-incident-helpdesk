---
# Slide 1 — Bot Telegram: Fungsi Inti & Tujuan

- Antarmuka utama untuk pelaporan insiden keamanan siber oleh pengguna.
- Tujuan: terima laporan cepat, triase otomatis, kirim notifikasi ke CSIRT, sediakan nomor tiket.
- Implementasi: `app/telegram/bot.py` (handler, conversation flow) dan template pesan di `app/telegram/templates.py`.

---
# Slide 2 — Perintah Utama untuk Pengguna

- `/report` : Mulai flow pelaporan (conversation)
- `/status <ticket_id>` : Cek status tiket
- `/help` : Panduan singkat penggunaan
- `/start` : Pesan sambutan

Speaker notes: Tunjukkan contoh singkat saat demo (ketik /report lalu kirim deskripsi).

---
# Slide 3 — Alur Pelaporan (/report)

1. Pengguna ketik `/report` → bot meminta deskripsi singkat (apa, kapan, dampak).
2. Pengguna kirim teks → `report_receive_handler` menerima teks.
3. Bot membuat `IncidentState` via `orchestrator.initialize_state()` dan memanggil `helpdesk_graph.ainvoke(state)` untuk pemrosesan pipeline (intent -> identifier -> RAG -> mitigation -> ticketing).
4. Hasil diproses di `_send_result`: jika perlu klarifikasi, kirim pertanyaan; jika tidak, kirim konfirmasi kepada pelapor dan alert ke CSIRT.

Referensi implementasi: lihat `report_start_handler`, `report_receive_handler`, `_send_result` pada `app/telegram/bot.py`.

---
# Slide 4 — Handler & Tanggung Jawab Teknis

- `start_handler` / `help_handler`: onboarding & panduan.
- `report_start_handler`: memulai ConversationHandler (state WAITING_REPORT).
- `report_receive_handler`: integrasi pipeline — membangun `IncidentState`, memanggil graph, menangani error.
- `_send_result`: mengirimkan:
  - konfirmasi ke pelapor (`format_reporter_confirmation`),
  - alert ke CSIRT (`format_csirt_alert`) jika `CSIRT_CHAT_ID` tersedia.
- `status_handler`: baca status tiket via `ticket_repository` (opsional).
- `cancel_handler`, `unknown_handler`: pengalaman pengguna fallback.

---
# Slide 5 — Konfigurasi & Env yang Penting

- `TELEGRAM_BOT_TOKEN`: token bot (dibutuhkan saat build app)
- `CSIRT_CHAT_ID` (ENV `CSIRT_CHAT_ID`): chat/group ID untuk mengirim alert ke CSIRT
- Dependensi injeksi saat build: `helpdesk_graph`, `orchestrator`, `ticket_repository` (opsional)

Catatan: jika `CSIRT_CHAT_ID` tidak di-set, bot tetap berfungsi tetapi tidak mengirim notifikasi grup otomatis.

---
# Slide 6 — Template Pesan & UX (Ringkas)

- Konfirmasi ke pelapor: `format_reporter_confirmation` (template menyertakan tiket, kepercayaan, mitigasi awal)
- Alert ke CSIRT: `format_csirt_alert` (ringkasan + rekomendasi awal)
- Update status: `format_status_update`
- Template ada di `app/telegram/templates.py`

---
# Slide 7 — Error Handling & Fail-Safe

- Jika pipeline (`helpdesk_graph` / `orchestrator`) tidak tersedia → beri pesan kegagalan ramah ke pengguna.
- Jika parsing/LLM error atau semua langkah tidak tervalidasi → fallback message: arahkan ke CSIRT secara manual.
- Conversation state cleanup: pesan pemrosesan dihapus setelah selesai / error.

---
# Slide 8 — Titik Integrasi Sistem

- `helpdesk_graph`: core pipeline (orchestrator, identifier, RAG, mitigation)
- `orchestrator`: inisialisasi `IncidentState` (lihat `app/agents/orchestrator.py`)
- `ticket_repository`: untuk lookup status tiket di `/status` (opsional, diinjeksi ke `bot_data`)
- `bot_data` injection: `build_bot_application()` menaruh dependensi ke `app.bot_data`

---
# Slide 9 — Contoh Interaksi Singkat (Slide Demo)

1. User: `/report` → bot: "Silakan jelaskan insiden..."
2. User: "Saya klik link phishing dan diminta password" → bot: "⏳ Memproses..."
3. Bot (hasil): "✅ Laporan Anda diterima. Tiket: TICKET-2026-0001. Jenis: Phishing (Kepercayaan 92%). Langkah mitigasi: ..." 
4. CSIRT menerima alert ringkas di grup (jika `CSIRT_CHAT_ID` di-set).

---
# Slide 10 — Ringkasan & Rekomendasi Implementasi

- Bot menyediakan jalur pelaporan cepat + triase otomatis.
- Pastikan ENV `CSIRT_CHAT_ID` dan `TELEGRAM_BOT_TOKEN` dikonfigurasi di deployment.
- Tambahkan batas maksimal ronde klarifikasi dan pemantauan log gagal kirim pesan.
- Saran: tambahkan telemetry (metrics untuk laporan/hits/error) dan salinan pesan ke database untuk audit.

---
