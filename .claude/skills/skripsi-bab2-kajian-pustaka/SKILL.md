---
name: skripsi-bab2-kajian-pustaka
description: Use when drafting, revising, or reviewing Bab II (Kajian Pustaka / Landasan Teori) of an Indonesian undergraduate thesis (skripsi/Tugas Akhir), especially Poltek SSN format. Covers Landasan Teori, Penelitian Terkait, Kerangka Konseptual.
---

# Skripsi Bab II — Kajian Pustaka

## Tujuan Bab
Membangun **fondasi konseptual** agar Bab III (metodologi) dan Bab IV (hasil) bisa dipahami tanpa pembaca harus riset sendiri. Bab II **bukan kopian Wikipedia** — hanya definisi dan konsep yang benar-benar dipakai di bab selanjutnya.

## Aturan Emas
**Setiap subbab di Bab II harus dirujuk minimal sekali di Bab III atau Bab IV.** Jika teori tidak dipakai, hapus. Panjang ≠ kualitas.

## Struktur Wajib (Format Poltek SSN)

```
II.1 LANDASAN TEORI
    II.1.1 [Lokus/Domain]           — konteks instansi
    II.1.2 [Konsep inti 1]          — teknologi utama (mis. Chatbot)
    II.1.3 [Konsep inti 2]          — (mis. Large Language Model)
    II.1.4 [Konsep inti 3]          — (mis. RAG)
    II.1.5 [Metode/framework]       — (mis. SDLC Waterfall)
    II.1.x [Metrik evaluasi]        — (mis. RAGAS, DeepEval)
II.2 PENELITIAN TERKAIT             — 5–10 karya prior, disusun kronologis/tematik
II.3 KERANGKA KONSEPTUAL            — diagram alur pikir penelitian
```

## Landasan Teori — Cara Menulis Satu Subbab

Pola 3 paragraf per konsep:

1. **Definisi + sitasi** — 1–2 kalimat definisi dari sumber primer. Kutip definisi asli, jangan parafrase longgar.
2. **Karakteristik / cara kerja** — bagaimana teknologi itu bekerja pada level yang relevan untuk proyek. Sisipkan gambar/tabel jika perlu (Gambar 2.x, Tabel 2.x).
3. **Relevansi untuk penelitian** — satu kalimat penutup yang menghubungkan ke proyek. Contoh: "Dalam penelitian ini, RAG digunakan untuk..."

**Kedalaman**: cukup agar pembaca non-spesialis paham, tidak sampai tutorial. Hindari pseudocode kecuali sangat kritis.

## Penelitian Terkait — Format

Dua pendekatan, pilih salah satu konsisten:

### Opsi A: Narasi Tematik
Kelompokkan per tema. Contoh: "Penelitian tentang evaluasi RAG", "Penelitian tentang pengamanan LLM". Di setiap tema, bandingkan 2–4 studi.

### Opsi B: Tabel Ringkasan + Narasi
Tabel dengan kolom: **Penulis (Tahun)**, **Metode**, **Dataset**, **Hasil**, **Gap/Perbedaan dengan Penelitian Ini**. Setelah tabel, tulis paragraf yang menjelaskan **posisi penelitian Anda** terhadap prior work.

**Wajib**: eksplisit nyatakan **apa yang berbeda** dari penelitian Anda. Frasa standar:
> "Berbeda dengan penelitian [X], penelitian ini menerapkan ... pada konteks ..."

## Kerangka Konseptual

Diagram alur (boleh flowchart sederhana) yang menunjukkan:
- Input penelitian (data, masalah)
- Proses/metode (teori yang sudah dijelaskan di II.1)
- Output (hasil yang diharapkan — tidak menyebut angka)

Dilengkapi 1–2 paragraf penjelasan yang **merujuk nomor gambar**: "Gambar 2.x menunjukkan kerangka konseptual penelitian..."

## Konvensi Gaya

