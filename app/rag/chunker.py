"""
Chunking strategy for the RAG pipeline.

Splits long documents into overlapping word-based chunks so each chunk is
small enough to embed meaningfully and large enough to retain context.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    chunk_index: int
    source: str


def chunk_text(text: str, source: str = "unknown", chunk_size: int = 300, overlap: int = 50) -> list[Chunk]:
    """
    Split text into overlapping chunks by word count.

    Args:
        text: the raw document text
        source: filename or identifier, stored as metadata
        chunk_size: approx. number of words per chunk
        overlap: number of words repeated between consecutive chunks
                 (preserves context across chunk boundaries)

    Returns:
        List of Chunk objects
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    index = 0
    step = chunk_size - overlap

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(Chunk(text=" ".join(chunk_words), chunk_index=index, source=source))
        index += 1
        start += step

    return chunks


def chunk_documents(documents: dict, chunk_size: int = 300, overlap: int = 50) -> list[Chunk]:
    """
    Chunk multiple documents at once.

    Args:
        documents: dict mapping filename -> raw text (from loader.load_directory)

    Returns:
        Flat list of Chunk objects across all documents
    """
    all_chunks = []
    for filename, text in documents.items():
        all_chunks.extend(chunk_text(text, source=filename, chunk_size=chunk_size, overlap=overlap))
    return all_chunks
