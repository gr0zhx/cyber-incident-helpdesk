# Masterplan Teknis: Sistem Helpdesk Keamanan Siber Berbasis Arsitektur Multi-Agent

**Sistem:** Helpdesk Respons Insiden Keamanan Siber Berbasis AI untuk Pusdatin Kementan  
**Penulis:** Agry Zharfa (NPM: 2221101769)  
**Program:** Rekayasa Kriptografi — Rekayasa Perangkat Lunak Kripto  
**Versi:** 1.0  
**Tanggal:** April 2026

---

## 1. Visi Sistem
### 1.1 Tujuan Keseluruhan
Sistem ini merupakan helpdesk keamanan siber berbasis AI yang mengotomatisasi fase **pra-triase** dalam alur respons insiden keamanan siber di lingkungan internal pemerintah — khususnya Pusdatin Kementan (Pusat Data dan Informasi, Kementerian Pertanian Republik Indonesia). Sistem menerima laporan insiden dalam bahasa alami dari pegawai pemerintah melalui antarmuka chatbot Telegram, mengklasifikasikan jenis dan tingkat keparahan insiden, mengambil panduan mitigasi yang terverifikasi dari dokumentasi keamanan siber otoritatif, menghasilkan tiket terstruktur, dan mengirimkan notifikasi kepada tim CSIRT — seluruhnya dalam alur yang aman, dapat diaudit, dan diawasi oleh manusia.

### 1.2 Peran dalam Alur Kerja Respons Insiden
Sistem ini menempati batas antara fase **Persiapan → Deteksi & Analisis** dalam siklus hidup respons insiden NIST SP 800-61. Sistem tidak melakukan mitigasi teknis langsung (misalnya memblokir IP, mengisolasi host). Sebaliknya, sistem mempercepat serah terima antara pelapor (manusia) dan analis CSIRT (manusia) dengan mengotomatisasi:
- Penerimaan dan validasi laporan insiden dalam teks bebas
- Identifikasi kemungkinan jenis insiden (phishing, malware, ransomware, web defacement, DDoS, akses tidak sah, kebocoran data, lainnya)
- Penilaian tingkat keparahan (Kritis, Tinggi, Sedang, Rendah, Informasional)
- Pengambilan SOP dan materi referensi yang relevan (NIST SP 800-61, MITRE ATT&CK)
- Pembuatan rekomendasi mitigasi awal yang berbasis dokumen sumber
- Pembuatan tiket terstruktur dengan ketertelusuran penuh
- Pengiriman notifikasi kepada personel CSIRT yang sesuai

Sistem secara eksplisit mempertahankan otoritas **human-in-the-loop**: semua keluaran bersifat advis, dan tim CSIRT tetap memiliki kendali penuh atas eskalasi dan tindakan respons teknis.

### 1.3 Batasan Lingkup
| Dalam Lingkup | Di Luar Lingkup |
|----------------|-----------------|
| Otomatisasi pra-triase | Mitigasi teknis otomatis (aturan firewall, isolasi host) |
| Penerimaan laporan bahasa alami | Input multi-modal (suara, analisis gambar) — pengembangan lanjutan |
| Klasifikasi dan rekomendasi berbasis LLM | Model yang di-fine-tune atau dilatih khusus |
| Keluaran advis berbasis pengetahuan (RAG) | Integrasi feed intelijen ancaman real-time |
| Pembuatan tiket dan notifikasi | Integrasi penuh SIEM/SOAR |
| Input Bahasa Indonesia dan Inggris | Bahasa lainnya |

---

## 2. Prinsip Secure-by-Design
Karena laporan insiden dapat mengandung informasi internal sensitif (alamat IP, nama pegawai, kredensial sistem, detail infrastruktur), sistem harus dirancang dengan keamanan sebagai kebutuhan fundamental, bukan tambahan di kemudian hari.

### 2.1 Pertahanan Terhadap Prompt Injection
Prompt injection merupakan ancaman LLM dengan prioritas tertinggi (OWASP LLM Top 10, LLM01). Sistem bertahan terhadapnya pada beberapa lapisan:

**Lapisan 1 — Pencocokan Pola Regex:** Filter berbasis aturan yang memindai setiap input pengguna untuk pola injeksi yang diketahui sebelum pemanggilan LLM apa pun. Pola meliputi "ignore previous instructions," "system prompt," upaya pengalihan peran ("you are now"), obfuskasi berbasis encoding (base64, hex, unicode escapes), dan injeksi delimiter (triple backticks, tag XML).

**Lapisan 2 — Deteksi Semantik:** Pengklasifikasi berbasis embedding membandingkan pesan masuk dengan korpus contoh prompt injection yang diketahui. Pesan dengan kemiripan kosinus di atas ambang batas yang ditentukan ditandai untuk peninjauan.

**Lapisan 3 — LLM-as-Judge:** Untuk kasus perbatasan, pemanggilan LLM sekunder dengan system prompt yang ketat dan terisolasi mengevaluasi apakah input merupakan laporan insiden yang sah atau upaya injeksi. Model penilai ini hanya menerima input mentah — tidak pernah system prompt dari agen utama — sehingga tidak dapat dikompromikan oleh injeksi yang sama.

**Lapisan 4 — Pemisahan Struktural:** Input pengguna selalu dimasukkan ke dalam prompt LLM melalui blok variabel yang dibatasi secara jelas (misalnya, `<user_report>...</user_report>`) dan system prompt secara eksplisit menginstruksikan model untuk memperlakukan konten di dalam tag tersebut sebagai data tidak tepercaya, bukan sebagai instruksi.

### 2.2 Sanitasi Input
Semua teks yang dikirimkan pengguna melewati pipeline sanitasi sebelum mencapai agen mana pun:

- Penghapusan tag HTML/script
- Deteksi pola SQL injection
- Pembatasan panjang input maksimum (dapat dikonfigurasi, default 2000 karakter)
- Normalisasi encoding karakter (UTF-8)
- Pemindaian lampiran file dengan ClamAV (jika unggah file didukung)
- Pembatasan laju per sesi pengguna (maksimum 10 laporan per jam)

### 2.3 Validasi Output
Setiap keluaran yang dihasilkan LLM divalidasi sebelum dikembalikan ke pengguna atau disimpan:

- **Verifikasi sitasi:** Setiap rekomendasi mitigasi harus merujuk setidaknya satu potongan sumber dari basis pengetahuan. Klaim tanpa referensi dihapus atau ditandai.
- **Deteksi halusinasi:** Keluaran dibandingkan dengan konteks yang diambil untuk memverifikasi konsistensi faktual. Skor kepercayaan di bawah ambang batas memicu eskalasi ke peninjauan manusia.
- **Penegakan daftar putih tindakan:** Sistem hanya dapat merekomendasikan tindakan dari daftar putih yang telah ditentukan (misalnya, "ganti kata sandi," "putuskan koneksi dari jaringan," "laporkan ke IT"). Sistem tidak dapat merekomendasikan tindakan destruktif atau tidak sah.
- **Pemindaian PII:** Keluaran dipindai untuk PII yang tidak sengaja disertakan (alamat IP internal, nama, kredensial) sebelum dikirim ke kanal eksternal.

### 2.4 Anonimisasi Data Sebelum Pemanggilan LLM
Sebelum input apa pun dikirim ke API LLM eksternal (GPT-4o melalui OpenAI), sistem melakukan:

- Penggantian alamat IP yang terdeteksi dengan placeholder (`[IP_DISUNTING_1]`)
- Penggantian alamat email dengan `[EMAIL_DISUNTING]`
- Penggantian nomor NIK/NIP Indonesia yang terdeteksi dengan `[ID_DISUNTING]`
- Penggantian hostname dan URL internal dengan label generik
- Tabel pemetaan disimpan dalam sesi sehingga nilai asli dapat dipulihkan di tiket akhir (yang disimpan hanya di database internal, tidak pernah dikirim ke LLM)

### 2.5 Audit Logging
Setiap tindakan dalam sistem dicatat dalam format JSON terstruktur ke log audit append-only:
- Identitas pengguna dan metadata sesi
- Input mentah (dengan masking PII pada salinan log)
- Keputusan dan keluaran setiap agen
- Pemicu guardrails dan hasilnya (lolos/blokir/tandai)
- Metadata pemanggilan API LLM (model yang digunakan, jumlah token, latensi)
- Peristiwa pembuatan tiket
- Peristiwa pengiriman notifikasi
- Peristiwa error dan jejak exception
Log disimpan di PostgreSQL dengan kebijakan retensi minimal 12 bulan dan hanya dapat diakses oleh personel audit yang berwenang (dikontrol RBAC).

