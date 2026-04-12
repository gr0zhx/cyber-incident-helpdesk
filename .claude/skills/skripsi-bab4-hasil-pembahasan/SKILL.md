---
name: skripsi-bab4-hasil-pembahasan
description: Use when drafting, revising, or reviewing Bab IV (Hasil Penelitian dan Pembahasan) of an Indonesian undergraduate thesis (skripsi/Tugas Akhir), especially Poltek SSN format. Covers pengembangan sistem, pengujian, evaluasi metrik, analisis hasil, pembahasan, dan deployment.
---

# Skripsi Bab IV — Hasil Penelitian dan Pembahasan

## Tujuan Bab
Menunjukkan **apa yang dihasilkan** penelitian dan **menjelaskan artinya**. Bab IV adalah tempat penguji menilai apakah rumusan masalah terjawab. Bab ini juga biasanya bab **terpanjang** (40–60% bobot skripsi).

## Aturan Emas
**Struktur Bab IV harus mencerminkan struktur Bab III dan menjawab setiap butir Rumusan Masalah Bab I.** Jika rumusan masalah ada 3 butir, penguji akan mencari 3 bagian pembahasan di Bab IV.

## Struktur Wajib (Format Poltek SSN)

Dua pendekatan umum, pilih salah satu:

### Pola A: Per Tahap SDLC (mirror Bab III)
```
IV.1 PENGEMBANGAN SISTEM
    IV.1.1 Analysis            — hasil analisis kebutuhan + pemilihan
    IV.1.2 Design              — arsitektur final, skema data
    IV.1.3 Implementation      — screenshot modul, integrasi
    IV.1.4 Testing             — hasil tiap jenis pengujian
IV.2 DEPLOYMENT / PEMBAHASAN AKHIR
```

### Pola B: Per Rumusan Masalah
```
IV.1 HASIL PENGEMBANGAN SISTEM
IV.2 HASIL PENGUJIAN [RM a]     — kualitas interaksi
IV.3 HASIL PENGUJIAN [RM b]     — benchmarking LLM
IV.4 HASIL PENGUJIAN [RM c]     — efektivitas pengamanan
```

**Rekomendasi**: Pola A jika metode SDLC-driven (paling umum di Poltek SSN), Pola B jika fokus pada eksperimen komparatif.

## Pola Paragraf "Hasil → Analisis"

Setiap hasil pengujian harus menunjukkan **dua lapisan**:

### Lapisan 1: Hasil Objektif (What)
- Kalimat pembuka yang merujuk tabel/gambar.
- Angka konkret (nilai metrik, persentase, jumlah).
- Tidak ada interpretasi di paragraf ini.

Contoh:
> "Tabel 4.1 menunjukkan hasil evaluasi framework RAGAS pada tiga LLM. Dari 9 pertanyaan yang diuji, 8 pertanyaan lolos threshold pada metrik Faithfulness dengan nilai rata-rata 0.776."

### Lapisan 2: Analisis (Why / So What)
- **Mengapa** hasilnya begitu. Hubungkan ke teori di Bab II.
- **Kapan** gagal. Analisis kasus edge / outlier.
- **Implikasi** untuk rumusan masalah.

Contoh:
> "Pertanyaan 1 gagal lolos threshold karena *retrieved context* tidak mengandung informasi yang relevan dengan *actual output*, sesuai dengan definisi Faithfulness pada [n]. Hal tersebut menunjukkan kelemahan *hybrid search* pada pertanyaan dengan terminologi yang tidak eksplisit di dokumen sumber."

**Aturan**: jangan hanya "lapor angka" — setiap tabel harus diikuti 1–2 paragraf analisis.

## Penyajian Tabel dan Gambar

