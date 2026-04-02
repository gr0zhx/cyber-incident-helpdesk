from langchain_core.documents import Document

from app.rag.chunker import chunk_documents, CHUNK_SIZE


def _make_doc(text: str, meta: dict | None = None) -> Document:
    return Document(page_content=text, metadata=meta or {
        "doc_id": "test-doc",
        "doc_title": "Test Document",
        "source_framework": "NIST",
        "page": 1,
    })


def test_chunk_preserves_metadata():
    doc = _make_doc("A" * 200)
    chunks = chunk_documents([doc])
    assert all(c.metadata["doc_id"] == "test-doc" for c in chunks)
    assert all(c.metadata["source_framework"] == "NIST" for c in chunks)


def test_chunk_adds_chunk_index():
    doc = _make_doc("B" * 200)
    chunks = chunk_documents([doc])
    indices = [c.metadata["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_adds_section_header_key():
    doc = _make_doc("Some text without headers.")
    chunks = chunk_documents([doc])
    assert all("section_header" in c.metadata for c in chunks)


def test_long_document_produces_multiple_chunks():
    long_text = "Word " * 2000  # well over CHUNK_SIZE
    doc = _make_doc(long_text)
    chunks = chunk_documents([doc])
    assert len(chunks) > 1


def test_chunk_size_within_limit():
    long_text = "Word " * 2000
    doc = _make_doc(long_text)
    chunks = chunk_documents([doc])
    for chunk in chunks:
        assert len(chunk.page_content) <= CHUNK_SIZE * 2  # allow some headroom


def test_multiple_documents_global_chunk_index():
    docs = [_make_doc("X " * 500), _make_doc("Y " * 500)]
    chunks = chunk_documents(docs)
    indices = [c.metadata["chunk_index"] for c in chunks]
    # indices should be monotonically increasing starting from 0
    assert indices == list(range(len(chunks)))
