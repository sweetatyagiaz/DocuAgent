"""
Test for Phase 5 guardrails.

Run with: python -m tests.test_guardrails
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.retriever import ingest_directory
from app.rag.rag_chain import answer_question
from app.tools import sql_tool
from app.agent.logger import log_decision, read_recent_decisions


def section(title):
    print(f"\n=== {title} ===")


def main():
    ingest_directory("data/sample_docs")

    section("1. RAG hallucination fallback (off-topic question)")
    result = answer_question("What is the airspeed velocity of an unladen swallow?")
    print(f"grounded={result['grounded']}")
    print(f"answer: {result['answer']}")
    assert result["grounded"] is False, "Expected off-topic question to be flagged as not grounded"

    section("2. RAG hallucination fallback (on-topic question still works)")
    result2 = answer_question("What is the refund policy?")
    print(f"grounded={result2['grounded']}")
    print(f"answer: {result2['answer'][:100]}")
    assert result2["grounded"] is True, "Expected on-topic question to pass the confidence check"

    section("3. SQL injection / unsafe query attempts")
    attempts = [
        "SELECT * FROM products; DROP TABLE products;",
        "SELECT * FROM products -- comment injection",
        "SELECT * FROM products /* block comment */",
        "DROP TABLE employees",
        "SELECT * FROM employees" * 50,  # too long
    ]
    for q in attempts:
        result = sql_tool.run(q)
        print(f"Query: {q[:60]}...")
        print(f"  -> {result[:80]}")
        assert result.startswith("Query rejected"), f"Expected rejection for: {q[:60]}"

    section("4. SQL row limit enforcement")
    result = sql_tool.run("SELECT * FROM products")
    print(result[:200])

    section("5. Decision logging")
    log_decision("test-thread", "test query", [{"tool": "calculator", "input": {"expression": "1+1"}, "output": "2"}], "The answer is 2")
    recent = read_recent_decisions(limit=1)
    print(f"Logged entry: {recent[0] if recent else 'NONE'}")
    assert len(recent) == 1 and recent[0]["query"] == "test query"

    print("\n✅ All guardrail checks passed.")


if __name__ == "__main__":
    main()
