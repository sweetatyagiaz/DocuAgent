"""
High-level retriever API for the RAG pipeline.

Wraps ingestion (load -> chunk -> embed -> store) and retrieval
(similarity search) behind simple functions the rest of the app can call.
"""

from app.rag.loader import load_directory, load_document
from app.rag.chunker import chunk_documents, chunk_text
from app.rag.vector_store import VectorStore

_store = None


def get_store(persist_directory: str = "./chroma_db") -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(persist_directory=persist_directory)
    return _store


def ingest_directory(directory: str, chunk_size: int = 80, overlap: int = 15) -> int:
    """Load every supported doc in a directory, chunk it, and store it."""
    documents = load_directory(directory)
    chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=overlap)
    store = get_store()
    return store.add_chunks(chunks)


def ingest_file(file_path: str, chunk_size: int = 80, overlap: int = 15) -> int:
    """Load a single file, chunk it, and store it (used by the upload widget in Phase 6)."""
    text = load_document(file_path)
    chunks = chunk_text(text, source=file_path.split("/")[-1], chunk_size=chunk_size, overlap=overlap)
    store = get_store()
    return store.add_chunks(chunks)


def retrieve(query: str, k: int = 4) -> list[dict]:
    """Retrieve the top-k most relevant chunks for a query."""
    store = get_store()
    return store.similarity_search(query, k=k)
