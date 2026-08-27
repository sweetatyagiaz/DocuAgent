# DocuAgent — GenAI RAG + Agentic AI Demo

An AI assistant that combines **Retrieval-Augmented Generation (RAG)** with
**Agentic tool-use** — it can answer questions grounded in your own documents,
search the web, run calculations, and query a database, deciding on its own
which tool(s) to use for a given question.

> Status: 🚧 Work in progress — currently in Phase 1 (project skeleton).
> See `GenAI-RAG-Agentic-Demo-Project-Plan` for the full build roadmap.

## Quick Start (current state)

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# then edit .env and add your ANTHROPIC_API_KEY and TAVILY_API_KEY

# 4. Run the backend
uvicorn app.main:app --reload

# 5. Confirm it works
curl http://127.0.0.1:8000/health
```

You should see a JSON response confirming the server is running and whether
your API keys loaded correctly.

## Project Structure

```
genai-rag-agent-demo/
├── app/
│   ├── main.py          # FastAPI entrypoint
│   ├── agent/            # Agent orchestration (LangGraph) — Phase 4
│   ├── rag/               # Document loading, chunking, vector store — Phase 2
│   ├── tools/             # RAG/Web/Calculator/SQL tools — Phase 3
│   └── db/                # SQLite demo database
├── frontend/              # Streamlit chat UI — Phase 6
├── data/sample_docs/      # Drop demo PDFs/docs here
├── tests/                 # Test queries — Phase 7
├── .env.example
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Phase 0: Environment setup
- [x] Phase 1: Project skeleton
- [x] Phase 2: RAG pipeline
- [x] Phase 3: Agent tools
- [x] Phase 4: Agentic orchestration
- [x] Phase 5: Guardrails
- [x] Phase 6: Frontend
- [x] Phase 7: Testing
- [x] Phase 8: Deployment
- [ ] Phase 9: Documentation polish

## Phase 2: RAG Pipeline (done)

The RAG pipeline lives in `app/rag/`:

- `loader.py` — reads .txt/.md/.pdf/.docx files
- `chunker.py` — splits text into overlapping word chunks
- `embeddings.py` — a local, zero-download "hashing trick" embedder (swap in
  `sentence-transformers` or an API embedding model for production-quality
  semantic search — see the docstring in that file)
- `vector_store.py` — ChromaDB wrapper (add / similarity search)
- `retriever.py` — ties ingestion + retrieval together
- `rag_chain.py` — retrieve → build prompt → call Claude → grounded answer

Try it yourself:

```bash
python3 tests/test_rag_pipeline.py
```

This ingests `data/sample_docs/acme_employee_handbook.txt` and runs sample
questions against it, showing which chunk was retrieved for each. If
`ANTHROPIC_API_KEY` isn't set in `.env`, it runs in "dry run" mode (shows
retrieval only); once you add your key, it calls Claude for a real grounded answer.

## Phase 3: Agent Tools (done)

Four tools live in `app/tools/`, each exposing a `TOOL_NAME`, `TOOL_DESCRIPTION`,
and a `run(...)` function — this consistent shape is what lets the Agent
(Phase 4) route between them dynamically:

- `rag_tool.py` (`document_search`) — answers from your ingested documents
- `web_search_tool.py` (`web_search`) — live web search via Tavily API
- `calculator_tool.py` (`calculator`) — safe AST-based math evaluation (no `eval()`)
- `sql_tool.py` (`sql_query`) — read-only queries against the demo SQLite DB
  (`products` and `employees` tables); rejects anything that isn't a single
  `SELECT` statement

Try it yourself:

```bash
python3 -m app.db.init_db        # creates app/db/sample.db with sample data
python3 tests/test_tools.py      # exercises all four tools
```

Web search and RAG-with-generation both work in a graceful "dry run" mode
until you add `TAVILY_API_KEY` / `ANTHROPIC_API_KEY` to `.env` — so you can
verify the plumbing before spending any API credits.

