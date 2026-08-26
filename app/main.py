"""
Entry point for the GenAI RAG + Agentic AI demo backend.

Phase 1 goal: prove the environment is wired up correctly with a minimal
FastAPI app before we add the RAG pipeline (Phase 2) and Agent (Phase 4).
"""

from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env into environment variables

app = FastAPI(
    title="DocuAgent API",
    description="RAG + Agentic AI demo backend",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "DocuAgent backend is running."}


@app.get("/health")
def health_check():
    """Basic health check that also confirms env vars are loading."""
    return {
        "status": "healthy",
        "anthropic_key_loaded": bool(os.getenv("ANTHROPIC_API_KEY")),
        "tavily_key_loaded": bool(os.getenv("TAVILY_API_KEY")),
    }


# To run locally:
#   uvicorn app.main:app --reload