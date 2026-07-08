from unittest.mock import MagicMock, patch

import pytest

from app.rag.retriever import HybridRetriever, _reciprocal_rank_fusion, _rrf_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hit(id_: str, score: float = 0.5, incident_types: list | None = None) -> dict:
    return {
        "id": id_,
        "content": f"Content for {id_}",
        "metadata": {"incident_types": incident_types or [], "source_framework": "NIST"},
        "score": score,
    }


# ---------------------------------------------------------------------------
# RRF unit tests (pure logic, no external deps)
# ---------------------------------------------------------------------------

def test_rrf_score_decreases_with_rank():
    assert _rrf_score(0) > _rrf_score(1) > _rrf_score(10)


def test_rrf_score_positive():
    for rank in range(20):
        assert _rrf_score(rank) > 0


def test_rrf_merge_combines_lists():
    semantic = [_make_hit("a"), _make_hit("b")]
    keyword  = [_make_hit("b"), _make_hit("c")]
    merged = _reciprocal_rank_fusion(semantic, keyword)
    ids = [h["id"] for h in merged]
    assert set(ids) == {"a", "b", "c"}


def test_rrf_boost_document_appearing_in_both_lists():
    semantic = [_make_hit("a"), _make_hit("b"), _make_hit("c")]
    keyword  = [_make_hit("b"), _make_hit("d")]
    merged = _reciprocal_rank_fusion(semantic, keyword)
    scores = {h["id"]: h["rrf_score"] for h in merged}
    # "b" appears in both → higher rrf_score than "a" (only semantic rank 0)
    assert scores["b"] > scores["a"]


def test_rrf_result_sorted_descending():
    semantic = [_make_hit(f"s{i}") for i in range(5)]
    keyword  = [_make_hit(f"k{i}") for i in range(5)]
    merged = _reciprocal_rank_fusion(semantic, keyword)
    scores = [h["rrf_score"] for h in merged]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# HybridRetriever tests (mocked Qdrant + embedder)
# ---------------------------------------------------------------------------

def _make_qdrant_hit(id_: str, score: float = 0.8):
    hit = MagicMock()
    hit.id = id_
    hit.score = score
    hit.payload = {
        "content": f"Content {id_}",
        "source_framework": "NIST",
        "incident_types": ["phishing"],
    }
    return hit


def _make_qdrant_point(id_: str):
    pt = MagicMock()
    pt.id = id_
    pt.payload = {
        "content": f"Content {id_}",
        "source_framework": "NIST",
        "incident_types": ["phishing"],
    }
    return pt


@pytest.fixture
def retriever():
    mock_client = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed_query.return_value = [0.1] * 1536
    return HybridRetriever(mock_client, mock_embedder), mock_client


def test_semantic_search_returns_results(retriever):
    hr, mock_client = retriever
    mock_client.search.return_value = [_make_qdrant_hit("doc1"), _make_qdrant_hit("doc2")]
    mock_client.scroll.return_value = ([], None)

    results = hr.retrieve("phishing email attack")
    assert len(results) >= 1
    assert results[0]["content"].startswith("Content")


def test_hybrid_retrieval_merges_results(retriever):
    hr, mock_client = retriever
    mock_client.search.return_value = [_make_qdrant_hit("sem1"), _make_qdrant_hit("sem2")]
    mock_client.scroll.return_value = ([_make_qdrant_point("kw1")], None)

    results = hr.retrieve("malware detection")
    ids = [r["id"] for r in results]
    assert "sem1" in ids
    assert "kw1" in ids


def test_metadata_filter_by_incident_type(retriever):
    hr, mock_client = retriever
    mock_client.search.return_value = [_make_qdrant_hit("doc1")]
    mock_client.scroll.return_value = ([], None)

    hr.retrieve("phishing", incident_type="phishing")

    # Verify that a filter was passed to client.search
    call_kwargs = mock_client.search.call_args[1]
    assert call_kwargs.get("query_filter") is not None


def test_retrieve_respects_top_k(retriever):
    hr, mock_client = retriever
    mock_client.search.return_value = [_make_qdrant_hit(f"d{i}") for i in range(10)]
    mock_client.scroll.return_value = ([], None)

    results = hr.retrieve("test", top_k=5)
    assert len(results) <= 5


def test_keyword_search_failure_is_graceful(retriever):
    hr, mock_client = retriever
    mock_client.search.return_value = [_make_qdrant_hit("doc1")]
    mock_client.scroll.side_effect = Exception("Qdrant error")

    # Should not raise — keyword failure falls back to empty list
    results = hr.retrieve("ransomware mitigation")
    assert isinstance(results, list)
