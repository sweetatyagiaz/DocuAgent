"""
RAG chain: retrieve relevant chunks, stuff them into a prompt, call Claude,
and return a grounded answer.

This is also exposed as a Tool in app/tools/rag_tool.py for the Agent (Phase 3/4).
"""

import os
from app.rag.retriever import retrieve

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY the
provided context from the user's documents. If the answer is not contained in the context,
say clearly that the documents don't cover this — do NOT make up an answer.

Always mention which source file(s) you drew from when possible."""


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
    Full RAG flow: retrieve -> prompt -> call Claude -> return answer + sources.

    Returns:
        {"answer": str, "sources": list[str], "retrieved_chunks": list[dict]}
    """
    chunks = retrieve(query, k=k)
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
    }
