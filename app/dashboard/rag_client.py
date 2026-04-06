"""Client untuk operasi manajemen knowledge base RAG.

Mengelola dua lapisan:
  - File layer  : PDF di knowledge_base/documents/ + metadata JSON
  - Vector layer: Chunks di Qdrant collection cybersecurity_knowledge
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.rag.embedder import COLLECTION_NAME

_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"
_DOCS_DIR = _KB_ROOT / "documents"
_META_DIR = _KB_ROOT / "metadata"

ALLOWED_EXTENSIONS = {".pdf"}


def _get_qdrant() -> QdrantClient:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key)


# ---------------------------------------------------------------------------
# Informasi collection
# ---------------------------------------------------------------------------

def get_collection_info() -> dict:
    """Ambil info collection Qdrant: jumlah vectors, ukuran, status."""
    client = _get_qdrant()
    try:
        info = client.get_collection(COLLECTION_NAME)
        return {
            "name": COLLECTION_NAME,
            "total_vectors": info.vectors_count,
            "indexed_vectors": info.indexed_vectors_count,
            "status": str(info.status),
            "on_disk": info.config.params.vectors.on_disk if info.config.params.vectors else False,
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_collection_stats_by_source() -> list[dict]:
    """Statistik jumlah chunk per doc_id (dokumen sumber)."""
    client = _get_qdrant()
    # Scroll semua point — ambil payload saja, tanpa vector
    all_doc_ids: dict[str, dict] = {}
    offset = None

    while True:
        results, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            with_payload=["doc_id", "doc_title", "source_framework", "object_type"],
            with_vectors=False,
            offset=offset,
        )
        for point in results:
            doc_id = point.payload.get("doc_id", "unknown")
            if doc_id not in all_doc_ids:
                all_doc_ids[doc_id] = {
                    "doc_id": doc_id,
                    "doc_title": point.payload.get("doc_title", ""),
                    "source_framework": point.payload.get("source_framework", ""),
                    "chunk_count": 0,
                }
            all_doc_ids[doc_id]["chunk_count"] += 1

        if next_offset is None:
            break
        offset = next_offset

    return sorted(all_doc_ids.values(), key=lambda x: x["chunk_count"], reverse=True)


# ---------------------------------------------------------------------------
# Manajemen metadata dokumen (file layer)
# ---------------------------------------------------------------------------

def list_metadata_documents() -> list[dict]:
    """Daftar semua dokumen yang terdaftar di metadata dir."""
    _META_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for meta_file in sorted(_META_DIR.glob("*.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            pdf_path = _DOCS_DIR / meta.get("filename", "")
            meta["_meta_file"] = meta_file.name
            meta["_pdf_exists"] = pdf_path.exists()
            meta["_pdf_size_kb"] = round(pdf_path.stat().st_size / 1024, 1) if pdf_path.exists() else 0
            result.append(meta)
        except Exception:
            continue
    return result


def save_metadata(meta_filename: str, data: dict) -> None:
    """Simpan atau update file metadata JSON."""
    _META_DIR.mkdir(parents=True, exist_ok=True)
    path = _META_DIR / meta_filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_metadata(meta_filename: str) -> None:
    """Hapus file metadata JSON."""
    path = _META_DIR / meta_filename
    if path.exists():
        path.unlink()


def save_pdf(filename: str, file_bytes: bytes) -> Path:
    """Simpan file PDF ke direktori dokumen knowledge base."""
    _DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _DOCS_DIR / filename
    dest.write_bytes(file_bytes)
    return dest


def delete_pdf(filename: str) -> bool:
    """Hapus file PDF dari direktori dokumen."""
    path = _DOCS_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False


def list_pdf_files() -> list[dict]:
    """Daftar semua file PDF di direktori dokumen (termasuk yang belum punya metadata)."""
    _DOCS_DIR.mkdir(parents=True, exist_ok=True)
    registered = {
        m.get("filename", "") for m in list_metadata_documents()
    }
    result = []
    for pdf in sorted(_DOCS_DIR.glob("*.pdf")):
        result.append({
            "filename": pdf.name,
            "size_kb": round(pdf.stat().st_size / 1024, 1),
            "has_metadata": pdf.name in registered,
        })
    return result


# ---------------------------------------------------------------------------
# Operasi Qdrant (vector layer)
# ---------------------------------------------------------------------------

def search_chunks(query_text: str, top_k: int = 10) -> list[dict]:
    """Cari chunks di Qdrant menggunakan full-text search (tanpa embedding)."""
    from qdrant_client.models import MatchText
    client = _get_qdrant()
    try:
        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="content", match=MatchText(text=query_text))]
            ),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "id": str(p.id),
                "content": p.payload.get("content", ""),
                "doc_id": p.payload.get("doc_id", ""),
                "doc_title": p.payload.get("doc_title", ""),
                "source_framework": p.payload.get("source_framework", ""),
                "section_header": p.payload.get("section_header", ""),
                "chunk_index": p.payload.get("chunk_index", 0),
                "object_type": p.payload.get("object_type", ""),
            }
            for p in results
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def delete_chunks_by_doc_id(doc_id: str) -> int:
    """Hapus semua chunk dari Qdrant berdasarkan doc_id.

    Returns:
        Jumlah chunk yang dihapus.
    """
    client = _get_qdrant()
    # Hitung dulu berapa chunk yang akan dihapus
    count_result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
        exact=True,
    )
    n = count_result.count

    if n > 0:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )
    return n


def get_chunks_sample(doc_id: str, limit: int = 5) -> list[dict]:
    """Ambil sampel chunks untuk preview dokumen tertentu."""
    client = _get_qdrant()
    results, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [
        {
            "id": str(p.id),
            "content": p.payload.get("content", "")[:300],
            "section_header": p.payload.get("section_header", ""),
            "chunk_index": p.payload.get("chunk_index", 0),
        }
        for p in results
    ]


# ---------------------------------------------------------------------------
# Ingest pipeline (wrapper untuk re-ingest dokumen)
# ---------------------------------------------------------------------------

def reingest_document(meta_filename: str) -> dict:
    """Re-ingest satu dokumen PDF: hapus chunks lama, embed ulang, upload.

    Returns:
        {"doc_id": ..., "deleted": N, "uploaded": N, "error": ...}
    """
    from app.rag.chunker import chunk_documents
    from app.rag.embedder import embed_chunks, upload_chunks
    from app.rag.ingestion import ingest_document, load_metadata
    from app.utils.llm_client import create_embedder

    meta_path = _META_DIR / meta_filename
    if not meta_path.exists():
        return {"error": f"Metadata tidak ditemukan: {meta_filename}"}

    meta = load_metadata(meta_path)
    pdf_path = _DOCS_DIR / meta.get("filename", "")
    if not pdf_path.exists():
        return {"error": f"PDF tidak ditemukan: {pdf_path.name}"}

    doc_id = meta["doc_id"]

    # 1. Hapus chunks lama
    deleted = delete_chunks_by_doc_id(doc_id)

    # 2. Load + chunk
    docs = ingest_document(pdf_path, meta)
    chunks = chunk_documents(docs)

    # 3. Embed
    embedder = create_embedder()
    vectors = embed_chunks(chunks, embedder)

    # 4. Upload
    client = _get_qdrant()
    uploaded = upload_chunks(client, chunks, vectors)

    return {
        "doc_id": doc_id,
        "doc_title": meta["doc_title"],
        "deleted": deleted,
        "uploaded": uploaded,
    }
