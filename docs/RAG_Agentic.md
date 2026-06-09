---
# Slide 1 — Mekanisme Agentic RAG

- Tagline: "Agentic RAG untuk rekomendasi mitigasi ber-sitasi dan fail-safe"
- Inti: loop retrieval → rerank → adequacy check → LLM → citation validation → fallback

Speaker notes: Buka dengan motivasi: RAG biasa rentan hallucination; kita tambahkan pemeriksaan sitasi dan loop adequacy.

---
# Slide 2 — Alur Pemrosesan (Ringkas)

- Query Builder: sanitasi input + tambahkan intent/keywords
- Hybrid Retrieval: semantic search + keyword (Qdrant)
- RRF + Rerank: gabungkan ranking, normalisasi RRF
- Adequacy Check (Agentic loop): threshold + query expansion (maks 3 iter)
- Citation Validation: verifikasi 6 metadata fields
- Fallback: fail-safe → arahkan ke CSIRT

Speaker notes: Jangan jelaskan kotak per kotak; tunjuk tiga pembeda utama di slide selanjutnya.

---
# Slide 3 — Hybrid Retrieval (Pembeda)

- Semantic Search (embedding) menangkap makna
- Keyword Search (full-text Qdrant) menangkap istilah teknis
- Merge: Reciprocal Rank Fusion (RRF)
- Parameter penting: `RRF_K = 60`

Speaker notes: Tekankan bahwa kombinasi ini menangani pertanyaan prosedural dan istilah teknis sekaligus.

---
# Slide 4 — Reranking & Scoring (Pembeda)

- Formula (implementasi):

  Score = 0.7 × cosine_similarity
         + 0.3 × (rrf_score / 0.05, diklip 0–1)
         + incident_type_boost (default +0.20)

- Output: `final_score` skala 0–1

Speaker notes: Jelaskan singkat normalisasi RRF (mengapa dibagi 0.05) dan bahwa semua komponen ternormalisasi.

---
# Slide 5 — Adequacy Check (Agentic Loop)

- Threshold default: `RETRIEVAL_SCORE_THRESHOLD = 0.22`
- Max Iteration: 3
- Jika belum memadai → lakukan query expansion berdasarkan `incident_type` → ulang retrieval

Speaker notes: Ini yang membuatnya "agentic" — bisa memperbaiki sendiri konteks sebelum memanggil LLM.

---
# Slide 6 — Citation Validation & Fallback (Pembeda kunci)

- Validasi terhadap 6 metadata fields: `source`, `section`, `doc_title`, `section_header`, `source_framework`, `external_id`
- Jika langkah LLM tidak bisa ditelusuri → hapus langkah tersebut
- Jika semua langkah gagal verifikasi → tidak berikan rekomendasi (fail-safe)

Speaker notes: Tekankan prinsip fail-safe — lebih baik minta bantuan CSIRT daripada salah memberi saran.

---
# Slide 7 — Parameter Ringkas (Bawa ke slide teknis)

- `MAX_ITERATIONS` = 3
- `TOP_K_RETRIEVAL` = 30
- `TOP_K_RERANK` = 5
- `CHUNK_SIZE` = 800, `CHUNK_OVERLAP` = 100
- `EMBEDDING_MODEL` = text-embedding-3-small (dim 1536)
- `RETRIEVAL_SCORE_THRESHOLD` = 0.22

Speaker notes: Sebutkan bahwa semua ini configurable via konstanta/ENV.

---
# Slide 8 — Demo / QA pointers

- Tunjukkan log reranker (nilai `final_score`) untuk satu query nyata
- Tunjukkan contoh JSON output: `mitigation_recommendation`, `citations`, `retrieved_chunks`, `rag_confidence`
- Diskusi tuning: ubah `RERANK_COSINE_WEIGHT`, `RERANK_RRF_WEIGHT`, `RERANK_INCIDENT_BOOST`

Speaker notes: Sediakan waktu untuk pertanyaan soal trade-off bobot dan threshold.

---
# Appendix — JSON output contoh

{
  "query": "...",
  "retrieval": [...],
  "reranked": [...],
  "adequacy": {"score": 0.45, "iterations": 1},
  "citations_valid": true,
  "recommendation": {...},
  "fallback": null
}

Speaker notes: Beri contoh singkat saat live demo.
