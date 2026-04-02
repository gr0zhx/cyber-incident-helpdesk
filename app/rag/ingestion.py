import json
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_metadata(metadata_path: str | Path) -> dict:
    with open(metadata_path, encoding="utf-8") as f:
        return json.load(f)


def ingest_document(pdf_path: str | Path, metadata: dict) -> list[Document]:
    """Load a PDF and return one Document per page with enriched metadata."""
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()

    enriched: list[Document] = []
    for page in pages:
        page.metadata.update(
            {
                "doc_id": metadata["doc_id"],
                "doc_title": metadata["doc_title"],
                "source_framework": metadata["source_framework"],
                "language": metadata.get("language", "en"),
                "incident_types": metadata.get("incident_types", []),
                "version": metadata.get("version", ""),
            }
        )
        enriched.append(page)
    return enriched


def ingest_directory(
    docs_dir: str | Path,
    metadata_dir: str | Path,
) -> list[Document]:
    """Ingest all PDFs in docs_dir whose metadata exists in metadata_dir."""
    docs_dir = Path(docs_dir)
    metadata_dir = Path(metadata_dir)

    all_documents: list[Document] = []

    for meta_file in sorted(metadata_dir.glob("*.json")):
        meta = load_metadata(meta_file)
        pdf_path = docs_dir / meta["filename"]

        if not pdf_path.exists():
            print(f"[SKIP] PDF tidak ditemukan: {pdf_path}")
            continue

        print(f"[READ] {meta['doc_title']} ({pdf_path.name})")
        docs = ingest_document(pdf_path, meta)
        all_documents.extend(docs)

    return all_documents
