"""Wrap rag_client untuk manajemen knowledge base dari web dashboard."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from app.dashboard.rag_client import (
    get_collection_info,
    list_metadata_documents,
    reingest_document,
    save_metadata,
    save_pdf,
)

logger = logging.getLogger(__name__)
_JOB_TTL = 3600  # 1 jam


class RagService:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    def get_collection_info(self) -> dict:
        """Info Qdrant collection (total vectors, status)."""
        try:
            return get_collection_info()
        except Exception as exc:
            logger.warning("get_collection_info gagal: %s", exc)
            return {"error": str(exc)}

    def list_documents(self) -> list[dict]:
        """Daftar dokumen yang terdaftar di knowledge base."""
        try:
            return list_metadata_documents()
        except Exception as exc:
            logger.warning("list_metadata_documents gagal: %s", exc)
            return []

    def upload_pdf(
        self,
        filename: str,
        data: bytes,
        doc_id: str,
        doc_title: str,
        source_framework: str,
        incident_types: list[str],
        language: str = "id",
    ) -> str:
        """Simpan PDF + metadata ke knowledge_base/, return meta_filename."""
        safe_name = filename.replace(" ", "_")
        save_pdf(safe_name, data)
        meta_filename = f"{doc_id}.json"
        save_metadata(meta_filename, {
            "doc_id": doc_id,
            "doc_title": doc_title,
            "filename": safe_name,
            "source_framework": source_framework,
            "incident_types": incident_types,
            "language": language,
            "version": "1.0",
        })
        return meta_filename

    def start_ingest_job(self, meta_filename: str) -> str:
        """Buat job ID dan simpan status 'pending' ke Redis."""
        job_id = str(uuid.uuid4())
        status = {"state": "pending", "meta_filename": meta_filename}
        self._redis.setex(f"rag:job:{job_id}", _JOB_TTL, json.dumps(status).encode())
        return job_id

    def get_job_status(self, job_id: str) -> Optional[dict]:
        raw = self._redis.get(f"rag:job:{job_id}")
        if not raw:
            return None
        return json.loads(raw)

    def run_ingest(self, job_id: str) -> None:
        """Eksekusi reingest (dipanggil dari BackgroundTasks)."""
        raw = self._redis.get(f"rag:job:{job_id}")
        if not raw:
            logger.error("Job %s tidak ditemukan di Redis", job_id)
            return
        status = json.loads(raw)
        meta_filename = status["meta_filename"]
        try:
            result = reingest_document(meta_filename)
            status["state"] = "done"
            status["result"] = result
        except Exception as exc:
            logger.exception("Ingest job %s gagal", job_id)
            status["state"] = "error"
            status["error"] = str(exc)
        self._redis.setex(f"rag:job:{job_id}", _JOB_TTL, json.dumps(status).encode())
        logger.info("RAG_INGEST_COMPLETED job=%s state=%s", job_id, status["state"])
