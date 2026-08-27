"""
Phase 7: Consolidated test suite.

Covers the plan's required categories with ~15 sample queries:
  - Pure RAG questions
  - Pure calculation questions
  - Pure SQL questions
  - Pure web-search questions
  - Multi-tool combined questions

Run with:
    pytest tests/test_queries.py -v

DESIGN NOTE: Tool-level tests (calculator/SQL/RAG-retrieval) run the actual
tool functions directly and are fully deterministic — no API key required,
so they always run in CI. Full multi-tool AGENT tests require a live
ANTHROPIC_API_KEY (the agent's LLM decides which tools to call), so those
are automatically skipped with a clear reason if no key is configured,
rather than failing or being silently wrong.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.tools import calculator_tool, sql_tool, web_search_tool
from app.rag.retriever import ingest_directory
from app.rag.rag_chain import answer_question
from app.agent.orchestrator import invoke_agent
from app.agent.memory import new_thread_id

HAS_API_KEY = bool(os.getenv("ANTHROPIC_API_KEY")) and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here"
skip_no_key = pytest.mark.skipif(not HAS_API_KEY, reason="ANTHROPIC_API_KEY not set — agent tests need a live LLM")


@pytest.fixture(scope="module", autouse=True)
def ingest_sample_docs():
    ingest_directory("data/sample_docs")


# ---------------------------------------------------------------------------
# Category 1: Pure calculation queries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expression,expected", [
    ("200 * 0.15", "30.0"),
    ("(45 + 55) / 2", "50.0"),
    ("2 ** 10", "1024"),
])
def test_calculator_queries(expression, expected):
    assert calculator_tool.run(expression) == expected


def test_calculator_rejects_unsafe_input():
    result = calculator_tool.run("__import__('os').system('ls')")
    assert result.startswith("Error")


# ---------------------------------------------------------------------------
# Category 2: Pure SQL queries
# ---------------------------------------------------------------------------

def test_sql_query_products_by_category():
    result = sql_tool.run("SELECT name FROM products WHERE category = 'Hardware'")
    assert "Wireless Mouse" in result
    assert "Acme Pro Subscription" not in result  # that's Software, shouldn't appear


def test_sql_query_employees_by_department():
    result = sql_tool.run("SELECT name FROM employees WHERE department = 'Engineering'")
    assert "Priya Sharma" in result
    assert "Daniel Kim" not in result  # Sales, shouldn't appear


def test_sql_query_aggregate():
    result = sql_tool.run("SELECT COUNT(*) as total FROM products")
    assert "7" in result


def test_sql_rejects_destructive_query():
    result = sql_tool.run("DELETE FROM products WHERE id = 1")
    assert result.startswith("Query rejected")


# ---------------------------------------------------------------------------
# Category 3: Pure RAG (document) queries
# ---------------------------------------------------------------------------

def test_rag_refund_policy_question():
    result = answer_question("What is the refund policy for annual plans?")
    assert result["grounded"] is True
    assert "acme_employee_handbook.txt" in result["sources"]


def test_rag_pto_question():
    result = answer_question("How many PTO days do employees get?")
    assert result["grounded"] is True


def test_rag_off_topic_question_is_not_hallucinated():
    result = answer_question("What is the capital of Mongolia?")
    assert result["grounded"] is False
    assert "don't" in result["answer"].lower() or "not" in result["answer"].lower()


# ---------------------------------------------------------------------------
# Category 4: Pure web-search queries
# ---------------------------------------------------------------------------

def test_web_search_runs_without_crashing():
    # Works whether or not TAVILY_API_KEY is set — either returns real
    # results or a clear "unavailable" message, never an exception.
    result = web_search_tool.run("current weather in Tokyo")
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Category 5: Multi-tool combined queries (require a live agent + API key)
# ---------------------------------------------------------------------------

@skip_no_key
def test_agent_combines_rag_and_calculator():
    thread_id = new_thread_id()
    result = invoke_agent(
        "What's our refund policy, and what's 15% of $200?", thread_id
    )
    tools_used = {tc["tool"] for tc in result["tool_calls"]}
    assert "document_search" in tools_used
    assert "calculator" in tools_used


@skip_no_key
def test_agent_combines_sql_and_calculator():
    thread_id = new_thread_id()
    result = invoke_agent(
        "How many hardware products do we have, and what's that number doubled?", thread_id
    )
    tools_used = {tc["tool"] for tc in result["tool_calls"]}
    assert "sql_query" in tools_used
    assert "calculator" in tools_used


@skip_no_key
def test_agent_remembers_context_across_turns():
    thread_id = new_thread_id()
    invoke_agent("What is our refund policy?", thread_id)
    followup = invoke_agent("Summarize what you just told me in one sentence.", thread_id)
    assert len(followup["answer"]) > 0


@skip_no_key
def test_agent_answers_simple_greeting_without_tools():
    thread_id = new_thread_id()
    result = invoke_agent("Hello, what can you help me with?", thread_id)
    # A simple greeting shouldn't need any tools
    assert len(result["tool_calls"]) == 0
