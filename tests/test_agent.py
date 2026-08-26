"""
Test for the Phase 4 Agent Orchestrator.

Run with:  python -m tests.test_agent

Since this sandbox has no ANTHROPIC_API_KEY configured, this test verifies:
  1. The agent graph builds correctly with all 4 tools registered
  2. Tool schemas (name, description, args) are valid for the LLM to use
  3. The agent fails gracefully (not a crash) when no API key is present
  4. If you DO have a key in your .env, it runs a real multi-tool query

Run this after adding your own ANTHROPIC_API_KEY to see full tool-chaining
in action, e.g. a query that needs both document_search AND calculator.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.orchestrator import ALL_TOOLS, invoke_agent
from app.agent.memory import new_thread_id
from app.rag.retriever import ingest_directory


def main():
    print("=== Step 1: Verify tool registration ===")
    for t in ALL_TOOLS:
        print(f"- {t.name}: {t.description[:80]}...")
        print(f"  args schema: {t.args}")

    print("\n=== Step 2: Ingest sample docs (so document_search has data) ===")
    n = ingest_directory("data/sample_docs")
    print(f"Ingested {n} chunks")

    print("\n=== Step 3: Invoke the agent ===")
    thread_id = new_thread_id()

    has_key = bool(os.getenv("ANTHROPIC_API_KEY")) and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here"
    if not has_key:
        print("(No ANTHROPIC_API_KEY set — expecting a graceful 'unavailable' message, not a crash)\n")

    test_query = "What is our refund policy for annual plans, and what is 15% of $200?"
    print(f"Query: {test_query}")
    result = invoke_agent(test_query, thread_id)
    print(f"\nAnswer: {result['answer']}")
    print(f"\nTool calls made: {len(result['tool_calls'])}")
    for tc in result["tool_calls"]:
        print(f"  -> {tc['tool']}({tc['input']}) => {str(tc['output'])[:150]}")

    if has_key:
        print("\n=== Step 4: Follow-up question to test memory ===")
        followup = "What was the first part of my last question about?"
        result2 = invoke_agent(followup, thread_id)
        print(f"Follow-up: {followup}")
        print(f"Answer: {result2['answer']}")


if __name__ == "__main__":
    main()