### 2.6 Arsitektur Least Privilege
- Setiap agen beroperasi dengan izin minimum yang diperlukan untuk fungsinya. Mitigation Advisor dapat membaca database vektor tetapi tidak dapat menulis ke dalamnya. Ticket Manager dapat menyisipkan ke database tiket tetapi tidak dapat menghapus atau memodifikasi tiket yang ada. Notifier dapat mengirim pesan tetapi tidak dapat mengakses konten tiket di luar payload notifikasi.
- Kunci API LLM disimpan sebagai variabel lingkungan atau dalam secrets manager, tidak pernah di-hardcode.
- Koneksi database menggunakan akun layanan khusus per agen dengan izin SQL yang dibatasi.
- Token bot Telegram dibatasi pada metode API bot minimum yang diperlukan.

### 2.7 Penegakan Human-in-the-Loop
- Sistem secara eksplisit TIDAK melakukan mitigasi teknis otomatis.
- Semua tiket yang dihasilkan menyertakan field `status: PENDING_REVIEW` yang harus diubah oleh analis CSIRT manusia sebelum tindakan respons apa pun diambil.
- Klasifikasi dengan kepercayaan rendah (di bawah ambang batas yang dapat dikonfigurasi, default 0,7) ditandai untuk peninjauan manusia wajib sebelum tiket dibuat.
- Tim CSIRT dapat mengganti klasifikasi atau rekomendasi AI mana pun melalui antarmuka admin khusus atau pembaruan database langsung.

### 2.8 Keamanan API
- Semua endpoint API dilindungi oleh autentikasi kunci API (dan opsional autentikasi berbasis JWT untuk endpoint admin).
- HTTPS/TLS diterapkan untuk semua komunikasi eksternal.
- API LLM diakses melalui lapisan proxy yang menerapkan pembatasan laju, mencatat semua pemanggilan, dan dapat melakukan circuit-break jika perilaku anomali terdeteksi.
- Kebijakan CORS membatasi API hanya untuk origin yang berwenang.

### 2.9 Perlindungan Data Sensitif
- Data insiden saat disimpan dienkripsi (AES-256 untuk field database yang berisi konten laporan).
- Backup database dienkripsi.
- Data dalam transit menggunakan TLS 1.2+.
- Akses ke data produksi memerlukan MFA untuk semua personel.
- Label klasifikasi data (Internal, Rahasia, Terbatas) dapat diterapkan pada tiket berdasarkan tingkat keparahan insiden.

---

## 3. Arsitektur Sistem Tingkat Tinggi
Sistem diorganisasikan ke dalam enam lapisan arsitektural, masing-masing dengan tanggung jawab yang jelas.

### 3.1 Lapisan Antarmuka Pengguna
**Komponen:** Bot Telegram
**Tanggung Jawab:**
- Menerima laporan insiden dari pegawai Kementan melalui perintah Telegram `/report`
- Mengelola alur percakapan (sambutan, penerimaan laporan, klarifikasi, penyampaian respons)
- Menampilkan rekomendasi mitigasi dan konfirmasi tiket kepada pelapor
- Beroperasi dalam mode webhook (bukan polling) untuk keandalan produksi
**Catatan Desain:**
- Bot menggunakan library `python-telegram-bot`
- Percakapan bersifat stateful melalui manajemen sesi (didukung Redis)
- Input diteruskan ke Lapisan Keamanan sebelum pemrosesan apa pun

### 3.2 Lapisan Keamanan
**Komponen:** Input Sanitizer, Guardrails Engine (NeMo Guardrails), Output Validator, Audit Logger
**Tanggung Jawab:**
- Memvalidasi dan menyanitasi semua input pengguna yang masuk
- Mendeteksi dan memblokir upaya prompt injection (regex + semantik + LLM-as-judge)
- Memindai unggahan file (ClamAV)
- Memvalidasi semua keluaran LLM sebelum pengiriman ke pengguna
- Menyunting PII dari payload yang akan dikirim ke LLM
- Memelihara jejak audit yang komprehensif
- Menerapkan pembatasan laju dan keamanan sesi
**Catatan Desain:**
- Guardrails Engine beroperasi sebagai gerbang wajib, jika gagal atau tidak dapat dijangkau, sistem memblokir input (perilaku fail-closed)
- NeMo Guardrails menyediakan rail input/output berbasis aturan dan berbasis model yang dapat dikonfigurasi

### 3.3 Lapisan Agen
**Komponen:** Agen Orchestrator, Agen Identificator Insiden, Agen Mitigation Advisor, Agen Ticket Manager, Agen Notifier
**Tanggung Jawab:**
- Mengelola alur kerja pra-triase end-to-end melalui orkestrasi mesin state berbasis LangGraph
- Setiap agen membaca dari dan menulis ke dokumen **Incident State** yang terpusat
- Orchestrator mengontrol pengurutan dan pengalihan
**Catatan Desain:**
- Diimplementasikan menggunakan LangGraph dengan node state dan transisi yang eksplisit
- Pola Orchestrator Terpusat (bukan peer-to-peer) untuk kesederhanaan dan auditabilitas
- Setiap agen adalah fungsi/kelas Python yang didaftarkan sebagai node LangGraph

### 3.4 Lapisan Pengetahuan
**Komponen:** Database Vektor (Qdrant), Layanan Embedding (text-embedding-3-small), Dokumen Basis Pengetahuan
**Tanggung Jawab:**
- Menyimpan dokumentasi keamanan siber yang telah di-chunk dan di-embed (NIST SP 800-61, MITRE ATT&CK)
- Menyediakan retrieval hybrid (pencarian vektor semantik + pencarian kata kunci BM25)
- Mendukung pemfilteran metadata berdasarkan sumber dokumen, jenis insiden, dan bagian
- Mengaktifkan Agentic RAG melalui logika retrieval iteratif Mitigation Advisor

### 3.5 Lapisan Data
**Komponen:** PostgreSQL (tiket), Redis (sesi/cache)
**Tanggung Jawab:**
- Menyimpan tiket insiden dengan skema lengkap
- Mengelola state sesi pengguna (konteks percakapan, data sementara)
- Mengantrekan pekerjaan notifikasi asinkron
- Menyimpan log audit

### 3.6 Lapisan Integrasi
**Komponen:** Klien API LLM (OpenAI, untuk sementara pada masa pengembangan menggunakan API Github), Klien API Telegram
**Tanggung Jawab:**
- Mengelola koneksi terotentikasi ke API eksternal
- Mengimplementasikan logika retry, circuit breaker, dan penanganan timeout untuk pemanggilan LLM
- Mengarahkan notifikasi ke grup Telegram tim CSIRT

---

## 4. Desain Arsitektur Multi-Agent
Sistem menggunakan pola **Orchestrator Terpusat** yang diimplementasikan dalam LangGraph, di mana agen supervisor (Orchestrator) mengelola objek Incident State bersama dan memanggil agen spesialis secara berurutan.
### 4.1 Incident State (Objek Data Bersama)
Incident State adalah dictionary Python (TypedDict dalam LangGraph) yang mengakumulasi data seiring setiap agen memproses laporan. Ini berfungsi sebagai sumber kebenaran tunggal untuk seluruh alur kerja.

