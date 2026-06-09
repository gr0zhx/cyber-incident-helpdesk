# Mekanisme Agentic RAG (Final - Sesuai Implementasi Repo)

## Ringkasan singkat
Implementasi di repository menggunakan pendekatan Agentic RAG: loop retrieval → rerank → adequacy check → expansion (maks 3 iterasi) → LLM generation → citation validation → fallback jika perlu.

## Alur Pemrosesan
1. Query Builder
   - Input: `incident_type`, laporan pengguna (sanitized)
   - Output: query terstruktur (intent + keywords / konteks)

2. Hybrid Search
   - Semantic Search (embedding-based) + Keyword Search (Qdrant full-text)
   - Hasil dua list digabungkan dengan Reciprocal Rank Fusion (RRF)
   - RRF parameter: `RRF_K = 60` (lihat `app/rag/retriever.py`)

3. RRF Reranking
   - Formula akhir (implementasi):
     Score = 0.7 * cosine_similarity + 0.3 * normalized_rrf + incident_type_boost
   - Normalisasi RRF: `rrf_norm = min(rrf_score / 0.05, 1.0)` (lihat `app/rag/reranker.py`)
   - Incident type boost default: +0.20 (configurable via ENV)
   - Hasil disimpan di `final_score` (skala 0–1)

4. Adequacy Check
   - Implementasi memeriksa apakah ada chunk dengan `final_score >= RETRIEVAL_SCORE_THRESHOLD`.
   - Nilai default di kode: `RETRIEVAL_SCORE_THRESHOLD = 0.22` (lihat `app/agents/mitigation.py`)
   - Batas iterasi: `MAX_ITERATIONS = 3`
   - Jika tidak memadai → query expansion (aturan berbasis `incident_type`) → ulang retrieval → rerank.

5. Citation Validation
   - Periksa keberadaan dan keterlacakan sumber pada langkah yang dihasilkan LLM.
   - Field yang dicocokkan (implementasi): `source`, `section`, `doc_title`, `section_header`, `source_framework`, `external_id` (6 fields)
   - Langkah tanpa sitasi yang diverifikasi akan dihapus; jika semua langkah gagal → fallback.

6. Respons Final / Fallback
   - Output API mengembalikan dict JSON berisi kunci: `mitigation_recommendation`, `citations`, `retrieved_chunks`, `rag_confidence`, `mitigation_steps`.
   - Fallback: `_FALLBACK_RESULT` (tidak memberikan rekomendasi yang tidak terverifikasi, arahkan ke CSIRT).

## Parameter Utama (nilai default di repo)
- `MAX_ITERATIONS`: 3
- `TOP_K_RETRIEVAL`: 30
- `TOP_K_RERANK`: 5
- `RETRIEVAL_SCORE_THRESHOLD`: 0.22
- `CHUNK_SIZE`: 800 karakter
- `CHUNK_OVERLAP`: 100 karakter
- `EMBEDDING_MODEL`: text-embedding-3-small
- `EMBEDDING_DIM`: 1536
- `RRF_K`: 60
- `RRF_NORMALIZE_DIVISOR`: 0.05
- `INCIDENT_TYPE_BOOST`: 0.20

## Catatan teknis penting untuk slide / pembahasan
- Jelaskan bahwa `rrf_score` kecil (mis. 0.01–0.05) dan oleh karena itu dinormalisasi agar kontribusinya skala-komparabel dengan cosine similarity.
- Tegaskan bahwa ambang (`RETRIEVAL_SCORE_THRESHOLD`) dan bobot rerank dapat disesuaikan via ENV untuk eksperimen.
- Sebutkan struktur JSON keluaran agar integrator tahu contract.

## Referensi implementasi
- Reranker: `app/rag/reranker.py`
- Retriever / RRF: `app/rag/retriever.py`
- Chunker: `app/rag/chunker.py` (CHUNK_SIZE / CHUNK_OVERLAP)
- Mitigation agent: `app/agents/mitigation.py` (loop agentic, adequacy, citation validation, fallback)

---

Generated from code inspection on repository (periksa file terkait saat presentasi).