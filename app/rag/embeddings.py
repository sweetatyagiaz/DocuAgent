"""
Embedding function for the RAG pipeline.

DEMO NOTE:
ChromaDB's built-in default embedder downloads a small ONNX model from the
internet on first use. That's fine on a normal machine, but it makes the
demo fragile in restricted/offline network environments (e.g. corporate
firewalls, sandboxes). To keep this project 100% self-contained and
runnable with zero downloads, we implement a simple local "hashing trick"
bag-of-words embedding here instead.

This is intentionally a demo-grade embedder — it captures keyword/term
overlap well (good enough to demonstrate the RAG pipeline end-to-end) but
won't capture deep semantic meaning the way a trained model does.

>>> For production quality, swap this out for a real embedding model, e.g.:
    - sentence-transformers (local, free, already in requirements.txt)
    - Anthropic/OpenAI/Voyage embeddings API (best quality, needs an API key)
  Only this file needs to change — vector_store.py and retriever.py don't care
  which embedding function is plugged in.
"""

import hashlib
import re
import numpy as np
from chromadb import Documents, EmbeddingFunction, Embeddings

EMBEDDING_DIM = 384  # matches common model output size, arbitrary otherwise

_word_re = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _word_re.findall(text.lower())


def _hash_embed(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    tokens = _tokenize(text)
    if not tokens:
        return vec

    for token in tokens:
        # stable hash -> bucket index (Python's hash() is randomized per-process, so use md5)
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        index = int(digest, 16) % dim
        # sign bit reduces hash-collision bias (standard hashing-trick technique)
        sign = 1.0 if int(digest, 16) % 2 == 0 else -1.0
        vec[index] += sign

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


class LocalHashingEmbeddingFunction(EmbeddingFunction):
    """A zero-dependency, zero-download embedding function for offline demos."""

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        return [_hash_embed(text, dim=self.dim) for text in input]

    @staticmethod
    def name() -> str:
        return "local-hashing-embedding-v1"

    def get_config(self) -> dict:
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(config: dict) -> "LocalHashingEmbeddingFunction":
        return LocalHashingEmbeddingFunction(dim=config.get("dim", EMBEDDING_DIM))


def get_embedding_function():
    return LocalHashingEmbeddingFunction()
