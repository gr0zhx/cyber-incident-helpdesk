from app.rag.reranker import rerank, INCIDENT_TYPE_BOOST


def _make_chunk(id_: str, rrf_score: float = 0.05, incident_types: list | None = None) -> dict:
    return {
        "id": id_,
        "content": f"Content of {id_}",
        "metadata": {"incident_types": incident_types or []},
        "rrf_score": rrf_score,
    }


def test_reranker_reduces_to_top_k():
    chunks = [_make_chunk(f"c{i}", rrf_score=0.1 - i * 0.005) for i in range(10)]
    result = rerank("query", chunks, top_k=3)
    assert len(result) == 3


def test_reranker_sorted_descending():
    chunks = [_make_chunk("low", 0.01), _make_chunk("high", 0.09), _make_chunk("mid", 0.05)]
    result = rerank("query", chunks, top_k=3)
    scores = [r["final_score"] for r in result]
    assert scores == sorted(scores, reverse=True)


def test_reranker_incident_type_boost():
    no_match  = _make_chunk("no",  rrf_score=0.05, incident_types=["malware"])
    with_match = _make_chunk("yes", rrf_score=0.05, incident_types=["phishing"])

    result = rerank("query", [no_match, with_match], top_k=2, incident_type="phishing")
    scores = {r["id"]: r["final_score"] for r in result}

    assert scores["yes"] == pytest.approx(0.05 + INCIDENT_TYPE_BOOST, abs=1e-6)
    assert scores["no"]  == pytest.approx(0.05, abs=1e-6)
    assert scores["yes"] > scores["no"]


def test_reranker_adds_final_score_key():
    chunks = [_make_chunk("a", 0.05)]
    result = rerank("query", chunks, top_k=1)
    assert "final_score" in result[0]


def test_reranker_top_k_larger_than_input():
    chunks = [_make_chunk("a"), _make_chunk("b")]
    result = rerank("query", chunks, top_k=10)
    assert len(result) == 2


def test_reranker_empty_input():
    assert rerank("query", [], top_k=5) == []


import pytest