## Phase 4: Agentic Orchestration (done)

`app/agent/` wires the four Phase 3 tools into a LangGraph ReAct agent that
decides — per message — which tool(s) to call, in what order, before
answering:

- `prompts.py` — the system prompt that defines tool-selection logic
  (this is the single most important piece of prompt engineering in the project)
- `memory.py` — thread-id helpers for multi-turn conversation memory
- `orchestrator.py` — builds the LangGraph agent (`create_react_agent`),
  wraps each Phase 3 tool as a LangChain `@tool`, and exposes
  `invoke_agent(message, thread_id)` which returns both the final answer
  **and** the full list of tool calls made (useful for a "show your work"
  UI panel in Phase 6)

Try it yourself:

```bash
python3 tests/test_agent.py
```

This verifies all 4 tools register with valid schemas, then invokes the
agent with a query that needs **two tools in one turn**:
*"What is our refund policy for annual plans, and what is 15% of $200?"*
— which should trigger both `document_search` and `calculator`.

Without `ANTHROPIC_API_KEY` set, it fails gracefully with a clear message
instead of crashing (proving the wiring is correct). Add your key to `.env`
to see live multi-tool reasoning and a memory-aware follow-up question.

## Phase 5: Guardrails & Reliability (done)

Three guardrails added to make the system trustworthy instead of just functional:

1. **Hallucination fallback (`app/rag/rag_chain.py`)** — before calling the LLM,
   a lexical-overlap confidence check compares the query's significant words
   against the top retrieved chunk. If there's not enough overlap, the system
   says plainly "the documents don't cover this" instead of generating an
   answer from a weak/irrelevant match. (We use word overlap rather than raw
   vector distance because this project's local hashing embedder — chosen to
   avoid a network dependency — doesn't separate relevant/irrelevant results
   cleanly enough on distance alone. Swap in a real embedding model and you
   can lean more on distance.)
2. **SQL input sanitization (`app/tools/sql_tool.py`)** — beyond the
   SELECT-only rule from Phase 3, it now also blocks SQL comment syntax
   (`--`, `/* */`, a common injection/obfuscation vector), caps query length,
   and auto-appends a `LIMIT` if the agent doesn't specify one, so a broad
   query can't dump an entire table into the LLM's context.
3. **Decision logging (`app/agent/logger.py`)** — every agent invocation is
   logged to `logs/agent_decisions.jsonl` with the query, which tool(s) were
   called, their inputs/outputs, and the final answer. Great for debugging
   *and* for a live demo ("here's the agent's reasoning trace").

Try it yourself:

```bash
python3 tests/test_guardrails.py
```

This verifies: an off-topic question is correctly flagged as ungrounded, an
on-topic question still passes, five different unsafe/malformed SQL queries
are all rejected with clear reasons, row-limiting works, and decisions are
logged correctly.

## Phase 6: Frontend (done)

`frontend/streamlit_app.py` is a full chat UI:

- **Chat window** with persistent conversation memory (uses the agent's
  thread-id system from Phase 4, with a "New conversation" button to reset it)
- **Document upload widget** in the sidebar — drop a PDF/TXT/DOCX in and it's
  immediately chunked, embedded, and added to the vector store, so you can
  ask questions about it in the very next message. A "Load sample documents"
  button ingests the included Acme handbook with one click for a quick demo.
- **Agent Reasoning panel** — a collapsible expander under each assistant
  reply showing exactly which tool(s) fired, their inputs, and their raw
  outputs, so you can visually prove the agent is really deciding between
  tools rather than following a fixed script

Run it:

```bash
streamlit run frontend/streamlit_app.py
```

