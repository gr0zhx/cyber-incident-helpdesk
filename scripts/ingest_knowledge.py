"""
Script ingesti dokumen ke Qdrant.

Penggunaan:
    python scripts/ingest_knowledge.py \
        --docs-dir knowledge_base/documents/ \
        --metadata-dir knowledge_base/metadata/
"""
import argparse
import sys
from pathlib import Path

# Tambahkan root proyek ke sys.path agar bisa import app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from app.config import get_settings
from app.rag.chunker import chunk_documents
from app.rag.embedder import embed_chunks, get_embedder, upload_chunks
from app.rag.ingestion import ingest_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest dokumen ke Qdrant")
    parser.add_argument(
        "--docs-dir",
        default="knowledge_base/documents/",
        help="Direktori berisi file PDF",
    )
    parser.add_argument(
        "--metadata-dir",
        default="knowledge_base/metadata/",
        help="Direktori berisi file metadata JSON",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    settings = get_settings()

    # --- 1. Ingesti ---
    print("Membaca dokumen...")
    documents = ingest_directory(args.docs_dir, args.metadata_dir)
    if not documents:
        print("Tidak ada dokumen yang berhasil dibaca. Pastikan PDF sudah ada di docs-dir.")
        sys.exit(1)
    print(f"Total halaman dibaca: {len(documents)}")

    # --- 2. Chunking ---
    print("\nChunking dokumen...")
    chunks = chunk_documents(documents)
    print(f"Chunking: {len(chunks)} chunks dihasilkan")

    # --- 3. Embedding ---
    print("\nEmbedding chunks...")
    embedder = get_embedder(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
    )
    vectors = embed_chunks(chunks, embedder)
    print(f"Embedding: {len(vectors)} chunks di-embed")

    # --- 4. Upload ke Qdrant ---
    print("\nUpload ke Qdrant...")
    client = QdrantClient(url=settings.qdrant_url)
    uploaded = upload_chunks(client, chunks, vectors)
    print(f"Upload ke Qdrant: {uploaded} chunks tersimpan")

    print("\nSelesai!")


if __name__ == "__main__":
    main()
