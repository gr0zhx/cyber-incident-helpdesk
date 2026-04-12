---
name: skripsi-bab3-metodologi
description: Use when drafting, revising, or reviewing Bab III (Metodologi Penelitian) of an Indonesian undergraduate thesis (skripsi/Tugas Akhir), especially Poltek SSN format. Covers Objek Penelitian, Jenis Penelitian, Desain Penelitian dengan SDLC (Waterfall/Agile/dll).
---

# Skripsi Bab III — Metodologi Penelitian

## Tujuan Bab
Menjelaskan **bagaimana** penelitian dikerjakan sehingga penelitian lain bisa mereproduksi prosesnya. Bab III adalah **kontrak**: apa yang ditulis di sini akan ditagih di Bab IV.

## Aturan Emas
**Setiap tahap di Bab III harus menghasilkan sesuatu yang dilaporkan di Bab IV.** Jika sebuah tahap tidak punya output yang dibahas di Bab IV, hapus atau gabung.

## Struktur Wajib (Format Poltek SSN)

```
III.1 OBJEK PENELITIAN     — apa yang diteliti + lokus
III.2 JENIS PENELITIAN     — kualitatif/kuantitatif/campuran + justifikasi
III.3 DESAIN PENELITIAN    — tahapan SDLC (Waterfall paling umum)
    III.3.1 Planning
    III.3.2 Analysis
    III.3.3 Design
    III.3.4 Implementation
    III.3.5 Testing
    III.3.6 Maintenance    (opsional untuk skripsi)
```

Subbab bisa disesuaikan jika pakai metode lain (Prototyping, DSR, CRISP-DM, Agile). Apa pun metodenya, **cantumkan gambar diagram metode + sitasi sumbernya** (contoh "Gambar 3.1 SDLC Waterfall [58]").

## III.1 Objek Penelitian

2–4 kalimat yang menjawab:
- **Lokus**: instansi/lokasi apa. (Contoh: Pusdatin Kementan)
- **Objek**: sistem/proses/fenomena yang dikembangkan atau diteliti.
- **Fokus**: aspek apa yang jadi perhatian utama (performa, ketergunaan, keamanan).

## III.2 Jenis Penelitian

Pilih salah satu + **justifikasi**:

| Jenis | Kapan dipakai |
|---|---|
| Kualitatif | Wawancara, analisis teks, eksplorasi konsep |
| Kuantitatif | Pengukuran metrik, uji statistik, benchmarking |
| Campuran (mixed-method) | Kombinasi — paling umum untuk skripsi rekayasa |

Tulis 2 paragraf: paragraf 1 menyatakan jenis, paragraf 2 menjelaskan **bagian mana** dari penelitian yang pakai pendekatan mana. Contoh: "Pendekatan kualitatif digunakan untuk evaluasi ketergunaan via wawancara. Pendekatan kuantitatif digunakan untuk benchmarking metrik RAG."

## III.3 Desain Penelitian — Template Waterfall

Tiap sub-subbab SDLC tulis **3 komponen**:

1. **Apa yang dilakukan** di tahap ini (aktivitas konkret)
2. **Input** — dari mana data/material berasal
3. **Output / deliverable** — apa yang dihasilkan untuk tahap berikut

### III.3.1 Planning
- Identifikasi masalah, wawancara stakeholder, penetapan scope.
- **Sebutkan metode pengambilan data** (wawancara semi-terstruktur, observasi, studi dokumen) + instrumen.

### III.3.2 Analysis
- Analisis kebutuhan fungsional & non-fungsional.
- **Daftar kebutuhan sistem** sebagai list a/b/c (boleh list di sini).
- Justifikasi pemilihan teknologi/metode (LLM mana, framework mana, **mengapa**).

### III.3.3 Design
- Arsitektur sistem (diagram) — **Gambar 3.x**.
- Flow diagram, ERD/skema data jika relevan.
- Prompt template / algoritma utama (bisa ditaruh di lampiran jika panjang).

### III.3.4 Implementation
- Stack teknologi yang dipakai (Python, FastAPI, dst) + versi.
- Lingkungan pengembangan (OS, spek minimum).
- Tidak perlu tulis kode panjang — cukup deskripsi modul.

### III.3.5 Testing
- **Metode pengujian**: unit, integrasi, fungsional, ketergunaan (CUQ/SUS), keamanan.
- **Dataset pengujian**: sumber + jumlah + justifikasi.
- **Metrik evaluasi**: nama + definisi + threshold. Contoh: "Faithfulness ≥ 0.85 (definisi dari RAGAS [n])".
- **Prosedur**: langkah eksperimen. Bisa pakai list numerik karena ini protokol.

## Konvensi Gaya

