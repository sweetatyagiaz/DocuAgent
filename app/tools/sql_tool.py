"""
SQL Tool for the Agent.

Lets the agent answer questions about structured data (products, employees)
by running read-only SQL queries against the demo SQLite database.

SAFETY: only SELECT statements are allowed. Anything else (INSERT, UPDATE,
DELETE, DROP, ATTACH, PRAGMA, multiple statements, etc.) is rejected before
it ever touches the database.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "sample.db")

TOOL_NAME = "sql_query"
TOOL_DESCRIPTION = (
    "Run a read-only SQL SELECT query against the demo database to answer "
    "questions about structured data. Available tables: "
    "products(id, name, category, price, stock), "
    "employees(id, name, department, hire_date, salary). "
    "Only SELECT statements are permitted."
)

_DISALLOWED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|PRAGMA|CREATE|REPLACE|EXEC)\b",
    re.IGNORECASE,
)


def _is_safe_select(query: str) -> tuple[bool, str]:
    stripped = query.strip().rstrip(";")

    if ";" in stripped:
        return False, "Multiple statements are not allowed."
    if not stripped.upper().startswith("SELECT"):
        return False, "Only SELECT statements are allowed."
    if _DISALLOWED_KEYWORDS.search(stripped):
        return False, "Query contains a disallowed keyword."
    return True, ""


def run(query: str, db_path: str = DB_PATH) -> str:
    """
    Execute a read-only SQL query and return the results as a formatted string.

    Args:
        query: a SELECT statement, e.g. "SELECT name, price FROM products WHERE category = 'Hardware'"

    Returns:
        A human-readable string of results, or an error message.
    """
    is_safe, reason = _is_safe_select(query)
    if not is_safe:
        return f"Query rejected: {reason} Only single SELECT statements are permitted."

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "Query ran successfully but returned no rows."

        columns = rows[0].keys()
        header = " | ".join(columns)
        lines = [header, "-" * len(header)]
        for row in rows:
            lines.append(" | ".join(str(row[c]) for c in columns))
        return "\n".join(lines)

    except sqlite3.Error as e:
        return f"SQL error: {e}"
