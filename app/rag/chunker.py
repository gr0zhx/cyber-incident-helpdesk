import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n", "\n", ". ", " "]

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=SEPARATORS,
    length_function=len,
)

# Heuristic: detect section headers (e.g. "3.1 Containment Strategy")
_HEADER_RE = re.compile(r"^(\d+[\.\d]*\s+[A-Z][^\n]{3,60})$", re.MULTILINE)


def _detect_section_header(text: str) -> str:
    """Return the first section header found in the text, or empty string."""
    match = _HEADER_RE.search(text)
    return match.group(1).strip() if match else ""


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into chunks, preserving and enriching metadata."""
    chunks: list[Document] = []
    chunk_index = 0

    for doc in documents:
        splits = _splitter.split_documents([doc])
        for split in splits:
            split.metadata["section_header"] = _detect_section_header(split.page_content)
            split.metadata["chunk_index"] = chunk_index
            chunks.append(split)
            chunk_index += 1

    return chunks
