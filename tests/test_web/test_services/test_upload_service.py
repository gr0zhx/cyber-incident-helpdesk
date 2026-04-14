import json
from pathlib import Path
from unittest.mock import patch

import fakeredis
import pytest

from app.web.services.upload_service import UploadError, UploadService

FAKE_PDF_BYTES = b"%PDF-1.4 fake"
FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\nFAKE"


def _make_service(tmp_path):
    r = fakeredis.FakeStrictRedis(decode_responses=False)
    return UploadService(redis=r, upload_root=tmp_path), r


def test_save_pending_pdf(tmp_path):
    svc, r = _make_service(tmp_path)
    with patch("app.web.services.upload_service.magic") as m:
        m.from_buffer.return_value = "application/pdf"
        meta = svc.save_pending(
            session_id="sess-1",
            filename="report.pdf",
            data=FAKE_PDF_BYTES,
        )
    assert meta["original_filename"] == "report.pdf"
    assert meta["mime_type"] == "application/pdf"
    assert Path(meta["stored_path"]).exists()
    pending = json.loads(r.get("web:pending_uploads:sess-1") or b"[]")
    assert len(pending) == 1 and pending[0]["original_filename"] == "report.pdf"


def test_save_pending_rejects_invalid_extension(tmp_path):
    svc, _ = _make_service(tmp_path)
    with pytest.raises(UploadError, match="[Ee]kstensi"):
        svc.save_pending("sess-1", "virus.exe", b"MZ")


def test_save_pending_rejects_mime_mismatch(tmp_path):
    svc, _ = _make_service(tmp_path)
    with patch("app.web.services.upload_service.magic") as m:
        m.from_buffer.return_value = "application/x-msdownload"
        with pytest.raises(UploadError, match="MIME"):
            svc.save_pending("sess-1", "photo.png", b"MZ")


def test_save_pending_rejects_oversized(tmp_path):
    svc, _ = _make_service(tmp_path)
    big = b"x" * (11 * 1024 * 1024)
    with pytest.raises(UploadError, match="besar"):
        svc.save_pending("sess-1", "big.pdf", big)


def test_flush_pending_returns_and_clears(tmp_path):
    svc, r = _make_service(tmp_path)
    r.set("web:pending_uploads:sess-1", json.dumps([
        {"original_filename": "a.pdf", "stored_path": "/tmp/a.pdf",
         "mime_type": "application/pdf", "size_bytes": 100}
    ]).encode())
    result = svc.flush_pending("sess-1")
    assert len(result) == 1
    assert r.get("web:pending_uploads:sess-1") is None


def test_get_pending_returns_empty_list(tmp_path):
    svc, _ = _make_service(tmp_path)
    assert svc.get_pending("sess-no-uploads") == []