- **Tabel**: untuk data numerik presisi (nilai metrik per pertanyaan, skor per responden).
- **Gambar/Grafik**: untuk tren, perbandingan, distribusi. Pakai bar chart untuk perbandingan, line chart untuk tren waktu, box plot untuk distribusi skor.
- **Penomoran**: "Tabel 4.1", "Gambar 4.1" — numbering per bab.
- **Caption**: singkat deskriptif, **di atas** tabel, **di bawah** gambar (konvensi Poltek SSN umum — cek panduan terbaru).
- **Rujukan**: setiap tabel/gambar **wajib** dirujuk di narasi sebelum muncul ("Tabel 4.1 menunjukkan...").
- **Satuan & threshold**: sertakan di header atau caption.
- **Highlight**: baris lolos/gagal bisa ditandai kolom "Threshold: TRUE/FALSE" atau warna (grayscale untuk cetak).

## Menulis Bagian Pengujian

Template 4 komponen per jenis pengujian:

1. **Deskripsi pengujian** — 1 paragraf mengingatkan apa yang diuji & metriknya (rujuk balik Bab III).
2. **Penyajian data** — tabel/gambar dengan hasil mentah.
3. **Analisis** — pola, outlier, justifikasi.
4. **Kesimpulan parsial** — kalimat yang secara eksplisit menjawab sub-pertanyaan rumusan masalah.

Contoh kalimat penutup:
> "Berdasarkan hasil tersebut, rumusan masalah (b) dapat dijawab bahwa LLM gpt-4.1 memiliki performa terbaik pada evaluasi framework DeepEval dan RAGAS dengan skor rerata tertinggi pada tiga metrik utama."

## Konvensi Gaya

- **Tense**: past tense untuk tindakan yang sudah dilakukan ("pengujian dilakukan dengan..."), present untuk interpretasi ("hasil ini menunjukkan...").
- **Passive voice** untuk prosedur, **active** boleh untuk interpretasi ("penelitian ini mendemonstrasikan...").
- **Angka**: pakai presisi konsisten (mis. 3 desimal untuk skor metrik: 0.776). Jangan campur 0.7 dan 0.7760.
- **Persen**: "85 persen" atau "85%" — pilih satu, konsisten se-skripsi.
- **Sitasi**: tetap dibutuhkan saat merujuk definisi metrik, metode dari Bab II, atau perbandingan dengan penelitian terkait.

## Bank Frasa

| Fungsi | Frasa |
|---|---|
| Rujuk tabel | "Tabel 4.x menunjukkan...", "Sebagaimana ditampilkan pada Tabel 4.x..." |
| Rujuk gambar | "Gambar 4.x menggambarkan...", "Pada Gambar 4.x terlihat..." |
| Pola hasil | "Dari hasil tersebut dapat diamati bahwa...", "Berdasarkan data pada..." |
| Kontras | "Meskipun demikian, pertanyaan X menunjukkan...", "Akan tetapi, pada kasus..." |
| Kausal | "Hal tersebut disebabkan oleh...", "Kegagalan tersebut dapat dijelaskan dengan..." |
| Komparasi ke prior | "Temuan ini sejalan dengan [n] yang menemukan...", "Berbeda dengan [n]..." |
| Keterbatasan | "Keterbatasan hasil ini terletak pada...", "Penelitian ini belum menguji..." |
| Jawaban rumusan | "Dengan demikian, rumusan masalah (a) terjawab..." |

## Apa yang HARUS Ada di Bab IV

- [ ] Screenshot atau mockup sistem akhir (minimal 2)
- [ ] Diagram arsitektur final (jika berbeda dari desain di Bab III)
- [ ] Hasil lengkap semua pengujian yang dijanjikan di Bab III
- [ ] Tabel metrik dengan threshold TRUE/FALSE
- [ ] Minimal 1 grafik visual (bar/line) untuk perbandingan
- [ ] Analisis outlier / kasus gagal
- [ ] Pembahasan yang menghubungkan kembali ke Bab II (teori) dan prior work
- [ ] **Jawaban eksplisit untuk setiap butir rumusan masalah**

## Apa yang DILARANG di Bab IV