```python
class IncidentState(TypedDict):
    # Input
    raw_input: str                    # Input mentah dari pengguna
    sanitized_input: str              # Input yang telah disanitasi
    reporter_id: str                  # ID Telegram pengguna
    reporter_name: str                # Nama pelapor
    reporter_contact: str             # Kontak pelapor
    timestamp_received: str           # Waktu penerimaan laporan
    session_id: str                   # ID sesi

    # Orchestrator
    intent: str                       # "report_incident" | "query_status" | "general_help"
    requires_clarification: bool      # Apakah perlu klarifikasi
    clarification_message: str        # Pesan klarifikasi jika diperlukan

    # Identificator
    incident_type: str                # Jenis insiden terklasifikasi
    severity: str                     # Tingkat keparahan
    confidence_score: float           # Skor kepercayaan klasifikasi
    classification_reasoning: str     # Penjelasan keputusan klasifikasi

    # Mitigation Advisor
    retrieved_chunks: list[dict]      # Potongan dokumen yang diambil
    mitigation_recommendation: str    # Rekomendasi mitigasi yang dihasilkan
    citations: list[dict]             # Daftar sitasi ke dokumen sumber
    rag_confidence: float             # Skor kepercayaan RAG

    # Ticket Manager
    ticket_id: str                    # ID tiket unik (TICKET-YYYY-NNNN)
    ticket_status: str                # "PENDING_REVIEW"
    escalation_level: str             # Tingkat eskalasi

    # Notifier
    notification_sent: bool           # Status pengiriman notifikasi
    notification_recipients: list[str] # Daftar penerima notifikasi
    notification_timestamp: str       # Waktu pengiriman notifikasi

    # Metadata
    processing_errors: list[str]      # Daftar error selama pemrosesan
    agent_trace: list[dict]           # Log terurut eksekusi agen
```

### 4.2 Agen Orchestrator
**Tanggung Jawab:**
- Menerima input yang telah divalidasi dari Lapisan Keamanan
- Mengklasifikasikan intent pengguna: laporan insiden, permintaan status tiket, atau bantuan umum
- Menginisialisasi Incident State
- Mengelola pemanggilan agen secara berurutan: Identificator → Mitigation Advisor → Ticket Manager → Notifier
- Menangani loop klarifikasi jika laporan ambigu (misalnya, terlalu samar, kurang konteks)
- Menangkap dan mencatat error dari agen downstream; memicu perilaku fallback

**Input:** Pesan pengguna yang telah disanitasi, konteks sesi
**Output:** Incident State yang telah diisi (diteruskan ke agen berikutnya), atau permintaan klarifikasi (kembali ke pengguna)
**Kebijakan:**
- Jika kepercayaan klasifikasi intent di bawah 0,6, minta pengguna untuk klarifikasi
- Maksimum 2 putaran klarifikasi sebelum eskalasi ke operator manusia
- Jika agen downstream mana pun gagal, catat error dan kembalikan pesan kegagalan yang sopan kepada pengguna
**Penanganan Kegagalan:**
- Timeout pada klasifikasi intent → default ke "report_incident" dan tandai untuk peninjauan
- Exception pada agen downstream → isi `processing_errors` dalam Incident State, lewati agen yang gagal, lanjutkan dengan agen yang tersisa, dan tandai tiket untuk peninjauan manual

### 4.3 Agen Identificator Insiden

**Tanggung Jawab:**
- Mengklasifikasikan insiden ke dalam salah satu jenis yang telah ditentukan: Phishing, Malware, Ransomware, Web Defacement, DDoS, Akses Tidak Sah, Kebocoran Data, Lainnya
- Menilai tingkat keparahan: Kritis, Tinggi, Sedang, Rendah, Informasional
- Menghasilkan skor kepercayaan untuk klasifikasi
- Menggunakan few-shot prompting dengan contoh representatif untuk setiap jenis insiden

**Input:** `sanitized_input` dari Incident State
**Output:** Memperbarui `incident_type`, `severity`, `confidence_score`, `classification_reasoning` dalam Incident State
**Kebijakan:**
- Hanya memberikan label dari set yang telah ditentukan — tidak pernah membuat kategori baru
- Jika kepercayaan di bawah 0,7, menandai klasifikasi sebagai tentatif dan menandai untuk peninjauan manusia
- Memberikan penalaran untuk klasifikasi (output chain-of-thought) untuk auditabilitas
**Penanganan Kegagalan:**
- Timeout LLM → coba ulang sekali dengan exponential backoff, lalu klasifikasikan sebagai "Lainnya" dengan keparahan "Sedang" dan tandai untuk peninjauan
- Format output tidak valid → error parsing dicatat, klasifikasi default diterapkan

### 4.4 Agen Mitigation Advisor

**Tanggung Jawab:**
- Merumuskan kueri retrieval berdasarkan jenis insiden yang diklasifikasikan dan laporan asli
- Menjalankan retrieval hybrid (semantik + kata kunci) terhadap database vektor
- Melakukan re-ranking potongan yang diambil menggunakan model cross-encoder
- Merangkai potongan top-k yang relevan ke dalam konteks RAG
- Menghasilkan rekomendasi mitigasi terstruktur yang berbasis konteks yang diambil
- Memastikan setiap pernyataan rekomendasi memiliki sitasi yang dapat ditelusuri ke dokumen sumber
**Input:** `incident_type`, `severity`, `sanitized_input` dari Incident State
**Output:** Memperbarui `retrieved_chunks`, `mitigation_recommendation`, `citations`, `rag_confidence` dalam Incident State
**Kebijakan:**
- Setiap pernyataan mitigasi harus didukung oleh setidaknya satu potongan yang diambil (generasi dengan sitasi dipaksakan)
- Jika tidak ditemukan dokumen yang relevan (retrieval mengembalikan hasil kosong atau di bawah ambang relevansi), agen mengembalikan pesan yang menyatakan bahwa panduan SOP tidak ditemukan dan merekomendasikan eskalasi langsung ke tim CSIRT
- Output harus dalam Bahasa Indonesia (sesuai dengan bahasa antarmuka pengguna)
- Maksimum 5 langkah mitigasi per rekomendasi untuk menjaga kejelasan
**Penanganan Kegagalan:**
- Database vektor tidak dapat dijangkau → kembalikan pesan fallback: "Sistem tidak dapat mengakses basis pengetahuan. Silakan hubungi tim CSIRT secara langsung."
- Timeout LLM → coba ulang sekali, lalu kembalikan rekomendasi parsial jika ada potongan yang berhasil diambil
- Halusinasi terdeteksi dalam validasi output → hapus klaim yang tidak didukung, tandai untuk peninjauan

### 4.5 Agen Ticket Manager
**Tanggung Jawab:**
- Merangkai semua data dari Incident State ke dalam rekaman tiket terstruktur
- Menghasilkan ID tiket unik (format: `TICKET-YYYY-NNNN`)
- Memvalidasi skema tiket sebelum penyimpanan
- Menyisipkan tiket ke database PostgreSQL
- Menetapkan status tiket awal sebagai `PENDING_REVIEW`
**Input:** Incident State lengkap setelah Identificator dan Mitigation Advisor telah dieksekusi
**Output:** Memperbarui `ticket_id`, `ticket_status`, `escalation_level` dalam Incident State
**Kebijakan:**
- Semua field wajib harus terisi sebelum pembuatan tiket
- Deteksi duplikat: jika laporan dengan konten yang sangat mirip dari pelapor yang sama ada dalam 24 jam terakhir, sistem menandainya sebagai potensi duplikat dan menambahkan ke tiket yang ada alih-alih membuat tiket baru
- Tingkat eskalasi ditetapkan otomatis berdasarkan keparahan: Kritis → Segera, Tinggi → Mendesak, Sedang → Standar, Rendah → Rutin
**Penanganan Kegagalan:**
- Kegagalan koneksi database → coba ulang dengan exponential backoff (maksimum 3 percobaan), lalu antrekan tiket untuk penyisipan nanti dan beritahu pengguna bahwa pembuatan tiket tertunda
- Kegagalan validasi skema → catat error, coba buat tiket parsial dengan data yang tersedia

### 4.6 Agen Notifier
**Tanggung Jawab:**
- Menentukan penerima notifikasi yang sesuai berdasarkan keparahan dan jenis insiden
- Memformat pesan notifikasi (ringkasan insiden, ID tiket, keparahan, rekomendasi utama)
- Mengirim notifikasi ke grup Telegram tim CSIRT
- Mengirim respons konfirmasi kepada pelapor asli
- Menerapkan validasi output (penyuntingan PII, pemeriksaan daftar putih tindakan) sebelum pengiriman
**Input:** Incident State yang telah difinalisasi (termasuk ID tiket)
**Output:** Memperbarui `notification_sent`, `notification_recipients`, `notification_timestamp` dalam Incident State
**Kebijakan:**
- Keparahan Kritis/Tinggi → notifikasi segera dengan @mention ketua CSIRT yang bertugas
- Keparahan Sedang → notifikasi standar ke grup CSIRT
- Keparahan Rendah/Informasional → notifikasi terbundel (ringkasan setiap 4 jam)
- Pembatasan laju: maksimum 50 notifikasi per jam untuk mencegah kelelahan peringatan
- Pesan notifikasi selalu ditinjau oleh Output Validator sebelum pengiriman
**Penanganan Kegagalan:**
- Kegagalan API Telegram → antrekan pesan untuk percobaan ulang (maksimum 3 percobaan), catat kegagalan
- Jika notifikasi tidak dapat dikirim setelah percobaan ulang, perbarui tiket dengan flag `notification_failed`

