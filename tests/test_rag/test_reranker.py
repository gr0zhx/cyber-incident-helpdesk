import pytest

from app.rag.reranker import (
    rerank,
    INCIDENT_TYPE_BOOST,
    _COSINE_WEIGHT,
    _RRF_WEIGHT,
    _RRF_NORMALIZE,
    _compute_final_score,
)


def _make_chunk(
    id_: str,
    rrf_score: float = 0.05,
    score: float = 0.5,
    incident_types: list | None = None,
) -> dict:
    return {
        "id": id_,
        "content": f"Content of {id_}",
        "metadata": {"incident_types": incident_types or []},
        "rrf_score": rrf_score,
        "score": score,
    }


def test_reranker_reduces_to_top_k():
    chunks = [_make_chunk(f"c{i}", rrf_score=0.05, score=0.9 - i * 0.05) for i in range(10)]
    result = rerank("query", chunks, top_k=3)
    assert len(result) == 3


def test_reranker_sorted_descending():
    chunks = [
        _make_chunk("low",  score=0.3, rrf_score=0.01),
        _make_chunk("high", score=0.9, rrf_score=0.05),
        _make_chunk("mid",  score=0.6, rrf_score=0.03),
    ]
    result = rerank("query", chunks, top_k=3)
    scores = [r["final_score"] for r in result]
    assert scores == sorted(scores, reverse=True)


def test_reranker_incident_type_boost():
    """Chunk dengan incident_type cocok harus punya final_score lebih tinggi."""
    no_match   = _make_chunk("no",  score=0.5, rrf_score=0.05, incident_types=["malware"])
    with_match = _make_chunk("yes", score=0.5, rrf_score=0.05, incident_types=["phishing"])

    result = rerank("query", [no_match, with_match], top_k=2, incident_type="phishing")
    scores = {r["id"]: r["final_score"] for r in result}

    # final_score = cosine*0.7 + rrf_norm*0.3 [+ boost]
    rrf_norm = min(0.05 / _RRF_NORMALIZE, 1.0)
    expected_base = _COSINE_WEIGHT * 0.5 + _RRF_WEIGHT * rrf_norm
    assert scores["yes"] == pytest.approx(expected_base + INCIDENT_TYPE_BOOST, abs=1e-6)
    assert scores["no"]  == pytest.approx(expected_base, abs=1e-6)
    assert scores["yes"] > scores["no"]


def test_reranker_final_score_formula():
    """Verifikasi formula: 0.7*cosine + 0.3*(rrf/0.05)."""
    chunk = _make_chunk("a", score=0.8, rrf_score=0.025)
    result = _compute_final_score(chunk, incident_type=None)
    rrf_norm = min(0.025 / _RRF_NORMALIZE, 1.0)  # 0.5
    expected = _COSINE_WEIGHT * 0.8 + _RRF_WEIGHT * rrf_norm
    assert result == pytest.approx(expected, abs=1e-6)


def test_reranker_final_score_capped_at_1():
    """final_score tidak boleh melebihi 1.0 meskipun semua sinyal maksimal."""
    chunk = _make_chunk("a", score=1.0, rrf_score=0.05, incident_types=["phishing"])
    result = _compute_final_score(chunk, incident_type="phishing")
    assert result <= 1.0


def test_reranker_adds_final_score_key():
    chunks = [_make_chunk("a")]
    result = rerank("query", chunks, top_k=1)
    assert "final_score" in result[0]


def test_reranker_top_k_larger_than_input():
    chunks = [_make_chunk("a"), _make_chunk("b")]
    result = rerank("query", chunks, top_k=10)
    assert len(result) == 2


def test_reranker_empty_input():
    assert rerank("query", [], top_k=5) == []