- ❌ **Tidak boleh** ada teori baru yang belum dibahas di Bab II. Jika butuh, balik edit Bab II.
- ❌ **Tidak boleh** ada metrik/metode baru yang belum didefinisikan di Bab III.
- ❌ **Tidak boleh** hanya melaporkan angka tanpa interpretasi.
- ❌ **Tidak boleh** klaim berlebihan ("sistem ini terbukti lebih baik dari semua LLM") — gunakan bahasa hati-hati.
- ❌ **Tidak boleh** kode/source panjang di badan bab — pindahkan ke lampiran.
- ❌ **Tidak boleh** sembunyikan hasil gagal — analisis kegagalan justru nilai tambah.

## Pembahasan Kegagalan / Limitasi

Bab IV yang jujur lebih kuat dari Bab IV yang sempurna. Pola:

1. Nyatakan kegagalan konkret (pertanyaan N gagal, metrik X di bawah threshold).
2. Jelaskan **akar penyebab** berdasarkan observasi (bukan tebakan).
3. Rujuk teori/prior work yang mendukung penjelasan.
4. Tawarkan **mitigasi** atau **saran perbaikan** (yang akan dibawa ke Bab V).

## Bahasa Hati-hati (Hedging)

Hindari bahasa absolut — gunakan qualifier ilmiah:

| Jangan | Ganti dengan |
|---|---|
| "terbukti lebih baik" | "menunjukkan performa yang lebih tinggi pada kondisi X" |
| "tidak bisa ditembus" | "mampu memitigasi Y persen serangan pada dataset Z" |
| "selalu berhasil" | "berhasil pada N dari M kasus uji" |
| "revolusioner" | (jangan dipakai di skripsi) |

## Kesalahan Umum

| Kesalahan | Perbaikan |
|---|---|
| Hanya deskripsi sistem, tidak ada hasil pengujian | Pastikan setiap jenis pengujian di Bab III muncul di Bab IV |
| Tabel tanpa narasi analisis | Tambah 1–2 paragraf pembahasan per tabel |
| Rumusan masalah tidak terjawab eksplisit | Tambahkan paragraf penutup tiap subbab yang menjawab RM |
| Kasus gagal disembunyikan | Tampilkan + analisis akar penyebab |
| Pakai teori baru yang tak ada di Bab II | Balik edit Bab II |
| Screenshot buram / low-res | Ganti dengan tangkapan layar langsung (minimum 1080p) |
| Numbering tabel/gambar tidak konsisten | Pakai fitur caption otomatis Word/LaTeX |
| Tidak bandingkan dengan prior work | Sertakan kalimat "sejalan/berbeda dengan [n]..." |

## Checklist Akhir

- [ ] Struktur mirror Bab III (Pola A) atau per RM (Pola B)
- [ ] Setiap rumusan masalah dijawab eksplisit dengan kalimat penutup
- [ ] Semua tabel/gambar dirujuk di narasi
- [ ] Semua tabel diikuti paragraf analisis
- [ ] Ada minimal 1 grafik visual komparatif
- [ ] Kasus gagal dianalisis (tidak disembunyikan)
- [ ] Tidak ada teori baru yang tak ada di Bab II
- [ ] Tidak ada metrik baru yang tak didefinisikan di Bab III
- [ ] Bahasa hedging (tidak klaim absolut)
- [ ] Deployment / integrasi akhir dibahas (jika ada)
- [ ] Kode panjang dipindahkan ke lampiran

## Referensi Silang
- `skripsi-bab1-pendahuluan` — cek rumusan masalah sebelum menulis untuk memastikan semua terjawab.
- `skripsi-bab3-metodologi` — struktur & metrik harus sinkron.
- Folder `TA/` — lihat Bab IV TA Rizal Abie (Tabel 4.1, 4.2, 4.3) untuk contoh penyajian hasil benchmarking RAG.
- Proyek Pusdatin Kementan: Bab IV kemungkinan mencakup (1) hasil pengembangan multi-agent LangGraph, (2) evaluasi klasifikasi insiden, (3) evaluasi RAG mitigasi (Context Relevance ≥ 0.75, Answer Relevance ≥ 0.80, Faithfulness ≥ 0.85), (4) hasil SUS (≥ 68), (5) Task Completion Rate (≥ 80%).