- **Tense**: present untuk teori umum ("RAG merupakan..."), past untuk hasil penelitian terdahulu ("Penelitian [5] menemukan...").
- **Sitasi**: setiap definisi, angka, klaim non-trivial **wajib** bersitasi. Paragraf tanpa sitasi sama dengan opini.
- **Istilah teknis**: italic pada penggunaan pertama + akronim dalam kurung. Setelah itu pakai akronim saja.
- **Gambar & tabel**: wajib caption ("Gambar 2.1 Arsitektur RAG [12]"), dirujuk di narasi sebelum muncul.
- **Hindari**: kalimat generik ("Teknologi ini sangat penting di era modern"), tinggal copy dari satu sumber, menterjemahkan Wikipedia.

## Bank Frasa

| Fungsi | Frasa |
|---|---|
| Definisi | "X merupakan...", "Menurut [n], X didefinisikan sebagai..." |
| Cara kerja | "Secara umum, X bekerja dengan cara...", "Proses tersebut terdiri dari tiga tahap..." |
| Rujukan studi | "Penelitian [n] menunjukkan bahwa...", "Pada [n], penulis mengusulkan..." |
| Kontras studi | "Berbeda dengan [n], [m] menggunakan...", "Meskipun demikian..." |
| Ringkas gap | "Dari uraian tersebut, terdapat gap penelitian dalam hal..." |
| Posisi penelitian | "Penelitian ini mengisi gap tersebut dengan..." |

## Kualitas Sumber

**Prioritas (tinggi → rendah)**:
1. Jurnal peer-reviewed terindeks (Scopus/WoS/SINTA)
2. Prosiding konferensi top (IEEE, ACM, NeurIPS, ACL)
3. Technical report resmi (NIST, Google Research, Anthropic, OpenAI)
4. Buku teks standar
5. Dokumen resmi pemerintah/standar (ISO, BSSN, Perka)
6. Preprint arXiv (**dengan verifikasi**)

**Hindari**: Medium, blog pribadi, Wikipedia, berita pop, LinkedIn posts, ChatGPT output.

**Target jumlah sitasi Bab II**: 25–50 sitasi unik untuk skripsi S1. Minimum 60% dari 5 tahun terakhir untuk bidang AI/keamanan siber.

## Checklist

- [ ] Setiap subbab II.1 dirujuk di Bab III atau IV (tidak ada teori "yatim")
- [ ] Penelitian terkait 5–10 karya, dengan tabel atau narasi tematik
- [ ] Ada pernyataan eksplisit posisi penelitian vs prior work
- [ ] Kerangka konseptual berupa diagram + paragraf penjelasan
- [ ] Semua gambar/tabel punya nomor, caption, dan dirujuk di narasi
- [ ] Tidak ada paragraf tanpa sitasi
- [ ] Sumber didominasi jurnal/konferensi peer-reviewed, bukan blog

## Kesalahan Umum

| Kesalahan | Perbaikan |
|---|---|
| Bab II terlalu panjang, banyak teori tidak dipakai | Hapus subbab yang tidak dirujuk di Bab III/IV |
| Definisi diparafrase longgar hingga maknanya bergeser | Kutip langsung dari sumber primer |
| Penelitian terkait hanya mendaftar ("A melakukan X. B melakukan Y.") | Bandingkan dan posisikan penelitian Anda |
| Kerangka konseptual hanya teks, tanpa diagram | Tambahkan flowchart alur pikir |
| Teori dikutip dari textbook lama (>10 tahun) untuk topik AI/LLM | Ganti dengan survey/paper terbaru |
| Akronim dipakai sebelum didefinisikan | Definisikan pada kemunculan pertama |

## Referensi Silang
- Skill `skripsi-bab1-pendahuluan` — untuk konvensi umum (sitasi, gaya).
- Skill `skripsi-bab3-metodologi` — teori di Bab II harus support Bab III.
- Folder `TA/` — lihat Bab II dari TA Rizal Abie untuk contoh subbab Chatbot/LLM/RAG/SmoothLLM.
