---
name: skripsi-bab1-pendahuluan
description: Use when drafting, revising, or reviewing Bab I (Pendahuluan) of an Indonesian undergraduate thesis (skripsi/Tugas Akhir), especially Poltek SSN format. Covers Latar Belakang, Rumusan Masalah, Pembatasan Masalah, Tujuan & Manfaat, Sistematika Penulisan.
---

# Skripsi Bab I — Pendahuluan

## Tujuan Bab
Menjawab tiga pertanyaan pembaca: **apa masalahnya**, **mengapa penting**, **apa yang akan dilakukan**. Bab I harus membuat penguji percaya bahwa topik Anda layak diteliti sebelum mereka membaca Bab II.

## Struktur Wajib (Format Poltek SSN)

```
I.1 LATAR BELAKANG          (3–6 halaman, paragraf naratif)
I.2 RUMUSAN MASALAH         (a, b, c — pertanyaan penelitian)
I.3 PEMBATASAN MASALAH      (a, b, c — scope/ruang lingkup)
I.4 TUJUAN DAN MANFAAT
    I.4.1 Tujuan            (a, b, c — parallel dgn rumusan)
    I.4.2 Manfaat           (akademis + praktis)
I.5 SISTEMATIKA PENULISAN   (ringkasan Bab I–V)
```

## Latar Belakang: Piramida Terbalik

Tulis dari umum ke spesifik dalam 5 lapisan paragraf, masing-masing dengan sitasi `[n]`:

1. **Konteks domain/lokus** — kondisi umum instansi/bidang (+ regulasi jika relevan).
2. **Tren teknologi/solusi** — teknologi apa yang sedang berkembang untuk menangani konteks tersebut.
3. **Masalah/gap** — kerentanan, kekurangan, atau celah dalam teknologi tersebut. Kutip data kuantitatif ("52 persen dari prompt injection berhasil...").
4. **Solusi/pendekatan** — metode yang Anda pilih dan **mengapa** metode itu, bukan yang lain. Bandingkan singkat vs alternatif.
5. **Pernyataan penelitian** — kalimat "Oleh karena itu, penelitian ini bertujuan untuk..." yang menjembatani ke rumusan masalah.

**Aturan kunci**: setiap klaim non-trivial **harus** punya sitasi. Hindari opini pribadi.

## Konvensi Gaya Bahasa

- **Sudut pandang**: pasif atau impersonal. Gunakan "penelitian ini", "peneliti", atau passive voice — **jangan** "saya"/"kami".
- **Tense**: present untuk fakta umum, past untuk penelitian terdahulu, future **tidak dipakai** (ganti dengan "penelitian ini akan" → "penelitian ini bertujuan untuk").
- **Sitasi**: numerik IEEE `[1]`, `[2]`, ditempatkan setelah klaim sebelum tanda baca.
- **Istilah asing**: italic pada penggunaan pertama (*Retrieval-Augmented Generation*), lalu boleh akronim (RAG).
- **Angka**: angka dengan satuan/persen pakai numerik ("52 persen", "9 pertanyaan"); di awal kalimat dieja.

## Bank Frasa Penghubung

| Fungsi | Frasa |
|---|---|
| Menambah bukti | Selain itu, Di samping itu, Sejalan dengan hal tersebut |
| Kontras | Namun, Di lain sisi, Akan tetapi, Sebaliknya |
| Sebab-akibat | Oleh karena itu, Hal tersebut disebabkan karena, Akibatnya |
| Rujukan | Berdasarkan [n], Mengacu pada, Sebagaimana dinyatakan |
| Penekanan | Terlebih lagi, Bahkan, Khususnya |
| Konklusi | Dengan demikian, Berdasarkan uraian tersebut |

## Rumusan Masalah — Aturan

- Bentuk **pertanyaan**, diawali "Bagaimana...", "Seberapa besar...", "LLM apa yang...".
- **Jumlah 2–4 butir** (idealnya 3). Terlalu banyak = fokus hilang.
- **Testable**: setiap butir harus bisa dijawab oleh hasil di Bab IV.
- **Parallel**: Rumusan a → Tujuan a → Hasil IV.a. Korespondensi satu-satu.

## Pembatasan Masalah — Aturan

- Tulis hal-hal yang **sengaja dikeluarkan** dari scope, bukan hal yang dikerjakan.
- Sebut teknologi/dataset/metode spesifik ("menggunakan dataset AdvBench", "hanya input teks").
- Jangan pakai untuk menyembunyikan kelemahan — penguji akan notice.

## Tujuan dan Manfaat

- **Tujuan**: ubah setiap rumusan jadi pernyataan deklaratif. "Bagaimana X?" → "Mengetahui X".
- **Manfaat akademis**: referensi untuk penelitian lanjutan.
- **Manfaat praktis**: dampak konkret untuk lokus/instansi (Pusdatin Kementan).

## Checklist Sebelum Lanjut ke Bab II

- [ ] Latar belakang punya ≥ 8 sitasi literatur primer
- [ ] Setiap paragraf latar belakang punya transisi ke paragraf berikut
- [ ] Rumusan masalah 2–4 butir, parallel dengan tujuan
- [ ] Pembatasan masalah spesifik (sebut metode/dataset/tools)
- [ ] Tidak ada kata ganti orang pertama ("saya"/"kami")
- [ ] Semua istilah asing italic pada penggunaan pertama
- [ ] Sistematika penulisan menyebut isi tiap bab dalam 2–3 baris

## Kesalahan Umum

| Kesalahan | Perbaikan |
|---|---|
| Latar belakang loncat dari domain langsung ke solusi tanpa jelaskan masalah | Sisipkan paragraf "gap" dengan data kuantitatif bersitasi |
| Rumusan masalah tidak punya jawaban di Bab IV | Cek korespondensi rumusan ↔ hasil sebelum submit |
| Manfaat hanya "menambah wawasan" (generik) | Sebutkan dampak konkret pada lokus spesifik |
| Pembatasan masalah menuliskan apa yang dikerjakan, bukan apa yang dikecualikan | Gunakan frasa "hanya", "tidak mencakup", "dibatasi pada" |
| Pakai sumber tidak kredibel (blog, Medium) | Ganti dengan jurnal/konferensi peer-reviewed |

## Contoh Paragraf Gap (dari TA Rizal, Poltek SSN)

> Namun, permasalahan yang rentan pada chatbot berbasis LLM adalah adanya halusinasi yang dihasilkan pada respons jawaban [9]. Halusinasi muncul disebabkan karena LLM menghasilkan respons yang kurang akurat, tetapi dijelaskan secara fasih sehingga terkesan logis bagi pengguna [9]. Penelitian [11] menyebutkan bahwa halusinasi memiliki isu terhadap beberapa hal, yakni akurasi, kepercayaan, *misinformation*, koheren, *nonsensical*, dan *factually incorrect*. Oleh karenanya, isu utama terkait chatbot berbasis LLM adalah adanya kemungkinan respons yang dihasilkan bersifat halusinatif.

Perhatikan: klaim → sitasi → klaim → sitasi → konklusi paragraf dengan "Oleh karenanya".

## Referensi Silang
- Folder `TA/` berisi 9 skripsi Poltek SSN sebelumnya sebagai contoh gaya.
- Untuk Bab II gunakan skill `skripsi-bab2-kajian-pustaka`.
- Proyek ini: chatbot helpdesk keamanan siber Pusdatin Kementan — sesuaikan lokus & domain di latar belakang.
