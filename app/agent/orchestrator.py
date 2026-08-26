"""
Agent Orchestrator — the "brain" of the project.

Wires the four tools from Phase 3 into a LangGraph ReAct agent that decides,
per user message, which tool(s) to call (zero, one, or several) before
answering. Conversation memory is handled via LangGraph's checkpointer, keyed
by thread_id so multiple users/sessions don't share state.
"""

import os
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.memory import config_for_thread
from app.tools import calculator_tool, sql_tool, web_search_tool, rag_tool


# --- Wrap our Phase 3 tools as LangChain tools -----------------------------
# Each @tool-decorated function's docstring IS the description the LLM sees
# when deciding whether to call it, so we reuse the same TOOL_DESCRIPTION
# strings defined in Phase 3 to keep a single source of truth.

@tool(calculator_tool.TOOL_NAME, description=calculator_tool.TOOL_DESCRIPTION)
def calculator(expression: str) -> str:
    return calculator_tool.run(expression)


@tool(sql_tool.TOOL_NAME, description=sql_tool.TOOL_DESCRIPTION)
def sql_query(query: str) -> str:
    return sql_tool.run(query)


@tool(web_search_tool.TOOL_NAME, description=web_search_tool.TOOL_DESCRIPTION)
def web_search(query: str) -> str:
    return web_search_tool.run(query)


@tool(rag_tool.TOOL_NAME, description=rag_tool.TOOL_DESCRIPTION)
def document_search(query: str) -> str:
    return rag_tool.run(query)


ALL_TOOLS = [calculator, sql_query, web_search, document_search]

_agent = None
_checkpointer = MemorySaver()


def build_agent():
    """
    Builds (once, then caches) the LangGraph ReAct agent.

    Raises:
        RuntimeError if ANTHROPIC_API_KEY is not configured — callers should
        catch this and show a friendly message rather than crash.
    """
    global _agent
    if _agent is not None:
        return _agent

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add a real key to your .env file to run the agent."
        )

    from langchain_anthropic import ChatAnthropic

    model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, api_key=api_key)

    _agent = create_react_agent(
        model,
        tools=ALL_TOOLS,
        prompt=AGENT_SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )
    return _agent


def invoke_agent(message: str, thread_id: str) -> dict:
    """
    Send a message to the agent and get back the final answer plus the
    sequence of tool calls it made (great for the "Agent Reasoning" panel
    in the Phase 6 frontend).

    Returns:
        {"answer": str, "tool_calls": [{"tool": str, "input": ..., "output": str}, ...]}
    """
    try:
        agent = build_agent()
    except RuntimeError as e:
        return {"answer": f"[Agent unavailable: {e}]", "tool_calls": []}

    config = config_for_thread(thread_id)
    result = agent.invoke({"messages": [{"role": "user", "content": message}]}, config=config)

    messages = result["messages"]
    tool_calls = []
    final_answer = ""

    for i, msg in enumerate(messages):
        msg_type = getattr(msg, "type", None)
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tool_calls.append({"tool": tc["name"], "input": tc["args"], "output": None})
        elif msg_type == "tool":
            # attach the observation to the most recent matching tool call
            for tc in reversed(tool_calls):
                if tc["output"] is None:
                    tc["output"] = msg.content
                    break
        elif msg_type == "ai" and not getattr(msg, "tool_calls", None):
            final_answer = msg.content

    return {"answer": final_answer, "tool_calls": tool_calls}
