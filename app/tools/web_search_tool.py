"""
Web Search Tool for the Agent.

Uses the Tavily API (free tier available at https://tavily.com) to fetch
current/real-time information the LLM's training data wouldn't have.
"""

import os

TOOL_NAME = "web_search"
TOOL_DESCRIPTION = (
    "Search the live web for current information — news, prices, recent "
    "events, or anything that changes over time and isn't in the documents "
    "or the database. Input should be a short search query."
)


def run(query: str, max_results: int = 3) -> str:
    """
    Run a web search and return a summarized list of results.

    Args:
        query: search terms
        max_results: how many results to return (default 3)

    Returns:
        A formatted string of results, or a message if no API key is configured.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "your_tavily_api_key_here":
        return (
            "[Web search unavailable — no TAVILY_API_KEY set in .env. "
            "Get a free key at https://tavily.com and add it to run real searches.]"
        )

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)

        results = response.get("results", [])
        if not results:
            return f"No web results found for: {query}"

        lines = [f"Web search results for: {query}\n"]
        for r in results:
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = (r.get("content", "") or "")[:300]
            lines.append(f"- {title}\n  {url}\n  {content}...\n")

        return "\n".join(lines)

    except Exception as e:
        return f"Web search error: {e}"
