"""
Script ingesti dokumen ke Qdrant.

Penggunaan:
    # Ingest PDF saja
    python scripts/ingest_knowledge.py

    # Ingest PDF + MITRE ATT&CK STIX
    python scripts/ingest_knowledge.py --stix-file knowledge_base/enterprise-attack.json

    # Ingest STIX saja (skip PDF)
    python scripts/ingest_knowledge.py --stix-only --stix-file knowledge_base/enterprise-attack.json
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
from app.rag.embedder import embed_chunks, upload_chunks
from app.rag.ingestion import ingest_attack_stix, ingest_directory
from app.utils.llm_client import create_embedder


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
    parser.add_argument(
        "--stix-file",
        default=None,
        help="Path ke file STIX JSON ATT&CK (misal: knowledge_base/enterprise-attack.json)",
    )
    parser.add_argument(
        "--stix-only",
        action="store_true",
        help="Hanya ingest STIX, skip PDF",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    settings = get_settings()

    all_documents = []

    # --- 1. Ingesti PDF ---
    if not args.stix_only:
        print("Membaca dokumen PDF...")
        pdf_docs = ingest_directory(args.docs_dir, args.metadata_dir)
        if pdf_docs:
            print(f"Total halaman PDF dibaca: {len(pdf_docs)}")
            all_documents.extend(pdf_docs)
        else:
            print("[INFO] Tidak ada PDF yang berhasil dibaca (pastikan PDF ada di docs-dir).")

    # --- 2. Ingesti MITRE ATT&CK STIX ---
    if args.stix_file:
        stix_path = Path(args.stix_file)
        if not stix_path.exists():
            print(f"[ERROR] File STIX tidak ditemukan: {stix_path}")
            sys.exit(1)
        print(f"\nMemproses MITRE ATT&CK STIX: {stix_path.name} ...")
        stix_docs = ingest_attack_stix(stix_path)
        all_documents.extend(stix_docs)

    if not all_documents:
        print("\nTidak ada dokumen untuk diingest. Gunakan --stix-file atau pastikan PDF tersedia.")
        sys.exit(1)

    print(f"\nTotal dokumen akan diproses: {len(all_documents)}")

    # --- 3. Chunking ---
    print("\nChunking dokumen...")
    chunks = chunk_documents(all_documents)
    print(f"Chunking: {len(chunks)} chunks dihasilkan")

    # --- 4. Embedding ---
    print("\nEmbedding chunks...")
    embedder = create_embedder()
    vectors = embed_chunks(chunks, embedder)
    print(f"Embedding: {len(vectors)} chunks di-embed")

    # --- 5. Upload ke Qdrant ---
    print("\nUpload ke Qdrant...")
    client = QdrantClient(url=settings.qdrant_url)
    uploaded = upload_chunks(client, chunks, vectors)
    print(f"Upload ke Qdrant: {uploaded} chunks tersimpan")

    print("\nSelesai!")


if __name__ == "__main__":
    main()