Then open the local URL it prints (usually http://localhost:8501). I booted
this exact app in a sandboxed environment and confirmed it serves HTTP 200
with no exceptions in the Streamlit script-run log before shipping it.

## Phase 7: Testing (done)

`tests/test_queries.py` is the consolidated pytest suite covering every
category from the plan — 12 deterministic tests plus 4 live-agent tests:

- **Calculator** (3 expressions + 1 safety check)
- **SQL** (category filter, department filter, aggregate `COUNT`, + 1 rejected
  destructive query)
- **RAG** (2 on-topic questions with correct source attribution, + 1 off-topic
  question correctly refused instead of hallucinated)
- **Web search** (runs without crashing regardless of API key state)
- **Multi-tool agent queries** (RAG+calculator combined, SQL+calculator
  combined, multi-turn memory, and "no tools needed" for a simple greeting)

The 12 deterministic tests need no API key and always run. The 4 agent-level
tests are automatically **skipped with a clear reason** (not failed) when
`ANTHROPIC_API_KEY` isn't set, since verifying which tools an LLM *chooses*
to call requires a live model.

Run it:

```bash
pytest tests/test_queries.py -v
```

I ran this exact suite: **12 passed, 4 skipped, 0 warnings** in this
sandbox (no API key available here). Add your key and rerun to unlock the
4 live multi-tool tests.

## Phase 8: Deployment (done)

Three Docker files, each for a different scenario:

- **`Dockerfile`** — single-process build for hosts that expect one
  container and one file literally named `Dockerfile` (e.g. **Hugging
  Face Spaces'** Docker SDK). Runs the Streamlit frontend on port 7860.
- **`Dockerfile.backend`** — the FastAPI service, for hosts where you want
  a standalone API/health-check endpoint alongside the UI.
- **`Dockerfile.frontend`** — the Streamlit UI as its own image, used
  together with the backend via `docker-compose.yml`.
- **`docker-compose.yml`** — runs backend + frontend together locally,
  sharing a named volume (`chroma_data`) so ingested documents survive
  container restarts.

**Important fix made during this phase:** the SQL tool's demo database
(`app/db/sample.db`) is now regenerated at Docker **build time**
(`RUN python -m app.db.init_db`) rather than relying on a binary file
being committed to the repo — this makes the image fully reproducible
from source alone.

### Run locally with Docker Compose

```bash
docker compose up --build
# Backend:  http://localhost:8000/health
# Frontend: http://localhost:8501
```

### Deploy options

| Host | How |
|---|---|
| **Hugging Face Spaces** | Create a Space with SDK = Docker, push this repo — it picks up the root `Dockerfile` automatically. Add `ANTHROPIC_API_KEY`/`TAVILY_API_KEY` as Space secrets. |
| **Render** | New Web Service → point at your GitHub repo → set Dockerfile path to `Dockerfile` (frontend-only) or configure two services from `Dockerfile.backend`/`Dockerfile.frontend` for the full split architecture. Add env vars in the dashboard. |
| **Railway** | New Project → Deploy from GitHub → Railway auto-detects `docker-compose.yml` and can spin up both services. Add env vars per service. |

**Testing note:** this sandbox has no Docker daemon available (the
package mirror here is incomplete and nested Docker isn't reliable in
this environment), so I couldn't run a literal `docker build`. Instead, I
verified correctness the way that matters most: I reproduced the *exact*
file set each `COPY` instruction would produce in an isolated directory,
regenerated the database the same way `RUN python -m app.db.init_db`
would, and ran both entrypoints (`uvicorn app.main:app` and
`streamlit run frontend/streamlit_app.py`) from that isolated context —
both served traffic correctly. I also fresh-installed `requirements.txt`
into a brand-new virtualenv and reran the full Phase 7 test suite against
it (12 passed, 4 skipped) to confirm the pinned dependency versions
actually work together. Please run `docker compose up --build` yourself
once to confirm on your machine/host, since a Dockerfile can still fail
in ways specific to the Docker layer (base image pulls, layer caching)
that this method can't catch.

## Tech Stack

Claude (Anthropic API) · LangGraph · ChromaDB · FastAPI · Streamlit · SQLite · Docker