---

## 5. Alur Kerja Komunikasi Antar Agen

Alur kerja lengkap dari laporan insiden hingga pembuatan tiket mengikuti pipeline sekuensial berbasis state yang dikelola oleh Orchestrator.

### 5.1 Alur Kerja Langkah demi Langkah
**Langkah 1: Pengiriman Laporan**
Pegawai Kementan mengirim laporan insiden dalam bahasa alami ke bot Telegram (contoh: `/report Saya menerima email phishing dari akun yang mengaku CEO, berisi link mencurigakan ke site login palsu.`).

**Langkah 2: Sanitasi Input**
Bot Telegram meneruskan pesan ke Input Sanitizer, yang menghapus konten berbahaya, menormalisasi encoding, dan memeriksa panjang input.

**Langkah 3: Pemeriksaan Guardrails**
Input yang telah disanitasi melewati Guardrails Engine. Engine melakukan pencocokan pola berbasis regex untuk pola injeksi yang diketahui, perbandingan kemiripan semantik terhadap korpus injeksi, dan (untuk kasus perbatasan) evaluasi LLM-as-judge. Jika input ditandai sebagai berbahaya, input diblokir dan dicatat; pengguna menerima pesan error. Jika aman, input dilanjutkan.

**Langkah 4: Inisialisasi Orchestrator**
Agen Orchestrator menerima input yang telah divalidasi, menginisialisasi objek Incident State baru, dan mengklasifikasikan intent pengguna. Untuk laporan insiden, Orchestrator mengisi field input (`raw_input`, `sanitized_input`, metadata pelapor, timestamp) dan memulai pipeline agen. Jika intent ambigu, Orchestrator meminta pengguna untuk klarifikasi (maksimum 2 putaran).

**Langkah 5: Identifikasi Insiden**
Orchestrator memanggil Agen Identificator Insiden. Agen ini menggunakan few-shot prompting untuk mengklasifikasikan jenis insiden (misalnya, "Phishing") dan menilai keparahan (misalnya, "Tinggi"). Agen menulis `incident_type`, `severity`, `confidence_score`, dan `classification_reasoning` ke Incident State. Jika kepercayaan di bawah ambang batas, flag peninjauan ditetapkan.

**Langkah 6: Retrieval dan Generasi Mitigasi**
Orchestrator memanggil Agen Mitigation Advisor. Agen ini merumuskan kueri retrieval (misalnya, "langkah mitigasi respons phishing email"), menjalankan pencarian hybrid terhadap database vektor Qdrant, melakukan re-ranking hasil dengan cross-encoder, merangkai 5 potongan teratas ke dalam jendela konteks, dan meminta GPT-4o untuk menghasilkan rekomendasi mitigasi terstruktur dengan sitasi. Agen menulis `retrieved_chunks`, `mitigation_recommendation`, `citations`, dan `rag_confidence` ke Incident State.

**Langkah 7: Validasi Output**
Output Validator memeriksa mitigasi yang dihasilkan untuk integritas sitasi (semua klaim merujuk potongan sumber), indikator halusinasi, kebocoran PII, dan kepatuhan daftar putih tindakan. Jika validasi gagal, output dikoreksi (klaim yang tidak didukung dihapus) atau tiket ditandai untuk peninjauan manusia wajib.

**Langkah 8: Pembuatan Tiket**
Orchestrator memanggil Agen Ticket Manager. Agen ini merangkai Incident State lengkap ke dalam tiket terstruktur, menghasilkan ID tiket unik, memvalidasi skema, dan menyimpan tiket ke PostgreSQL dengan status `PENDING_REVIEW`. Agen menulis `ticket_id`, `ticket_status`, dan `escalation_level` ke Incident State.

**Langkah 9: Pengiriman Notifikasi**
Orchestrator memanggil Agen Notifier. Agen ini memformat pesan notifikasi (termasuk ID tiket, jenis insiden, keparahan, dan ringkasan rekomendasi mitigasi), menentukan penerima berdasarkan aturan routing keparahan/jenis, mengirim notifikasi ke grup Telegram CSIRT, dan mengirim pesan konfirmasi ke pelapor.

**Langkah 10: Penyelesaian**
Orchestrator memverifikasi bahwa semua langkah agen telah selesai (atau telah di-degrade secara sopan jika terjadi kegagalan), menambahkan entri akhir ke `agent_trace`, dan menandai alur kerja sebagai selesai. Pelapor menerima pesan seperti:

> ✅ Laporan Anda telah diterima.  
> **Tiket:** TICKET-2026-0047  
> **Jenis Insiden:** Phishing (Kepercayaan: 92%)  
> **Tingkat Keparahan:** Tinggi  
> Tim Keamanan Siber telah diberitahu dan akan menindaklanjuti.

### 5.2 Mesin State LangGraph

```
[MULAI] → [sanitasi_input] → [pemeriksaan_guardrails]
    → (diblokir) → [kirim_respons_error] → [SELESAI]
    → (aman) → [inisialisasi_orchestrator]
        → (perlu_klarifikasi) → [minta_klarifikasi] → [inisialisasi_orchestrator]
        → (laporan_insiden) → [identificator_insiden]
            → [mitigation_advisor] → [validasi_output]
                → (valid) → [ticket_manager] → [notifier] → [kirim_respons] → [SELESAI]
                → (tidak_valid) → [tandai_untuk_peninjauan] → [ticket_manager] → [notifier] → [kirim_respons] → [SELESAI]
        → (kueri_status) → [pencarian_tiket] → [kirim_respons] → [SELESAI]
        → (bantuan_umum) → [kirim_info_bantuan] → [SELESAI]
```

---

## 6. Desain Pipeline RAG
### 6.1 Ingesti Dokumen
**Dokumen Sumber:**
- NIST SP 800-61 Rev. 2 (Panduan Penanganan Insiden Keamanan Komputer)
- MITRE ATT&CK Framework (teknik, taktik, mitigasi yang relevan dengan 8 jenis insiden)
- Pedoman keamanan siber umum

**Pipeline Preprocessing:**
1. Konversi format: File PDF dan DOCX dikonversi ke Markdown menggunakan `pypandoc` atau `markdownify`
2. Ekstraksi metadata: Judul, versi, tanggal, penulis, dan hierarki bagian diekstrak dan disimpan bersama setiap dokumen
3. OCR: PDF yang dipindai diproses dengan Tesseract OCR sebelum konversi
4. Pembersihan: Header, footer, nomor halaman, dan watermark dihapus
5. Deteksi bahasa: Dokumen ditandai sebagai Bahasa Indonesia atau Inggris untuk pemrosesan downstream

### 6.2 Strategi Chunking Dokumen
Sistem menggunakan **semantic chunking** dengan konfigurasi berikut:

- **Metode utama:** Pemisahan karakter rekursif dengan batas yang sadar hierarki (pisah pada header bagian terlebih dahulu, lalu paragraf, lalu kalimat)
- **Ukuran chunk target:** 500–800 token (dioptimalkan untuk jendela kinerja model embedding)
- **Overlap:** 100 token antara chunk yang berdekatan untuk menjaga kontinuitas konteks
- **Metadata per chunk:** `doc_id`, `doc_title`, `section_header`, `page_number`, `incident_types` (daftar jenis insiden yang relevan, ditandai secara manual atau semi-otomatis), `source_framework` ("NIST" | "MITRE" | "Umum")

### 6.3 Pembuatan Embedding
- **Model:** `text-embedding-3-small` (OpenAI) — dipilih untuk efisiensi biaya dan kinerja multibahasa yang kuat
- **Dimensionalitas:** 1536
- **Pemrosesan batch:** Dokumen di-embed dalam batch 100 chunk untuk mengelola batas laju API
- **Cache embedding:** Embedding yang dihasilkan di-cache secara lokal untuk menghindari pemanggilan API berulang selama re-indexing

