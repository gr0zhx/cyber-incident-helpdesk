"""
Score-based reranker untuk prototipe.

final_score menggabungkan dua sinyal pada skala yang sama (0–1):
  - cosine similarity (bobot 0.7) : kualitas semantik query ↔ chunk
  - rrf_score yang dinormalisasi  (bobot 0.3) : gabungan ranking semantic + keyword
  - incident_type boost (+0.10)   : jika tipe insiden cocok dengan metadata chunk

Bobot 70/30 mengutamakan relevansi semantik (cosine) tapi tetap menghargai
sinyal keyword dari hybrid retrieval. Hasilnya skala konsisten 0–1 sehingga
threshold tunggal berlaku untuk semua tahap pipeline.
"""

# Bobot kombinasi cosine + RRF
_COSINE_WEIGHT = 0.7
_RRF_WEIGHT = 0.3

# RRF score biasanya di rentang 0.01–0.05 untuk top-20 hasil.
# Normalisasi ke 0–1 dengan membagi konstanta representatif.
_RRF_NORMALIZE = 0.05

INCIDENT_TYPE_BOOST = 0.10
MIN_SCORE_THRESHOLD = 0.0


def _compute_final_score(chunk: dict, incident_type: str | None) -> float:
    """Gabungkan cosine similarity + RRF score ke skala 0–1."""
    cosine = chunk.get("score", 0.0)                     # sudah 0–1
    rrf_norm = min(chunk.get("rrf_score", 0.0) / _RRF_NORMALIZE, 1.0)  # normalisasi ke 0–1

    base = (_COSINE_WEIGHT * cosine) + (_RRF_WEIGHT * rrf_norm)

    if incident_type:
        chunk_types = chunk.get("metadata", {}).get("incident_types", [])
        if incident_type.lower() in [t.lower() for t in chunk_types]:
            base += INCIDENT_TYPE_BOOST

    return min(base, 1.0)  # cap di 1.0


def rerank(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    incident_type: str | None = None,
) -> list[dict]:
    """
    Rerank retrieved chunks by final score and return top_k.

    final_score = 0.7 * cosine + 0.3 * normalized_rrf [+ 0.10 incident_type boost]
    Skala konsisten 0–1 sehingga satu threshold berlaku di seluruh pipeline.

    Args:
        query: original query string (reserved for future cross-encoder use)
        chunks: list of chunk dicts from HybridRetriever
        top_k: number of chunks to return
        incident_type: optional incident type for boosting

    Returns:
        Sorted list of top_k chunk dicts with 'final_score' added.
    """
    scored = []
    for chunk in chunks:
        final_score = _compute_final_score(chunk, incident_type)
        if final_score >= MIN_SCORE_THRESHOLD:
            scored.append({**chunk, "final_score": final_score})

    scored.sort(key=lambda c: c["final_score"], reverse=True)
    return scored[:top_k]
