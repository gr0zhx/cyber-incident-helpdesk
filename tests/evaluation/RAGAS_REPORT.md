# Laporan Evaluasi RAG Pipeline — RAGAS
**Tanggal:** 31 May 2026  
**Model:** gpt-4o (answer generation) + gpt-4o-mini (RAGAS evaluator)  
**Dataset:** 20 soal (10 NIST SP 800-61 + 10 MITRE ATT&CK)  
**Library:** RAGAS 0.4.3  

---

## 1. Ringkasan Skor

| Metrik | Skor | Target | Status |
|--------|------|--------|--------|
| Faithfulness | 0.4381 | >= 0.8 | Belum Tercapai |
| Answer Relevancy | 0.3261 | >= 0.75 | Belum Tercapai |
| Context Precision | 0.7219 | >= 0.75 | Belum Tercapai |
| Context Recall | 0.6583 | >= 0.8 | Belum Tercapai |

---

## 2. Skor per Dokumen

| Dokumen | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---------|-------------|-----------------|------------------|----------------|
| NIST SP 800-61 (10 soal) | 0.4450 | 0.3323 | 0.6237 | 0.7000 |
| MITRE ATT\&CK (10 soal) | 0.4312 | 0.3199 | 0.8200 | 0.6167 |

---

## 3. Skor per Soal

| ID | Pertanyaan (ringkas) | Faithfulness | Ans. Relevancy | Ctx. Precision | Ctx. Recall | Sumber |
|----|---------------------|-------------|----------------|----------------|-------------|--------|
| QA-001 | Dokumen minimum apa yang wajib ada sebelum insiden sibe... | 0.7857 | 0.5091 | 0.3667 | 0.5000 | NIST |
| QA-002 | Laporan via WhatsApp/japri sering minim detail. Data mi... | 1.0000 | 0.3928 | 1.0000 | 0.5000 | NIST |
| QA-003 | Saat dua insiden datang bersamaan, satu mengganggu laya... | 0.6000 | 0.3105 | 0.0000 | 1.0000 | NIST |
| QA-004 | Saat serangan masih berjalan, tindakan paling aman apa:... | 0.0000 | 0.0000 | 0.8875 | 1.0000 | NIST |
| QA-005 | Akun saya tiba-tiba login sendiri dari perangkat/lokasi... | 0.0714 | 0.5070 | 0.4778 | 1.0000 | NIST |
| QA-006 | Saya klik email mencurigakan, tapi belum tahu ada dampa... | 0.2143 | 0.2976 | 0.5889 | 1.0000 | NIST |
| QA-007 | Komputer jadi lambat, muncul pop-up aneh, dan file suli... | 0.2000 | 0.2380 | 0.9167 | 0.5000 | NIST |
| QA-008 | Kenapa saya diminta jangan hapus email/chat/berkas yang... | 0.4615 | 0.2093 | 1.0000 | 0.5000 | NIST |
| QA-009 | Kalau data kerja saya hilang karena insiden, apakah mas... | 0.5455 | 0.3704 | 0.5833 | 0.5000 | NIST |
| QA-010 | Saya dihubungi oleh pihak yang mengaku dari tim IT dan ... | 0.5714 | 0.4884 | 0.4167 | 0.5000 | NIST |
| QA-011 | Saya menerima email yang mengatasnamakan atasan dengan ... | 0.5455 | 0.3286 | 1.0000 | 0.6667 | MITRE |
| QA-012 | Saya menerima email dengan lampiran invoice dari pengir... | 0.3077 | 0.2070 | 1.0000 | 0.5000 | MITRE |
| QA-013 | File pada shared drive tiba-tiba terenkripsi dan muncul... | 0.2727 | 0.3921 | 0.0000 | 0.2500 | MITRE |
| QA-014 | Halaman utama website berubah tanpa izin dan menampilka... | 0.2143 | 0.4053 | 1.0000 | 0.5000 | MITRE |
| QA-015 | Aplikasi yang terhubung ke internet tiba-tiba dapat dia... | 0.7143 | 0.3752 | 1.0000 | 0.5000 | MITRE |
| QA-016 | Terdapat login berhasil menggunakan akun pegawai, namun... | 0.8571 | 0.3016 | 1.0000 | 0.2500 | MITRE |
| QA-017 | Trafik mendadak meledak sehingga layanan publik drop, a... | 0.2000 | 0.1918 | 0.2000 | 1.0000 | MITRE |
| QA-018 | Saya melihat adanya unggahan dokumen internal ke layana... | 0.1333 | 0.3157 | 1.0000 | 0.5000 | MITRE |
| QA-019 | Saya menemukan file atau skrip yang tidak dikenal muncu... | 0.6667 | 0.3634 | 1.0000 | 1.0000 | MITRE |
| QA-020 | Saya sempat mengunduh dan menjalankan file yang dikirim... | 0.4000 | 0.3187 | 1.0000 | 1.0000 | MITRE |

---

## 4. Definisi Metrik

| Metrik | Definisi |
|--------|----------|
| **Faithfulness** | Sejauh mana jawaban sistem dapat diverifikasi dari context yang diambil (0 = banyak hallucination, 1 = sepenuhnya berdasarkan dokumen) |
| **Answer Relevancy** | Sejauh mana jawaban secara langsung menjawab pertanyaan yang diajukan |
| **Context Precision** | Seberapa baik urutan ranking dokumen yang diambil — dokumen relevan diharapkan ada di posisi atas |
| **Context Recall** | Seberapa lengkap dokumen yang diambil mencakup informasi yang dibutuhkan untuk menjawab |

---

## 5. Catatan Teknis

- **Retriever:** HybridRetriever (semantic search + keyword search, Reciprocal Rank Fusion)
- **Reranker:** Score-based (0.7 × cosine + 0.3 × normalized RRF)
- **Top-k retrieval:** 5 chunks per pertanyaan
- **Knowledge base:** Qdrant collection 
- **Embedding model:** text-embedding-3-small