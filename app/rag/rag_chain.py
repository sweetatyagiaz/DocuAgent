"""
RAG chain: retrieve relevant chunks, stuff them into a prompt, call Claude,
and return a grounded answer.

This is also exposed as a Tool in app/tools/rag_tool.py for the Agent (Phase 3/4).

GUARDRAIL (Phase 5): before calling the LLM, we check whether the retrieved
chunks are actually relevant to the query using lexical overlap between the
query's significant words and the retrieved text. This project uses a
lightweight local hashing embedder (see embeddings.py) that's great for
avoiding network dependencies but doesn't separate relevant/irrelevant
results as cleanly as a trained model would on raw vector distance alone —
so a word-overlap check is a more reliable confidence signal here. If you
swap in a real embedding model, you can lean more on `distance` and less on
this overlap check.
"""

import os
import re
from app.rag.retriever import retrieve

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY the
provided context from the user's documents. If the answer is not contained in the context,
say clearly that the documents don't cover this — do NOT make up an answer.

Always mention which source file(s) you drew from when possible."""

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "how", "who", "of", "in",
    "to", "on", "for", "and", "or", "me", "tell", "about", "does", "do", "i", "my",
    "it", "this", "that", "with", "our", "your", "can", "will", "be",
}

MIN_OVERLAP_RATIO = 0.34  # at least ~1/3 of the query's significant words must appear
                          # in the top retrieved chunk, otherwise we don't trust it


def _significant_words(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _confidence_check(query: str, chunks: list[dict]) -> bool:
    """Returns True if the top chunk seems genuinely relevant to the query."""
    if not chunks:
        return False
    query_words = _significant_words(query)
    if not query_words:
        return True  # can't judge (e.g. query was all stopwords) — don't block
    top_chunk_words = _significant_words(chunks[0]["text"])
    overlap = len(query_words & top_chunk_words) / len(query_words)
    return overlap >= MIN_OVERLAP_RATIO


def build_prompt(query: str, chunks: list[dict]) -> str:
    if not chunks:
        context = "(No relevant context was found in the documents.)"
    else:
        context = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )

    return f"""Context from documents:
{context}

Question: {query}

Answer the question using only the context above."""


def answer_question(query: str, k: int = 4) -> dict:
    """
    Full RAG flow: retrieve -> confidence check -> prompt -> call Claude -> return answer + sources.

    Returns:
        {"answer": str, "sources": list[str], "retrieved_chunks": list[dict], "grounded": bool}
    """
    chunks = retrieve(query, k=k)

    if not _confidence_check(query, chunks):
        return {
            "answer": "I don't see anything in the uploaded documents that answers this — "
                      "it may not be covered, or you may need to upload the relevant document.",
            "sources": [],
            "retrieved_chunks": chunks,
            "grounded": False,
        }

    prompt = build_prompt(query, chunks)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        # No key configured yet — return the retrieval result so the
        # pipeline is still verifiable end-to-end without a live API call.
        return {
            "answer": "[DRY RUN — no ANTHROPIC_API_KEY set. Retrieval worked; "
                      "add your key in .env to get a generated answer.]",
            "sources": list({c["source"] for c in chunks}),
            "retrieved_chunks": chunks,
            "grounded": True,
        }

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=RAG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    return {
        "answer": answer_text,
        "sources": list({c["source"] for c in chunks}),
        "retrieved_chunks": chunks,
        "grounded": True,
    }

