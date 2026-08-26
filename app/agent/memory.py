"""
Conversation memory for the Agent.

LangGraph's checkpointer handles the actual state persistence — this module
just wraps thread-id management so the rest of the app doesn't need to know
about LangGraph's config dict shape.
"""

import uuid


def new_thread_id() -> str:
    """Generate a new conversation thread id (call this once per new chat session)."""
    return str(uuid.uuid4())


def config_for_thread(thread_id: str) -> dict:
    """Build the LangGraph config dict that scopes memory to a given conversation."""
    return {"configurable": {"thread_id": thread_id}}
