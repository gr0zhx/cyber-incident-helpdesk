import uuid
from typing import Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    PayloadSchemaType,
)

COLLECTION_NAME = "cybersecurity_knowledge"
VECTOR_SIZE = 1536
BATCH_SIZE = 100


def get_embedder(api_key: str, model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    return OpenAIEmbeddings(api_key=api_key, model=model)


def embed_chunks(
    chunks: list[Document],
    embedder: OpenAIEmbeddings,
) -> list[list[float]]:
    """Embed chunks in batches of BATCH_SIZE to respect rate limits."""
    all_vectors: list[list[float]] = []
    total = len(chunks)

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c.page_content for c in batch]
        vectors = embedder.embed_documents(texts)
        all_vectors.extend(vectors)
        print(f"  Embedding batch {i // BATCH_SIZE + 1}/{(total + BATCH_SIZE - 1) // BATCH_SIZE} "
              f"({min(i + BATCH_SIZE, total)}/{total} chunks)")

    return all_vectors


def ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it does not exist, with full-text index."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        # Full-text index for keyword search
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="content",
            field_schema=PayloadSchemaType.TEXT,
        )
        print(f"[QDRANT] Collection '{COLLECTION_NAME}' dibuat.")
    else:
        print(f"[QDRANT] Collection '{COLLECTION_NAME}' sudah ada.")


def _build_payload(chunk: Document) -> dict[str, Any]:
    meta = chunk.metadata
    return {
        "content": chunk.page_content,
        "doc_id": meta.get("doc_id", ""),
        "doc_title": meta.get("doc_title", ""),
        "source_framework": meta.get("source_framework", ""),
        "language": meta.get("language", "en"),
        "incident_types": meta.get("incident_types", []),
        "page_number": meta.get("page", meta.get("page_number", 0)),
        "section_header": meta.get("section_header", ""),
        "chunk_index": meta.get("chunk_index", 0),
    }


def upload_chunks(
    client: QdrantClient,
    chunks: list[Document],
    vectors: list[list[float]],
) -> int:
    """Upload chunks with their embeddings to Qdrant in batches."""
    ensure_collection(client)

    uploaded = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i : i + BATCH_SIZE]
        batch_vectors = vectors[i : i + BATCH_SIZE]

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload=_build_payload(chunk),
            )
            for chunk, vec in zip(batch_chunks, batch_vectors)
        ]

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        uploaded += len(points)

    return uploaded