### 6.4 Desain Database Vektor
- **Database:** Qdrant (self-hosted)
- **Jenis indeks:** HNSW (Hierarchical Navigable Small World) untuk pencarian nearest neighbor yang cepat
- **Struktur koleksi:** Koleksi tunggal `cybersecurity_knowledge` dengan field payload untuk pemfilteran metadata
- **Filter metadata:** `source_framework`, `incident_type`, `language`, `doc_version`

### 6.5 Strategi Retrieval (Pencarian Hybrid)
Mitigation Advisor menggunakan pendekatan retrieval hybrid yang menggabungkan dua sinyal:
**Pencarian Semantik (Kemiripan Vektor):**
- Kueri di-embed menggunakan model embedding yang sama
- Pencarian kemiripan kosinus terhadap koleksi Qdrant
- Mengembalikan 20 kandidat teratas

**Pencarian Kata Kunci (BM25):**
- Kueri juga dicari menggunakan BM25 terhadap indeks kata kunci (dikelola di Qdrant atau indeks Elasticsearch/Tantivy paralel)
- Mengembalikan 20 kandidat teratas

**Reciprocal Rank Fusion (RRF):**
- Dua set hasil digabungkan menggunakan penilaian RRF: `RRF(d) = Σ 1/(k + rank(d))` di mana `k = 60`
- Pemfilteran metadata diterapkan: jika jenis insiden diketahui, chunk yang ditandai dengan jenis insiden tersebut diberi bobot lebih
- Daftar gabungan dipangkas menjadi 20 kandidat teratas untuk re-ranking

### 6.6 Re-Ranking
- **Model:** Re-ranker cross-encoder (misalnya, `bge-reranker-v2-m3` atau `ms-marco-MiniLM-L-12-v2`)
- **Proses:** 20 kandidat teratas dari RRF dinilai oleh cross-encoder, yang mengevaluasi relevansi kueri-chunk dengan perhatian dua arah penuh
- **Ambang batas:** Chunk dengan skor re-ranker di bawah 0,5 dibuang
- **Output:** 5 chunk teratas dipilih sebagai konteks retrieval akhir

### 6.7 Generasi Berbasis Konteks (Grounded Generation)

5 chunk teratas dirangkai ke dalam prompt RAG terstruktur:

```
Sistem: Anda adalah penasihat respons insiden keamanan siber untuk organisasi
pemerintah Indonesia. Hasilkan rekomendasi mitigasi berdasarkan HANYA pada
dokumen referensi yang disediakan. Setiap rekomendasi harus menyitasi dokumen
sumber. Jika dokumen tidak mengandung panduan yang relevan, nyatakan secara
eksplisit. Jawab dalam Bahasa Indonesia.

Dokumen Konteks:
[Chunk 1: {metadata} — {konten}]
[Chunk 2: {metadata} — {konten}]
...

Laporan Insiden: {sanitized_input}
Jenis Insiden: {incident_type}
Tingkat Keparahan: {severity}

Hasilkan rekomendasi mitigasi terstruktur dengan sitasi.
```

LLM (GPT-4o) menghasilkan respons, yang kemudian di-parse untuk mengekstrak langkah-langkah mitigasi individu dan sitasi terkait.

### 6.8 Agentic RAG
Mitigation Advisor mengimplementasikan **Agentic RAG** — yang berarti agen dapat membuat keputusan retrieval secara iteratif alih-alih melakukan satu kali retrieval:

1. **Retrieval Awal:** Agen melakukan retrieval pertama dengan kueri yang diturunkan dari klasifikasi insiden
2. **Pemeriksaan Kecukupan:** Agen mengevaluasi apakah chunk yang diambil cukup mencakup jenis insiden dan keparahannya. Jika cakupan tidak memadai (misalnya, chunk yang diambil terlalu umum atau tidak relevan), agen merumuskan ulang kueri dan melakukan retrieval kedua dengan istilah yang lebih spesifik
3. **Ekspansi Kueri:** Jika kueri awal menghasilkan hasil relevansi rendah, agen dapat memperluas kueri dengan sinonim, ID teknik MITRE ATT&CK, atau nomor bagian NIST
4. **Iterasi maksimum:** 3 kali retrieval untuk mencegah loop tak terbatas
5. **Agregasi:** Hasil dari semua kali retrieval digabungkan dan di-re-rank sebelum perangkaian konteks akhir

Pendekatan iteratif ini meningkatkan keandalan dengan memastikan sistem mengadaptasi strategi pencariannya berdasarkan kualitas retrieval, bukan secara membabi buta menghasilkan dari apa pun yang dikembalikan pencarian pertama.

---

## 7. Arsitektur Basis Pengetahuan
### 7.1 Korpus Dokumen
Basis pengetahuan diorganisasikan ke dalam tiga tingkat:

**Tingkat 1 — Referensi Utama (Standar Otoritatif):**
- NIST SP 800-61: Prosedur penanganan insiden, kerangka klasifikasi, tindakan respons
- MITRE ATT&CK: Pemetaan taktik-teknik untuk setiap jenis insiden, entri mitigasi (seri M), strategi deteksi

**Tingkat 2 — Panduan Operasional (SOP):**
- Pedoman Umum
- Matriks eskalasi dan direktori kontak (dianonimisasi untuk basis pengetahuan)


### 7.2 Organisasi Pengetahuan
Dokumen diindeks dengan skema metadata terstruktur yang memungkinkan pemfilteran presisi selama retrieval:

```json
{
  "doc_id": "nist-800-61-rev2",
  "doc_title": "Computer Security Incident Handling Guide",
  "source_framework": "NIST",
  "version": "Rev. 2",
  "publication_date": "2012-08",
  "language": "en",
  "sections": [
    {
      "section_id": "3.2.4",
      "section_title": "Incident Analysis",
      "incident_types": ["phishing", "malware", "ransomware", "general"],
      "chunks": ["chunk_001", "chunk_002", ...]
    }
  ]
}
```

### 7.3 Integrasi MITRE ATT&CK
Basis pengetahuan menyertakan data MITRE ATT&CK yang distrukturkan berdasarkan:
- **Taktik** (Initial Access, Execution, Persistence, dll.) yang dipetakan ke jenis insiden
- **Teknik** (misalnya, T1566 — Phishing, T1486 — Data Encrypted for Impact) dengan deskripsi
- **Mitigasi** (entri seri M, misalnya, M1054 — Software Configuration) yang ditautkan ke setiap teknik
Pemetaan ini memungkinkan Mitigation Advisor untuk mendasarkan rekomendasinya tidak hanya pada SOP umum tetapi juga pada mitigasi ATT&CK yang spesifik, meningkatkan spesifisitas dan kemampuan untuk ditindaklanjuti.

### 7.4 Kontrol Versi dan Strategi Pembaruan
- Dokumen basis pengetahuan diversi menggunakan field metadata `doc_version`
- Ketika dokumen diperbarui, chunk versi lama dihapus secara soft (ditandai tidak aktif) dan chunk baru di-embed dan diindeks
- Changelog dipelihara untuk melacak dokumen mana yang diperbarui, kapan, dan oleh siapa
- Re-indexing dipicu secara manual atau melalui pekerjaan terjadwal (misalnya, siklus peninjauan bulanan)
- Sistem mencatat versi dokumen mana yang digunakan untuk setiap tiket, memastikan ketertelusuran penuh

---

## 8. Arsitektur Keamanan
### 8.1 Guardrails Engine
Guardrails Engine diimplementasikan menggunakan **NeMo Guardrails** dengan konfigurasi rail kustom:

**Input Rails:**
- `check_prompt_injection`: Memblokir upaya prompt injection yang terdeteksi
- `check_topic_relevance`: Memastikan input terkait dengan pelaporan insiden keamanan siber (menolak pesan di luar topik)
- `check_input_length`: Menerapkan panjang input maksimum
- `check_encoding`: Mendeteksi upaya obfuskasi (encoding base64, hex dalam pesan)

**Output Rails:**
- `check_hallucination`: Memverifikasi konsistensi output dengan konteks yang diambil
- `check_citation_presence`: Memastikan rekomendasi mitigasi memiliki sitasi
- `check_pii_leakage`: Memindai output untuk paparan PII yang tidak disengaja
- `check_action_whitelist`: Memastikan tindakan yang direkomendasikan dari set yang disetujui

