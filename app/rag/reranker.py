"""
Score-based reranker untuk prototipe.

Menggabungkan sinyal:
  - rrf_score  : dari Reciprocal Rank Fusion (semantic + keyword)
  - boost      : jika incident_type cocok dengan incident_types di metadata chunk
Tidak menggunakan cross-encoder agar hemat resource di tahap prototipe.
"""

INCIDENT_TYPE_BOOST = 0.15
MIN_SCORE_THRESHOLD = 0.0


def _compute_final_score(chunk: dict, incident_type: str | None) -> float:
    base = chunk.get("rrf_score", chunk.get("score", 0.0))

    if incident_type:
        chunk_types = chunk.get("metadata", {}).get("incident_types", [])
        if incident_type.lower() in [t.lower() for t in chunk_types]:
            base += INCIDENT_TYPE_BOOST

    return base


def rerank(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
    incident_type: str | None = None,
) -> list[dict]:
    """
    Rerank retrieved chunks by final score and return top_k.

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
