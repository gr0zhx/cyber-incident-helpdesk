"""Unit tests for MitigationAdvisorAgent.

All tests mock the LLM client and retriever — no real API or Qdrant calls are made.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.mitigation import (
    MitigationAdvisorAgent,
    _assemble_context,
    _check_adequacy,
    _compute_rag_confidence,
    _expand_query,
    _merge_results,
    _validate_citations,
    _FALLBACK_RESULT,
)
from app.utils.llm_parser import parse_llm_json as _parse_llm_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_chunk(id: str, content: str, source: str, section: str = "", score: float = 0.5) -> dict:
    return {
        "id": id,
        "content": content,
        "metadata": {"source": source, "section": section},
        "final_score": score,
        "rrf_score": score,
    }


def _make_llm_response(steps: list[dict], general: str = "", escalation: str = "") -> dict:
    return {
        "mitigation_steps": steps,
        "general_guidance": general,
        "escalation_note": escalation,
    }


def _mock_retriever(chunks: list[dict]):
    retriever = MagicMock()
    retriever.retrieve.return_value = chunks
    return retriever


def _mock_reranker(chunks: list[dict]):
    def _fn(query, all_chunks, top_k=5, incident_type=None):
        return chunks[:top_k]
    return _fn


def _make_agent(
    llm_response: dict | None = None,
    chunks: list[dict] | None = None,
    llm_side_effect=None,
) -> MitigationAdvisorAgent:
    mock_client = MagicMock()

    if llm_side_effect is not None:
        mock_client.chat.completions.create = AsyncMock(side_effect=llm_side_effect)
    else:
        content = json.dumps(llm_response) if llm_response is not None else ""
        choice = MagicMock()
        choice.message.content = content
        completion = MagicMock()
        completion.choices = [choice]
        mock_client.chat.completions.create = AsyncMock(return_value=completion)

    default_chunks = chunks if chunks is not None else [
        _make_chunk("1", "Isolasi endpoint yang terinfeksi segera.", "NIST SP 800-61", "Bagian 3.2", score=0.6),
        _make_chunk("2", "Notifikasi tim CSIRT.", "BSSN Panduan Respons Insiden", "Bab 4", score=0.5),
    ]
    retriever = _mock_retriever(default_chunks)
    reranker_fn = _mock_reranker(default_chunks)

    return MitigationAdvisorAgent(
        llm_client=mock_client,
        retriever=retriever,
        reranker_fn=reranker_fn,
        model="gpt-4o",
    )


# ---------------------------------------------------------------------------
# Pure helper function tests (no async)
# ---------------------------------------------------------------------------

def test_parse_llm_response_valid_json():
    raw = json.dumps({"mitigation_steps": [], "general_guidance": "ok", "escalation_note": ""})
    result = _parse_llm_response(raw)
    assert result is not None
    assert "mitigation_steps" in result


def test_parse_llm_response_embedded_in_text():
    payload = {"mitigation_steps": [{"step": 1, "action": "Isolasi", "source": "NIST SP 800-61"}]}
    raw = f"Berikut rekomendasinya:\n{json.dumps(payload)}\nTerima kasih."
    result = _parse_llm_response(raw)
    assert result is not None
    assert result["mitigation_steps"][0]["action"] == "Isolasi"


def test_parse_llm_response_invalid_returns_none():
    assert _parse_llm_response("bukan json") is None
    assert _parse_llm_response("") is None


def test_check_adequacy_above_threshold():
    chunks = [_make_chunk("1", "konten", "Sumber", score=0.5)]
    assert _check_adequacy(chunks) is True


def test_check_adequacy_below_threshold():
    chunks = [_make_chunk("1", "konten", "Sumber", score=0.1)]
    assert _check_adequacy(chunks) is False


def test_check_adequacy_empty():
    assert _check_adequacy([]) is False


def test_expand_query_iteration2():
    result = _expand_query("email phishing CEO", "Phishing", 2)
    assert "phishing" in result.lower()
    assert "email phishing CEO" in result


def test_expand_query_iteration3():
    result = _expand_query("email phishing CEO", "Phishing", 3)
    assert "phishing" in result.lower()


def test_merge_results_deduplication():
    c1 = _make_chunk("1", "aaa", "NIST")
    c2 = _make_chunk("2", "bbb", "BSSN")
    c1_dup = _make_chunk("1", "aaa", "NIST")
    merged = _merge_results([c1, c2], [c1_dup])
    assert len(merged) == 2


def test_merge_results_combines():
    c1 = _make_chunk("1", "aaa", "NIST")
    c2 = _make_chunk("2", "bbb", "BSSN")
    merged = _merge_results([c1], [c2])
    assert len(merged) == 2


def test_validate_citations_removes_unsourced_steps():
    chunks = [_make_chunk("1", "konten", "NIST SP 800-61", "Bagian 3")]
    steps = [
        {"step": 1, "action": "Tindakan A", "source": "NIST SP 800-61"},
        {"step": 2, "action": "Tindakan B", "source": ""},  # tanpa sitasi
    ]
    valid = _validate_citations(steps, chunks)
    assert len(valid) == 1
    assert valid[0]["step"] == 1


def test_validate_citations_accepts_known_standards():
    chunks = [_make_chunk("1", "konten", "Dokumen Internal")]
    steps = [
        {"step": 1, "action": "Ikuti prosedur", "source": "NIST SP 800-61, Bagian 3.4"},
        {"step": 2, "action": "Cek ATT&CK", "source": "MITRE ATT&CK T1566"},
    ]
    valid = _validate_citations(steps, chunks)
    assert len(valid) == 2


def test_validate_citations_accepts_numeric_chunk_reference():
    """LLM sering menghasilkan '[1] Training and Awareness' — harus diterima karena [1] valid."""
    chunks = [
        _make_chunk("1", "konten A", "NIST SP 800-61", "Training and Awareness"),
        _make_chunk("2", "konten B", "NIST SP 800-61", "Containment"),
    ]
    steps = [
        {"step": 1, "action": "Lakukan pelatihan", "source": "[1] Training and Awareness"},
        {"step": 2, "action": "Lakukan isolasi", "source": "[2] Containment Procedures"},
        {"step": 3, "action": "Tidak valid", "source": "[9] Bab yang tidak ada"},
    ]
    valid = _validate_citations(steps, chunks)
    # [1] dan [2] valid (dalam rentang 1–2), [9] tidak valid
    assert len(valid) == 2
    assert valid[0]["step"] == 1
    assert valid[1]["step"] == 2


def test_compute_rag_confidence_average():
    chunks = [
        _make_chunk("1", "", "", score=0.8),
        _make_chunk("2", "", "", score=0.6),
    ]
    conf = _compute_rag_confidence(chunks)
    assert abs(conf - 0.7) < 0.01


def test_compute_rag_confidence_empty():
    assert _compute_rag_confidence([]) == 0.0


def test_assemble_context_formats_chunks():
    chunks = [
        _make_chunk("1", "Isolasi endpoint.", "NIST SP 800-61", "Bagian 3.2"),
    ]
    ctx = _assemble_context(chunks)
    assert "[1]" in ctx
    assert "NIST SP 800-61" in ctx
    assert "Isolasi endpoint." in ctx


# ---------------------------------------------------------------------------
# Async integration-style tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_mitigation_phishing():
    """Ada dokumen relevan → rekomendasi dengan sitasi."""
    chunks = [_make_chunk("1", "Jangan klik link mencurigakan.", "NIST SP 800-61", "Bagian 3.1", score=0.7)]
    llm_resp = _make_llm_response(
        steps=[{"step": 1, "action": "Jangan klik link mencurigakan.", "source": "NIST SP 800-61"}],
        general="Laporkan ke tim keamanan.",
    )
    agent = _make_agent(llm_response=llm_resp, chunks=chunks)

    result = await agent.generate_mitigation("Saya klik link phishing dari CEO palsu.", "Phishing", "Tinggi")

    assert "mitigation_recommendation" in result
    assert result["rag_confidence"] > 0.0
    assert isinstance(result["citations"], list)
    assert isinstance(result["retrieved_chunks"], list)


@pytest.mark.asyncio
async def test_generate_mitigation_with_citations():
    """Setiap langkah yang valid harus memiliki source."""
    chunks = [_make_chunk("1", "Isolasi sistem.", "NIST SP 800-61", "Bagian 3.4", score=0.65)]
    llm_resp = _make_llm_response(
        steps=[
            {"step": 1, "action": "Isolasi sistem.", "source": "NIST SP 800-61"},
            {"step": 2, "action": "Backup data.", "source": "NIST SP 800-61"},
        ]
    )
    agent = _make_agent(llm_response=llm_resp, chunks=chunks)

    result = await agent.generate_mitigation("Ransomware terdeteksi.", "Ransomware", "Kritis")

    assert len(result["citations"]) >= 1
    for citation in result["citations"]:
        assert "source" in citation


@pytest.mark.asyncio
async def test_agentic_rag_retry():
    """Query pertama menghasilkan skor rendah → iterasi berikutnya berhasil."""
    low_score_chunk = _make_chunk("x", "tidak relevan", "Sumber X", score=0.05)
    high_score_chunk = _make_chunk("1", "Prosedur respons phishing.", "NIST SP 800-61", "Bagian 3", score=0.8)

    call_count = {"n": 0}

    def retriever_fn(query, incident_type=None, top_k=20):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return [low_score_chunk]
        return [high_score_chunk]

    retriever = MagicMock()
    retriever.retrieve.side_effect = retriever_fn

    # Reranker passthrough: berikan skor yang ada
    def reranker_fn(query, chunks, top_k=5, incident_type=None):
        return sorted(chunks, key=lambda c: c.get("final_score", 0), reverse=True)[:top_k]

    llm_resp = _make_llm_response(
        steps=[{"step": 1, "action": "Blokir pengirim.", "source": "NIST SP 800-61"}]
    )
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(llm_resp)
    completion = MagicMock()
    completion.choices = [choice]
    mock_client.chat.completions.create = AsyncMock(return_value=completion)

    agent = MitigationAdvisorAgent(
        llm_client=mock_client,
        retriever=retriever,
        reranker_fn=reranker_fn,
        model="gpt-4o",
    )

    result = await agent.generate_mitigation("Email phishing dari CEO", "Phishing", "Tinggi")

    assert call_count["n"] >= 2
    assert result["rag_confidence"] > 0.0


@pytest.mark.asyncio
async def test_fallback_no_relevant_docs():
    """Tidak ada dokumen relevan → pesan fallback standar."""
    low_chunks = [_make_chunk("1", "konten tidak relevan", "Sumber", score=0.05)]
    agent = _make_agent(llm_response={}, chunks=low_chunks)

    result = await agent.generate_mitigation("Insiden tidak diketahui", "Lainnya", "Rendah")

    assert result["rag_confidence"] == 0.0
    assert result["citations"] == []
    assert "Tim Keamanan Siber dan PDP" in result["mitigation_recommendation"]


@pytest.mark.asyncio
async def test_citation_validation_removes_fake_citations():
    """Sitasi yang tidak ada di chunk atau standar yang dikenal harus dihapus."""
    chunks = [_make_chunk("1", "Panduan NIST.", "NIST SP 800-61", "Bagian 3", score=0.7)]
    llm_resp = _make_llm_response(
        steps=[
            {"step": 1, "action": "Tindakan valid.", "source": "NIST SP 800-61"},
            {"step": 2, "action": "Tindakan palsu.", "source": "Buku Karangan Sendiri 2024"},
        ]
    )
    agent = _make_agent(llm_response=llm_resp, chunks=chunks)

    result = await agent.generate_mitigation("Phishing masuk.", "Phishing", "Tinggi")

    # Hanya 1 langkah valid yang harus tersisa
    assert len(result.get("mitigation_steps", [])) == 1
    assert result["mitigation_steps"][0]["step"] == 1


@pytest.mark.asyncio
async def test_result_keys_always_present():
    """Semua key wajib harus ada, bahkan saat fallback."""
    low_chunks = [_make_chunk("1", "x", "S", score=0.05)]
    agent = _make_agent(llm_response={}, chunks=low_chunks)

    result = await agent.generate_mitigation("test", "Lainnya", "Rendah")

    required = {"mitigation_recommendation", "citations", "retrieved_chunks", "rag_confidence"}
    assert required.issubset(result.keys())


@pytest.mark.asyncio
async def test_llm_timeout_returns_fallback():
    """LLM timeout → fallback yang aman, pipeline tidak crash."""
    from openai import APITimeoutError

    chunks = [_make_chunk("1", "Panduan NIST.", "NIST SP 800-61", score=0.7)]
    agent = _make_agent(llm_side_effect=APITimeoutError(request=MagicMock()), chunks=chunks)

    result = await agent.generate_mitigation("DDoS terdeteksi", "DDoS", "Kritis")

    assert result["rag_confidence"] == 0.0
    assert "Tim Keamanan Siber dan PDP" in result["mitigation_recommendation"] or "timeout" in result["mitigation_recommendation"].lower()


@pytest.mark.asyncio
async def test_all_citations_fail_validation_returns_fallback():
    """Semua langkah LLM punya sitasi palsu → fallback, bukan state tidak konsisten."""
    chunks = [_make_chunk("1", "Panduan NIST.", "NIST SP 800-61", "Bagian 3", score=0.8)]
    llm_resp = _make_llm_response(
        steps=[
            {"step": 1, "action": "Tindakan A.", "source": "Buku Karangan Sendiri Vol. 1"},
            {"step": 2, "action": "Tindakan B.", "source": "Blog Random 2023"},
        ]
    )
    agent = _make_agent(llm_response=llm_resp, chunks=chunks)

    result = await agent.generate_mitigation("Insiden terjadi", "Phishing", "Tinggi")

    # Semua sitasi palsu → harus fallback, rag_confidence harus 0.0 (bukan nilai chunk)
    assert result["rag_confidence"] == 0.0
    assert result["citations"] == []
    assert "Tim Keamanan Siber dan PDP" in result["mitigation_recommendation"]


def test_validate_citations_rejects_short_generic_word():
    """Kata pendek (<5 karakter) tidak boleh memicu false positive di has_match."""
    chunks = [_make_chunk("1", "konten", "NIST SP 800-61 Panduan Resmi", "Bab A")]
    steps = [
        {"step": 1, "action": "Tindakan.", "source": "SOP"},  # terlalu pendek, bukan standar dikenal
    ]
    valid = _validate_citations(steps, chunks)
    assert len(valid) == 0
