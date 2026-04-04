# Kuesioner System Usability Scale (SUS)
## Sistem Helpdesk Keamanan Siber Pusdatin Kementan

**Petunjuk Pengisian:**
Setelah mencoba sistem chatbot helpdesk keamanan siber, mohon berikan penilaian Anda untuk setiap pernyataan di bawah ini.

Skala penilaian: **1 = Sangat Tidak Setuju** hingga **5 = Sangat Setuju**

---

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|----|-----------|---|---|---|---|---|
| 1 | Saya pikir saya ingin sering menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Saya merasa sistem ini terlalu rumit untuk digunakan. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Saya merasa sistem ini mudah digunakan. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Saya memerlukan bantuan dari orang teknis untuk menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Saya merasa berbagai fungsi dalam sistem ini terintegrasi dengan baik. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Saya merasa terlalu banyak ketidakkonsistenan dalam sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Saya bayangkan kebanyakan orang akan cepat belajar menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Saya merasa sistem ini sangat tidak praktis untuk digunakan. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Saya merasa sangat percaya diri menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Saya perlu banyak belajar sebelum bisa menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## Cara Menghitung Skor SUS

**Formula:**
```
Untuk pertanyaan ganjil (1,3,5,7,9): nilai_kontribusi = jawaban - 1
Untuk pertanyaan genap (2,4,6,8,10): nilai_kontribusi = 5 - jawaban
Skor SUS = (jumlah semua nilai_kontribusi) × 2.5
```

**Interpretasi Skor:**
| Skor | Nilai Huruf | Interpretasi |
|------|-------------|--------------|
| ≥ 90.9 | A+ | Terbaik |
| 85–90.9 | A | Sangat Baik |
| 77.5–84.9 | B | Baik |
| 72.5–77.4 | C | Di atas rata-rata |
| 68–72.4 | D | Rata-rata industri |
| 51–67.9 | F | Di bawah rata-rata |
| < 51 | F | Buruk |

**Target sistem ini: ≥ 68 (rata-rata industri)**

---

## Skenario Pengujian untuk Peserta

Berikut 5 skenario yang akan diujikan kepada peserta:

### Skenario 1 — Laporan Phishing
> Anda menerima email dari seseorang yang mengaku sebagai CEO meminta transfer dana segera ke rekening baru. Email tersebut berisi link yang mencurigakan.
>
> **Tugas:** Laporkan insiden ini melalui chatbot helpdesk.

### Skenario 2 — Ransomware
> File-file di komputer Anda tiba-tiba tidak bisa dibuka dan ada pesan yang meminta pembayaran Bitcoin untuk mendapatkan kunci dekripsi.
>
> **Tugas:** Laporkan insiden ini dan ikuti rekomendasi yang diberikan sistem.

### Skenario 3 — Akses Tidak Sah
> Anda mendapat notifikasi bahwa akun email dinas Anda digunakan untuk login dari kota lain padahal Anda sedang di kantor.
>
> **Tugas:** Laporkan insiden ini melalui chatbot dan catat nomor tiket yang diberikan.

### Skenario 4 — Cek Status Tiket
> Setelah melapor kemarin, Anda ingin mengecek status penanganan tiket insiden Anda.
>
> **Tugas:** Gunakan fitur cek status tiket.

### Skenario 5 — Pertanyaan Umum
> Anda ingin tahu apa yang harus dilakukan jika menerima email phishing.
>
> **Tugas:** Tanyakan kepada chatbot cara menangani email phishing.

---

## Panduan Singkat untuk Peserta Uji

1. Buka aplikasi Telegram di HP atau komputer Anda.
2. Cari bot dengan nama **@PusdatinHelpdesk_bot** (atau sesuai nama bot yang diberikan penguji).
3. Mulai dengan mengetik `/start`.
4. Untuk melaporkan insiden, ketik `/report` lalu ikuti instruksi.
5. Untuk melihat panduan, ketik `/help`.
6. Setelah mencoba semua skenario, isi kuesioner SUS di atas.

**Waktu yang disediakan:** 15–20 menit

---

*Dokumen ini merupakan bagian dari evaluasi skripsi: "Sistem Helpdesk Keamanan Siber Multi-Agent Berbasis LLM untuk Pra-Triase Insiden di Pusdatin Kementan"*
