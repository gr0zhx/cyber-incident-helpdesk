import json
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from app.web.services.rag_service import RagService


def _make_service():
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    return RagService(redis=r), r


def test_get_collection_info_wraps_rag_client(tmp_path):
    svc, _ = _make_service()
    with patch("app.web.services.rag_service.get_collection_info",
               return_value={"name": "cybersecurity_knowledge", "total_vectors": 42}):
        info = svc.get_collection_info()
    assert info["total_vectors"] == 42


def test_list_documents_wraps_rag_client(tmp_path):
    svc, _ = _make_service()
    with patch("app.web.services.rag_service.list_metadata_documents",
               return_value=[{"doc_id": "doc-1", "doc_title": "NIST Guide"}]):
        docs = svc.list_documents()
    assert len(docs) == 1 and docs[0]["doc_id"] == "doc-1"


def test_start_ingest_job_stores_status_pending(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("nist-guide.json")
    status = json.loads(r.get(f"rag:job:{job_id}"))
    assert status["state"] == "pending"
    assert status["meta_filename"] == "nist-guide.json"


def test_get_job_status_returns_none_for_unknown(tmp_path):
    svc, _ = _make_service()
    assert svc.get_job_status("nonexistent") is None


def test_get_job_status_returns_stored(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("doc.json")
    status = svc.get_job_status(job_id)
    assert status is not None and status["state"] == "pending"


def test_run_ingest_updates_status_to_done(tmp_path):
    svc, r = _make_service()
    job_id = svc.start_ingest_job("doc.json")
    with patch("app.web.services.rag_service.reingest_document",
               return_value={"doc_id": "d1", "uploaded": 10, "deleted": 5}):
        svc.run_ingest(job_id)
    status = svc.get_job_status(job_id)
    assert status["state"] == "done"
    assert status["result"]["uploaded"] == 10


def test_run_ingest_updates_status_to_error_on_failure(tmp_path):
    svc, _ = _make_service()
    job_id = svc.start_ingest_job("bad.json")
    with patch("app.web.services.rag_service.reingest_document",
               side_effect=RuntimeError("Qdrant down")):
        svc.run_ingest(job_id)
    status = svc.get_job_status(job_id)
    assert status["state"] == "error"
    assert "Qdrant down" in status["error"]