- **Tense**: present atau future-in-past — **hindari** "akan dilakukan" (itu untuk proposal, bukan skripsi final). Ganti dengan present: "Tahap ini menjelaskan..." atau "Tahap ini terdiri dari...".
- **Passive voice** dominan: "data dikumpulkan melalui wawancara", bukan "peneliti mengumpulkan data".
- **Reproducibility**: sebutkan versi library, URL sumber data, seed jika acak, hyperparameter LLM (temperature, top-p).
- **Diagram**: wajib punya nomor, caption, sitasi sumber jika adaptasi, dan **dirujuk di narasi sebelum muncul** ("Gambar 3.1 menunjukkan...").

## Bank Frasa

| Fungsi | Frasa |
|---|---|
| Pembuka tahap | "Tahap ini menjelaskan...", "Pada tahap ini..." |
| Input-proses-output | "Berdasarkan hasil tahap sebelumnya...", "Output dari tahap ini digunakan untuk..." |
| Justifikasi pilihan | "Pemilihan X didasarkan pada...", "X dipilih karena..." |
| Prosedur | "Langkah-langkah yang dilakukan meliputi...", "Proses tersebut terdiri dari..." |
| Metrik | "Metrik yang digunakan adalah X yang didefinisikan sebagai... [n]" |
| Pengacuan diagram | "Gambar 3.x menunjukkan alur...", "Tabel 3.x merangkum parameter..." |

## Kebutuhan Reproducibility (Wajib Ditulis)

Checklist apa yang harus ada agar penelitian bisa direplikasi:

- [ ] Daftar kebutuhan sistem (fungsional + non-fungsional)
- [ ] Arsitektur sistem (diagram)
- [ ] Sumber & jumlah data latih/uji
- [ ] Versi semua library utama (`requirements.txt` bisa dilampirkan)
- [ ] Hyperparameter LLM: model, temperature, max tokens, seed
- [ ] Prompt template (boleh di lampiran)
- [ ] Nama & versi framework evaluasi (RAGAS x.y, DeepEval x.y)
- [ ] Threshold tiap metrik + sumbernya
- [ ] Protokol pengujian (jumlah repetisi, dataset, kriteria lolos)

## Kesalahan Umum

| Kesalahan | Perbaikan |
|---|---|
| Pakai "akan" / future tense (meniru proposal) | Ganti ke present tense — Bab III final menggambarkan metode yang **sudah dilakukan** |
| Tahap SDLC dijelaskan generik, tidak spesifik untuk proyek | Tambahkan detail konkret: nama LLM, dataset, library |
| Tidak ada diagram arsitektur | Wajib minimal 1 diagram arsitektur di III.3.3 |
| Threshold metrik muncul tiba-tiba di Bab IV tanpa didefinisikan di Bab III | Definisikan semua metrik + threshold di III.3.5 |
| Daftar kebutuhan bercampur dengan deskripsi naratif | Pakai list a/b/c eksplisit di III.3.2 |
| Prompt template ditulis di Bab III yang jadi sangat panjang | Pindahkan ke Lampiran, rujuk dari Bab III |
| Justifikasi pilihan teknologi hanya "karena populer" | Rujuk data/sumber konkret (tren, benchmark, studi) |

## Kapan Boleh Pakai List (Bullet/Numerik)

Bab III **boleh pakai list**, tidak wajib prosa, untuk:
- Daftar kebutuhan sistem
- Daftar kriteria inklusi/eksklusi data
- Langkah-langkah prosedur pengujian
- Daftar peralatan / lingkungan

Untuk narasi konteks dan justifikasi, **tetap pakai prosa**.

## Checklist

- [ ] Objek & lokus penelitian jelas
- [ ] Jenis penelitian dijustifikasi, bukan hanya dinyatakan
- [ ] Semua tahap SDLC punya input, proses, output
- [ ] Ada diagram arsitektur (Gambar 3.x)
- [ ] Semua metrik & threshold didefinisikan di sini
- [ ] Hyperparameter LLM dicantumkan
- [ ] Tidak ada "akan" / future tense
- [ ] Setiap sub-subbab terhubung ke bagian di Bab IV

## Referensi Silang
- `skripsi-bab2-kajian-pustaka` — teori metode SDLC & metrik harus sudah ada di Bab II.
- `skripsi-bab4-hasil-pembahasan` — hasil di Bab IV harus mengikuti struktur yang sama dengan metode di Bab III.
- Folder `TA/` — lihat Bab III TA Rizal Abie untuk contoh SDLC Waterfall pada proyek chatbot RAG.
- Proyek Pusdatin Kementan: SDLC bisa disesuaikan dengan alur multi-agent LangGraph (Planning → Analysis → Design pipeline → Implementation per-agent → Testing end-to-end).
