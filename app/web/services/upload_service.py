"""Validasi dan penyimpanan file upload pelapor."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_list(raw: Any) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        logger.warning("Corrupt pending uploads JSON, reset")
        return []

try:
    import magic
except ImportError:  # pragma: no cover — platform fallback
    magic = None  # type: ignore[assignment]

MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIMES = {"application/pdf", "image/png", "image/jpeg"}


class UploadError(ValueError):
    """File upload ditolak karena validasi gagal."""


class UploadService:
    def __init__(self, redis: Any, upload_root: Path | str) -> None:
        self._redis = redis
        self._root = Path(upload_root)

    def save_pending(self, session_id: str, filename: str, data: bytes) -> dict:
        """Validasi, simpan ke disk, catat ke Redis pending. Return metadata."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UploadError(f"Ekstensi file tidak diizinkan: {ext}")
        if len(data) > MAX_SIZE_BYTES:
            raise UploadError("File terlalu besar (maks 10 MB).")
        if magic is None:
            raise UploadError("python-magic tidak terinstall di server ini.")
        detected = magic.from_buffer(data, mime=True)
        if detected not in ALLOWED_MIMES:
            raise UploadError(f"MIME type file tidak valid: {detected}")

        month_dir = self._root / datetime.utcnow().strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4()}{ext}"
        stored_path = month_dir / stored_name
        stored_path.write_bytes(data)

        meta = {
            "original_filename": filename,
            "stored_path": str(stored_path),
            "mime_type": detected,
            "size_bytes": len(data),
        }
        key = f"web:pending_uploads:{session_id}"
        existing = _load_list(self._redis.get(key))
        existing.append(meta)
        self._redis.setex(key, 3600, json.dumps(existing).encode())
        return meta

    def flush_pending(self, session_id: str) -> list[dict]:
        """Ambil + hapus pending uploads dari Redis (atomic). Return list metadata."""
        key = f"web:pending_uploads:{session_id}"
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        raw, _ = pipe.execute()
        return _load_list(raw)

    def get_pending(self, session_id: str) -> list[dict]:
        """Lihat pending uploads tanpa menghapus."""
        key = f"web:pending_uploads:{session_id}"
        return _load_list(self._redis.get(key))
