"""
Persistent vector store wrapper around ChromaDB.

Handles adding chunked documents and running similarity search.
"""

import chromadb
from app.rag.embeddings import get_embedding_function
from app.rag.chunker import Chunk


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """
        Embed and store a list of Chunk objects.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        ids = [f"{c.source}::{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [{"source": c.source, "chunk_index": c.chunk_index} for c in chunks]

        # upsert avoids duplicate-id errors if you re-ingest the same file
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def similarity_search(self, query: str, k: int = 4) -> list[dict]:
        """
        Retrieve the top-k most similar chunks to the query.

        Returns:
            List of dicts: {"text": ..., "source": ..., "distance": ...}
        """
        results = self.collection.query(query_texts=[query], n_results=k)

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            output.append({"text": doc, "source": meta.get("source"), "distance": dist})
        return output

    def count(self) -> int:
        return self.collection.count()