### 8.2 Deteksi Prompt Injection (Detail)
Sistem mengimplementasikan pendekatan defense-in-depth:
| Lapisan | Metode | Latensi | Cakupan |
|---------|--------|---------|---------|
| L1: Regex | Pencocokan pola terhadap string injeksi yang diketahui | <5ms | Pola yang diketahui |
| L2: Embedding | Kemiripan kosinus terhadap korpus injeksi (ambang: 0,85) | ~50ms | Varian semantik |
| L3: LLM Judge | Model sekunder mengevaluasi intent | ~500ms | Serangan baru |
| L4: Struktural | Isolasi input berbasis delimiter dalam prompt | 0ms | Konteks injeksi |

Semua lapisan berjalan secara berurutan. Deteksi positif pada lapisan mana pun memblokir input. L3 (LLM Judge) dipanggil hanya untuk input yang lolos L1 dan L2 tetapi memiliki skor perbatasan.

### 8.3 Pemfilteran Input Berbahaya
Selain prompt injection, sistem memfilter untuk:
- **Pola SQL injection** untuk berjaga-jaga jika input chatbot secara tidak sengaja diteruskan ke kueri database (defense in depth)
- **Payload XSS** (tag script HTML, atribut event handler)
- **Upaya path traversal** (`../`, `%2e%2e/`)
- **Pola command injection** (`;`, `|`, `&&`, backticks)

### 8.4 Penyuntingan Data Sensitif
Pipeline penyuntingan PII menggunakan pola regex dan model named entity recognition untuk mendeteksi dan menyamarkan:
- Nomor Induk Kependudukan (NIK, NIP) Indonesia
- email
- Nomor telepon
- Alamat IP (IPv4 & IPv6)
- Hostname dan URL internal
- Nomor kartu kredit
- Kata sandi atau kredensial yang disebutkan dalam laporan

Penyuntingan diterapkan **sebelum** pemanggilan API LLM apa pun dan bersifat reversibel untuk tiket internal (pemetaan disimpan dalam sesi dan disertakan dalam rekaman database akhir).

### 8.5 Sanitasi Unggahan File
Jika unggahan file didukung (misalnya, tangkapan layar email phishing):
- Validasi jenis file (daftar putih: PNG, JPG, PDF saja)
- Batas ukuran file (maksimum 10MB)
- Verifikasi tipe MIME (pemeriksaan magic number, bukan hanya ekstensi)
- Pemindaian virus dengan ClamAV
- File disimpan di direktori terisolasi dengan akses terbatas
- File tidak pernah dikirim ke API LLM — hanya metadata atau konten teks (jika diekstrak) yang disertakan

### 8.6 Pencegahan Penyalahgunaan Model
- **Anggaran token per sesi:** Maksimum 10.000 token per percakapan untuk mencegah serangan pengurasan token
- **Pembatasan laju:** Maksimum 10 pemanggilan LLM per pengguna per jam
- **Deteksi anomali:** Input yang sangat panjang, pengiriman berulang yang cepat, atau pola yang menunjukkan penyalahgunaan otomatis ditandai dan diblokir sementara
- **Pemantauan biaya:** Pengeluaran API LLM harian dipantau dengan peringatan jika ambang batas terlampaui

---

## 9. Model Data dan Struktur Tiket
### 9.1 Skema Tiket Insiden

```sql
CREATE TABLE incident_tickets (
    ticket_id           VARCHAR(20) PRIMARY KEY,      -- TICKET-YYYY-NNNN
    reporter_id         VARCHAR(50) NOT NULL,          -- ID pengguna Telegram atau ID internal
    reporter_name       VARCHAR(100),                  -- Nama pelapor
    reporter_contact    VARCHAR(100),                  -- Email atau telepon
    reporter_department VARCHAR(100),                  -- Departemen/unit kerja

    incident_type       VARCHAR(30) NOT NULL,          -- Enum: jenis yang telah ditentukan
    severity            VARCHAR(20) NOT NULL,          -- Kritis/Tinggi/Sedang/Rendah/Info
    confidence_score    DECIMAL(4,3),                  -- 0.000 - 1.000

    description_raw     TEXT NOT NULL,                 -- Teks laporan asli
    description_sanitized TEXT NOT NULL,               -- Versi yang telah dibersihkan

    evidence_files      JSONB,                         -- Array metadata file
    evidence_urls       JSONB,                         -- Array URL terkait

    mitigation_recommendation TEXT,                    -- Rekomendasi yang dihasilkan
    citations           JSONB,                         -- Array objek sitasi
    rag_confidence      DECIMAL(4,3),                  -- Skor kepercayaan RAG

    status              VARCHAR(30) DEFAULT 'PENDING_REVIEW',  -- Status tiket
    escalation_level    VARCHAR(20),                   -- Segera/Mendesak/Standar/Rutin
    assigned_to         VARCHAR(100),                  -- Analis CSIRT (ditetapkan manusia)

    created_at          TIMESTAMP DEFAULT NOW(),       -- Waktu pembuatan
    updated_at          TIMESTAMP DEFAULT NOW(),       -- Waktu pembaruan terakhir
    reviewed_at         TIMESTAMP,                     -- Waktu peninjauan manusia
    resolved_at         TIMESTAMP,                     -- Waktu insiden diselesaikan
    closed_at           TIMESTAMP,                     -- Waktu tiket ditutup

    classification_reasoning TEXT,                     -- Jejak penalaran AI
    agent_trace         JSONB,                         -- Log eksekusi agen lengkap
    notification_status VARCHAR(20),                   -- sent/failed/pending
    is_duplicate        BOOLEAN DEFAULT FALSE,         -- Apakah duplikat
    parent_ticket_id    VARCHAR(20),                   -- Jika duplikat, tautan ke asli

    created_by          VARCHAR(50) DEFAULT 'SYSTEM',
    modified_by         VARCHAR(50)
);

CREATE INDEX idx_tickets_status ON incident_tickets(status);
CREATE INDEX idx_tickets_severity ON incident_tickets(severity);
CREATE INDEX idx_tickets_type ON incident_tickets(incident_type);
CREATE INDEX idx_tickets_created ON incident_tickets(created_at);
CREATE INDEX idx_tickets_reporter ON incident_tickets(reporter_id);
```

### 9.2 Struktur Objek Sitasi
```json
{
  "citation_id": "cit_001",
  "source_doc": "NIST SP 800-61 Rev. 2",
  "section": "3.4.1 - Strategi Penahanan",
  "chunk_id": "chunk_042",
  "relevance_score": 0.91,
  "text_excerpt": "100 karakter pertama dari bagian yang disitasi..."
}
```

### 9.3 Skema Log Audit

```sql
CREATE TABLE audit_logs (
    log_id          BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMP DEFAULT NOW(),
    event_type      VARCHAR(50) NOT NULL,              -- Jenis peristiwa
    session_id      VARCHAR(50),                       -- ID sesi
    user_id         VARCHAR(50),                       -- ID pengguna
    agent_name      VARCHAR(30),                       -- Nama agen
    action          VARCHAR(100),                      -- Tindakan yang dilakukan
    input_summary   TEXT,                              -- Input yang dipotong/disunting
    output_summary  TEXT,                              -- Output yang dipotong/disunting
    guardrail_result VARCHAR(20),                      -- lolos/blokir/tandai
    llm_model       VARCHAR(50),                       -- Model LLM yang digunakan
    token_count     INTEGER,                           -- Jumlah token
    latency_ms      INTEGER,                           -- Latensi dalam milidetik
    error_message   TEXT,                              -- Pesan error jika ada
    metadata        JSONB                              -- Metadata tambahan
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_session ON audit_logs(session_id);
CREATE INDEX idx_audit_event ON audit_logs(event_type);
```

---

## 10. Arsitektur Implementasi

### 10.1 Technology Stack

