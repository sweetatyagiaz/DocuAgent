"""
RAG Tool for the Agent.

Wraps the Phase 2 RAG chain (app/rag/rag_chain.py) so the agent can call it
like any other tool to answer questions grounded in the ingested documents.
"""

from app.rag.rag_chain import answer_question

TOOL_NAME = "document_search"
TOOL_DESCRIPTION = (
    "Answer questions using the content of the user's uploaded documents "
    "(company handbook, policies, reports, etc.). Use this whenever the "
    "question could be answered from internal documents rather than "
    "general knowledge, live web data, or the structured database."
)


def run(query: str, k: int = 4) -> str:
    """
    Args:
        query: the user's question

    Returns:
        A formatted string with the answer and cited sources.
    """
    result = answer_question(query, k=k)
    sources = ", ".join(result["sources"]) if result["sources"] else "none"
    return f"{result['answer']}\n\n(Sources: {sources})"
