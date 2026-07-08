"""Wrap rag_client untuk manajemen knowledge base dari web dashboard."""
from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Optional

_DOC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")

from app.dashboard.rag_client import (
    get_collection_info,
    list_metadata_documents,
    reingest_document,
    save_metadata,
    save_document,
)
from app.rag.ingestion import SUPPORTED_EXTENSIONS

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

    def upload_document(
        self,
        filename: str,
        data: bytes,
        doc_id: str,
        doc_title: str,
        source_framework: str,
        incident_types: list[str],
        language: str = "id",
    ) -> str:
        """Simpan dokumen + metadata ke knowledge_base/, return meta_filename.

        Mendukung: .pdf, .txt, .md, .csv, .json
        """
        if not _DOC_ID_RE.match(doc_id):
            raise ValueError("doc_id hanya boleh alfanumerik, dash, underscore (maks 64 karakter).")
        base_name = Path(filename).name
        if not base_name or base_name.startswith("."):
            raise ValueError("Nama file tidak valid.")
        safe_name = base_name.replace(" ", "_")
        ext = Path(safe_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Tipe file tidak didukung: {ext}. Gunakan: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        save_document(safe_name, data)
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
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupt RAG job status job=%s", job_id)
            return None

    def run_ingest(self, job_id: str) -> None:
        """Eksekusi reingest (dipanggil dari BackgroundTasks)."""
        raw = self._redis.get(f"rag:job:{job_id}")
        if not raw:
            logger.error("Job %s tidak ditemukan di Redis", job_id)
            return
        try:
            status = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            logger.error("Job %s status corrupt, abort ingest", job_id)
            return
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