| Komponen | Teknologi | Justifikasi |
|----------|-----------|-------------|
| **Bahasa Pemrograman** | Python 3.11+ | Ekosistem ML/NLP yang kaya, native LangChain/LangGraph |
| **Framework Backend** | FastAPI | Dukungan async, dokumentasi OpenAPI otomatis, performa tinggi |
| **Orkestrasi Agen** | LangGraph | Manajemen state eksplisit, alur kontrol berbasis graf, siap produksi |
| **Penyedia LLM** | OpenAI GPT-4o (via API) (untuk sementara pada masa pengembangan menggunakan API Github) | Kemampuan multibahasa kuat, dukungan structured output |
| **Model Embedding** | text-embedding-3-small (OpenAI) | Efisien biaya, kinerja multibahasa baik |
| **Database Vektor** | Qdrant (self-hosted) | Pemfilteran metadata sangat baik, dapat di-host sendiri untuk kedaulatan data |
| **Database Relasional** | PostgreSQL 16 | Keandalan terbukti, dukungan JSONB, indexing kuat |
| **Cache / Penyimpanan Sesi** | Redis | Penyimpanan in-memory cepat, dukungan TTL sesi |
| **Antarmuka Chatbot** | python-telegram-bot | Library matang, dukungan webhook |
| **Guardrails** | NeMo Guardrails | Dibangun khusus untuk keamanan LLM, rail yang dapat dikonfigurasi |
| **Re-Ranker** | bge-reranker-v2-m3 atau cross-encoder | Re-ranking lintas bahasa yang kuat |
| **Pemantauan** | LangSmith (tracing LLM) + logging dasar | Observabilitas LLM, debugging prompt |
| **Kontainerisasi** | Docker + Docker Compose | Deployment yang dapat direproduksi, isolasi layanan |

### 10.2 Struktur Proyek

```
cybersec-helpdesk/
├── app/
│   ├── main.py                  # Entry point aplikasi FastAPI
│   ├── config.py                # Manajemen konfigurasi
│   ├── agents/
│   │   ├── orchestrator.py      # Agen Orchestrator
│   │   ├── identifier.py        # Agen Identificator Insiden
│   │   ├── mitigation.py        # Agen Mitigation Advisor
│   │   ├── ticket_manager.py    # Agen Ticket Manager
│   │   ├── notifier.py          # Agen Notifikasi
│   │   └── graph.py             # Definisi mesin state LangGraph
│   ├── security/
│   │   ├── guardrails.py        # Integrasi NeMo Guardrails
│   │   ├── sanitizer.py         # Sanitasi input
│   │   ├── validator.py         # Validasi output
│   │   ├── pii_redactor.py      # Deteksi dan penyuntingan PII
│   │   └── prompt_injection.py  # Lapisan deteksi injeksi
│   ├── rag/
│   │   ├── ingestion.py         # Pipeline ingesti dokumen
│   │   ├── chunker.py           # Logika chunking
│   │   ├── embedder.py          # Pembuatan embedding
│   │   ├── retriever.py         # Logika retrieval hybrid
│   │   └── reranker.py          # Re-ranking cross-encoder
│   ├── database/
│   │   ├── models.py            # Model SQLAlchemy
│   │   ├── repository.py        # Operasi database
│   │   └── migrations/          # Migrasi Alembic
│   ├── telegram/
│   │   ├── bot.py               # Handler bot Telegram
│   │   └── templates.py         # Template pesan
│   └── utils/
│       ├── logger.py            # Logging terstruktur
│       └── audit.py             # Manajemen jejak audit
├── knowledge_base/
│   ├── documents/               # Dokumen sumber (PDF, DOCX, CSV, JSON, dan lainnya)
│   └── metadata/                # File metadata dokumen
├── config/
│   ├── guardrails/              # File konfigurasi NeMo Guardrails
│   └── prompts/                 # Template prompt agen
├── tests/
│   ├── test_agents/             # Unit test agen
│   ├── test_security/           # Unit test keamanan
│   ├── test_rag/                # Unit test RAG
│   └── evaluation/              # Skrip dan skenario evaluasi
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 11. Rencana Evaluasi

### 11.1 Task Completion Rate (TCR)

**Definisi:** Proporsi kasus uji di mana sistem berhasil menyelesaikan alur kerja pra-triase penuh tanpa memerlukan intervensi manusia.

**Formula:**

> TCR = (Jumlah kasus yang berhasil diselesaikan secara otomatis / Jumlah total kasus uji) × 100%

**Kriteria penyelesaian — suatu kasus dianggap "selesai" ketika sistem berhasil:**
1. Mengidentifikasi jenis insiden
2. Menghasilkan rekomendasi mitigasi yang didukung oleh dokumen sumber
3. Membuat tiket terstruktur dalam database
4. Mengirim notifikasi kepada tim CSIRT dan pelapor

**Target:** TCR ≥ 80%

**Dataset Uji:** 30–50 skenario pengujian yang mencakup semua 8 jenis insiden, termasuk:
- Laporan yang jelas dan terdeskripsi dengan baik (diharapkan: tingkat penyelesaian tinggi)
- Laporan ambigu atau tidak lengkap (menguji penanganan klarifikasi)
- Kasus tepi (beberapa jenis insiden dalam satu laporan, laporan non-keamanan siber)
- Input adversarial (upaya prompt injection — diharapkan: diblokir, tidak dihitung dalam penyebut TCR)

### 11.2 Metrik Evaluasi RAG (Framework RAGAS)

**Context Relevance (Relevansi Konteks):** Mengukur apakah chunk yang diambil relevan dengan kueri.

> Context Relevance = (Jumlah kalimat relevan dalam konteks yang diambil) / (Total kalimat dalam konteks yang diambil)

**Target:** ≥ 0,75

**Answer Relevance (Relevansi Jawaban):** Mengukur apakah jawaban yang dihasilkan menjawab pertanyaan asli.

> Answer Relevance = mean(cosine_similarity(jawaban_yang_dihasilkan, pertanyaan_sintetis))

**Target:** ≥ 0,80

**Faithfulness (Kesetiaan):** Mengukur apakah jawaban yang dihasilkan konsisten secara faktual dengan konteks yang diambil (yaitu, tanpa halusinasi).

> Faithfulness = (Jumlah klaim yang didukung konteks) / (Total klaim dalam jawaban)

**Target:** ≥ 0,85

**Dataset Evaluasi:** 20–30 pasangan pertanyaan-jawaban yang disusun dari dokumen basis pengetahuan, diverifikasi oleh pakar domain, mencakup setiap jenis insiden.

### 11.3 System Usability Scale (SUS)

**Proses:**
1. Deploy sistem di lingkungan uji terkontrol yang dapat diakses oleh 10–20 pegawai Kementan
2. Setiap peserta menguji sistem dengan 3–5 skenario pelaporan insiden yang representatif
3. Setelah pengujian, peserta mengisi kuesioner SUS standar (10 item, skala Likert 5 poin)

**Penilaian SUS:** Jumlah kontribusi item individual × 2,5 = skor SUS (0–100)

**Target:** Skor SUS ≥ 68 (rata-rata industri untuk usabilitas "dapat diterima")

### 11.4 Contoh Skenario Evaluasi

| # | Skenario | Jenis yang Diharapkan | Keparahan yang Diharapkan |
|---|----------|----------------------|--------------------------|
| 1 | "Saya menerima email dari CEO meminta transfer dana segera dengan link login palsu" | Phishing | Tinggi |
| 2 | "Komputer saya tiba-tiba lambat dan ada popup meminta pembayaran Bitcoin untuk buka file" | Ransomware | Kritis |
| 3 | "Website kementan.go.id tampilan halamannya berubah dan ada tulisan diretas" | Web Defacement | Tinggi |
| 4 | "Saya tidak bisa akses server internal sejak tadi pagi, sepertinya ada serangan DDoS" | DDoS | Tinggi |
| 5 | "Ada program aneh terinstall di laptop saya tanpa sepengetahuan saya" | Malware | Sedang |
| 6 | "Ada orang yang mengakses akun email saya dari lokasi yang tidak dikenal" | Akses Tidak Sah | Tinggi |
| 7 | "Ada yang aneh di komputer saya" (ambigu) | Memerlukan Klarifikasi | — |
| 8 | "Cuaca hari ini cerah" (di luar topik) | Ditolak (di luar topik) | — |

### 11.5 Evaluasi Pakar

Selain metrik otomatis, tim CSIRT mengevaluasi sampel keluaran sistem pada skala Likert (1–5) untuk:
- **Relevansi:** Apakah rekomendasi menjawab insiden spesifik?
- **Akurasi:** Apakah rekomendasi benar secara faktual sesuai SOP/NIST/ATT&CK?
- **Kelengkapan:** Apakah semua langkah respons yang diperlukan disertakan?
- **Kejelasan:** Apakah rekomendasi mudah dipahami oleh pelapor?
- **Kemampuan Ditindaklanjuti:** Apakah pelapor dapat mengikuti langkah-langkah tersebut segera?

---

## 12. Arsitektur Deployment

### 12.1 Deployment Prototipe (Pengembangan/Demo)

Untuk fase prototipe, sistem di-deploy pada satu VPS atau server cloud menggunakan Docker Compose:

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
    depends_on: [db, redis, qdrant]

  telegram-bot:
    build: .
    command: python -m app.telegram.bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - API_URL=http://api:8000

  db:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      - POSTGRES_DB=helpdesk
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine

  qdrant:
    image: qdrant/qdrant:latest
    volumes: ["qdrant_data:/qdrant/storage"]

volumes:
  pgdata:
  qdrant_data:
```

