"""
Decision logger for the Agent (Phase 5).

Records which tool(s) the agent chose for each query, with inputs/outputs
and a timestamp. This is genuinely useful for two things:
  1. Debugging — see exactly why the agent did (or didn't) call a tool
  2. Demo storytelling — show a live log of the agent's reasoning trace
     during a walkthrough, which is a great "wow" moment for reviewers
"""

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
LOG_PATH = os.path.join(LOG_DIR, "agent_decisions.jsonl")


def log_decision(thread_id: str, query: str, tool_calls: list[dict], answer: str) -> None:
    """Append one structured log entry as a JSON line."""
    os.makedirs(LOG_DIR, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thread_id": thread_id,
        "query": query,
        "tools_used": [tc["tool"] for tc in tool_calls],
        "tool_calls": tool_calls,
        "answer": answer,
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_recent_decisions(limit: int = 20) -> list[dict]:
    """Read the most recent N logged decisions (for a UI debug panel)."""
    if not os.path.exists(LOG_PATH):
        return []

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = [json.loads(line) for line in lines[-limit:]]
    return list(reversed(entries))
