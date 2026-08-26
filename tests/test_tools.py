"""
Manual/automated test for the Phase 3 Agent tools.

Run with:  python -m tests.test_tools
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools import calculator_tool, sql_tool, web_search_tool, rag_tool
from app.rag.retriever import ingest_directory


def section(title):
    print(f"\n=== {title} ===")


def main():
    section("Calculator Tool")
    print("15% of 200 ->", calculator_tool.run("200 * 0.15"))
    print("(45 + 55) / 2 ->", calculator_tool.run("(45 + 55) / 2"))
    print("Invalid expression 'import os' ->", calculator_tool.run("import os"))
    print("Division by zero ->", calculator_tool.run("5 / 0"))

    section("SQL Tool")
    print("All hardware products:")
    print(sql_tool.run("SELECT name, price, stock FROM products WHERE category = 'Hardware'"))
    print("\nEngineering employees:")
    print(sql_tool.run("SELECT name, hire_date, salary FROM employees WHERE department = 'Engineering'"))
    print("\nRejected unsafe query (DROP TABLE):")
    print(sql_tool.run("DROP TABLE products"))

    section("Web Search Tool")
    print(web_search_tool.run("latest AI model releases 2026"))

    section("RAG Tool (document_search)")
    ingest_directory("data/sample_docs")
    print(rag_tool.run("What is the refund policy for annual plans?"))

    section("Tool metadata (used by the Agent for routing in Phase 4)")
    for tool in [calculator_tool, sql_tool, web_search_tool, rag_tool]:
        print(f"- {tool.TOOL_NAME}: {tool.TOOL_DESCRIPTION}")


if __name__ == "__main__":
    main()