**Rekomendasi VPS:** DigitalOcean atau Hetzner dengan 4 vCPU, 8GB RAM, 80GB SSD cukup untuk beban kerja prototipe.

### 12.2 Topologi Jaringan

```
Internet
    │
    ├── API Telegram ←→ [Layanan Bot Telegram]
    │                         │
    │                    [Jaringan Internal]
    │                         │
    │              ┌──────────┴──────────┐
    │              │    Server FastAPI     │
    │              │    (port 8000)        │
    │              └──────────┬──────────┘
    │                         │
    │         ┌───────────────┼───────────────┐
    │         │               │               │
    │    [PostgreSQL]     [Qdrant]        [Redis]
    │    (port 5432)     (port 6333)     (port 6379)
    │
    └── API OpenAI ←→ [Klien LLM dalam FastAPI]
```

### 12.3 Pertimbangan Keamanan untuk Deployment

- Semua layanan berkomunikasi melalui jaringan Docker internal (tidak terekspos ke internet)
- Hanya endpoint webhook bot Telegram dan (opsional) server API yang terekspos
- HTTPS diterapkan untuk semua endpoint yang menghadap eksternal (gunakan reverse proxy nginx dengan Let's Encrypt)
- Port database tidak pernah terekspos secara eksternal
- Variabel lingkungan (kunci API, token, kata sandi) dikelola melalui file `.env` (pengembangan) atau secrets manager (produksi)
- Pembaruan keamanan rutin untuk semua image Docker

### 12.4 Logging dan Pemantauan

- Logging JSON terstruktur ke stdout (dikumpulkan oleh Docker logging driver)
- Integrasi LangSmith untuk tracing pemanggilan LLM dan debugging prompt
- Metrik aplikasi diekspos melalui endpoint `/metrics` (kompatibel Prometheus)
- Peringatan: notifikasi email atau Telegram sederhana jika tingkat error melebihi ambang batas

### 12.5 Kontrol Akses

- Akses bot Telegram dibatasi oleh daftar putih ID pengguna (hanya pegawai Kementan terdaftar)
- Endpoint API admin (jika ada) dilindungi oleh kunci API + daftar putih IP
- Akses database dibatasi ke akun layanan dengan izin least-privilege
- Log audit bersifat read-only untuk semua akun kecuali administrator audit

---

## Lampiran A: Template Prompt Agen

### A.1 Orchestrator — Prompt Klasifikasi Intent

```
Anda adalah pengklasifikasi intent untuk helpdesk keamanan siber.
Klasifikasikan pesan pengguna ke dalam salah satu dari tiga kategori:
1. "report_incident" — pengguna melaporkan insiden keamanan siber
2. "query_status" — pengguna menanyakan status tiket yang ada
3. "general_help" — pengguna meminta bantuan atau informasi umum

Pesan pengguna: <user_report>{sanitized_input}</user_report>

Jawab dalam JSON: {"intent": "...", "confidence": 0.XX, "needs_clarification": true/false, "clarification_question": "..."}
```

### A.2 Identificator Insiden — Prompt Klasifikasi

```
Anda adalah pengklasifikasi insiden keamanan siber. Berdasarkan laporan insiden
di bawah ini, tentukan jenis insiden dan tingkat keparahannya.

Jenis insiden yang diizinkan: Phishing, Malware, Ransomware, Web Defacement, DDoS,
Akses Tidak Sah, Kebocoran Data, Lainnya

Tingkat keparahan: Kritis, Tinggi, Sedang, Rendah, Informasional

[Contoh few-shot disediakan di sini untuk setiap jenis...]

Laporan insiden: <user_report>{sanitized_input}</user_report>

Jawab dalam JSON:
{
  "incident_type": "...",
  "severity": "...",
  "confidence_score": 0.XX,
  "reasoning": "Penjelasan singkat keputusan klasifikasi"
}
```

### A.3 Mitigation Advisor — Prompt Generasi RAG

```
Anda adalah penasihat respons insiden keamanan siber untuk organisasi pemerintah
Indonesia (Kementerian Pertanian). Hasilkan rekomendasi mitigasi awal berdasarkan
HANYA pada dokumen referensi yang disediakan di bawah ini.

Aturan:
1. Setiap rekomendasi harus menyitasi bagian dokumen sumber
2. Jika dokumen tidak mengandung panduan yang relevan, nyatakan secara eksplisit
3. Maksimum 5 langkah mitigasi yang dapat ditindaklanjuti
4. Jawab dalam Bahasa Indonesia
5. Jangan merekomendasikan tindakan yang memerlukan akses sistem langsung atau eksekusi teknis

Dokumen Referensi:
{assembled_context_with_metadata}

Jenis Insiden: {incident_type}
Tingkat Keparahan: {severity}
Laporan: <user_report>{sanitized_input}</user_report>

Jawab dalam JSON:
{
  "mitigation_steps": [
    {"step": 1, "action": "...", "source": "NIST SP 800-61, Bagian 3.4.1"},
    ...
  ],
  "general_guidance": "...",
  "escalation_note": "..."
}
```

---

## Lampiran B: Catatan Keputusan Utama

| Keputusan | Pilihan | Alasan |
|-----------|---------|--------|
| Pola orkestrasi agen | Orchestrator Terpusat (LangGraph) | Debugging lebih sederhana, alur kontrol jelas, auditabilitas lebih mudah untuk evaluasi penelitian |
| RAG vs fine-tuning | RAG | Tidak ada dataset berlabel besar yang tersedia; SOP sering berubah; perlu ketertelusuran sitasi |
| Database vektor | Qdrant (self-hosted) | Kedaulatan data (konteks pemerintah), pemfilteran metadata sangat baik, SDK Python yang baik |
| Penyedia LLM | OpenAI GPT-4o | Kinerja multibahasa terbaik, dukungan structured output; Azure OpenAI dipertimbangkan untuk produksi |
| Retrieval hybrid | Semantik + BM25 + RRF | Menangkap makna semantik dan kecocokan kata kunci yang tepat (misalnya, ID teknik MITRE) |
| Framework guardrails | NeMo Guardrails | Dibangun khusus untuk keamanan LLM, dapat dikonfigurasi, terdokumentasi dengan baik |
| Perilaku kegagalan | Fail-closed | Jika guardrails atau validasi gagal, blokir input/output alih-alih meneruskannya |
| Default status tiket | PENDING_REVIEW | Memastikan pengawasan manusia sebelum tindakan respons apa pun |

---

## Lampiran C: Daftar Risiko

| Risiko | Dampak | Kemungkinan | Mitigasi |
|--------|--------|-------------|----------|
| Prompt injection melewati guardrails | Tinggi | Sedang | Pertahanan multi-lapisan, pengujian adversarial rutin |
| Halusinasi LLM dalam saran mitigasi | Tinggi | Sedang | Generasi dengan sitasi dipaksakan, validasi faithfulness |
| Downtime API OpenAI | Sedang | Rendah | Logika retry, pesan degradasi yang sopan |
| Basis pengetahuan menjadi usang | Sedang | Sedang | Siklus peninjauan terjadwal, kontrol versi |
| Data sensitif bocor ke API LLM | Kritis | Rendah | Penyuntingan PII sebelum pemanggilan API, audit logging |
| Sistem kewalahan oleh volume | Rendah | Rendah | Pembatasan laju, pemrosesan berbasis antrian |
| Pengguna mengirim laporan palsu/menyesatkan | Sedang | Sedang | Peninjauan manusia untuk semua tiket, jejak audit |

---

*Akhir Masterplan Teknis*