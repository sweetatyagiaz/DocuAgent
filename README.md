# GenAI Project: RAG + Agentic AI System

## 1. Project Overview

**Goal:** Build a portfolio-grade demo that showcases two of the most in-demand GenAI capabilities in one working system:

1. **RAG (Retrieval-Augmented Generation)** — the system answers questions grounded in your own documents instead of hallucinating.
2. **Agentic AI** — the system doesn't just answer questions; it can *plan, decide, and take actions* using tools (search, calculator, APIs, database queries, etc.) autonomously.

**Why this combo is "powerful":** Most demo projects do ONE of these. Combining them shows you can build a system that:
- Knows things (via RAG)
- Does things (via Agents/Tools)
- Reasons about *when* to retrieve vs. *when* to act (via an orchestrator/router)

**End Product:** A chatbot/web app named something like **"DocuAgent"** — an AI assistant that can:
- Answer questions from uploaded PDFs/docs (RAG)
- Search the web for real-time info (Agent + Tool)
- Perform calculations (Agent + Tool)
- Query a small database (Agent + Tool)
- Maintain conversation memory
- Show its reasoning steps (for demo "wow factor")

---

## 2. Architecture Overview

```
                     ┌─────────────────────┐
                     │      User (UI)       │
                     │  Streamlit / React    │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │   Orchestrator/Agent  │
                     │  (LangChain/LangGraph)│
                     └───┬───────┬───────┬───┘
                         │       │       │
             ┌───────────▼┐  ┌───▼────┐ ┌▼─────────────┐
             │ RAG Tool    │  │ Web    │ │ Calculator /  │
             │ (Vector DB  │  │ Search │ │ SQL DB Tool   │
             │ Retriever)  │  │ Tool   │ │               │
             └──────┬──────┘  └────────┘ └───────────────┘
                    │
         ┌──────────▼──────────┐
         │  Vector Store        │
         │ (ChromaDB / FAISS)   │
         └──────────┬───────────┘
                    │
         ┌──────────▼──────────┐
         │ Document Loader &     │
         │ Chunking Pipeline     │
         └───────────────────────┘
```

**Core idea:** The Agent is the "brain." It decides for every user query:
- "Do I need to look this up in the documents?" → uses RAG tool
- "Do I need current/live info?" → uses Web Search tool
- "Do I need to compute something?" → uses Calculator tool
- "Do I need structured data?" → uses SQL tool
- "Can I just answer directly?" → responds directly

---

## 3. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Claude (Anthropic API) or OpenAI GPT | Reasoning + generation |
| Agent Framework | LangGraph (preferred) or LangChain Agents | Orchestration, tool routing, memory |
| Embeddings | Anthropic/OpenAI embeddings or `sentence-transformers` (free/local) | Convert text to vectors |
| Vector DB | ChromaDB (local, easy) or FAISS | Store & retrieve document chunks |
| Document Parsing | `pypdf`, `unstructured`, or `LlamaIndex` loaders | Extract text from PDFs/docs |
| Backend | Python + FastAPI | Serve the agent as an API |
| Frontend | Streamlit (fastest) or React (more "production" looking) | Chat interface |
| Database (for SQL tool) | SQLite | Lightweight structured data demo |
| Memory | LangGraph checkpointer / ConversationBufferMemory | Multi-turn context |
| Deployment | Docker + (Render/Railway/HuggingFace Spaces) | Public demo link |
| Version Control | Git + GitHub | Source control, portfolio visibility |

---

## 4. Step-by-Step Build Plan

### **Phase 0: Setup**
1. Install Python 3.11+, Git, and an IDE (VS Code).
2. Create project folder and virtual environment.
3. Initialize Git repository.
4. Create GitHub repo and connect it (instructions in Section 6 below).
5. Set up `.env` file for API keys (never commit this).

### **Phase 1: Project Skeleton**
6. Create the folder structure (see Section 5).
7. Set up `requirements.txt` with core dependencies.
8. Create a basic FastAPI "hello world" backend to confirm environment works.

### **Phase 2: RAG Pipeline**
9. Build a document loader (accepts PDF/TXT/DOCX).
10. Implement chunking strategy (e.g., 500-token chunks with overlap).
11. Generate embeddings for chunks.
12. Store embeddings in ChromaDB (persistent local store).
13. Build a retriever function (top-k similarity search).
14. Build a basic "RAG chain": retrieve → stuff into prompt → call LLM → return answer.
15. Test RAG in isolation with a sample PDF (e.g., a company handbook or research paper).

### **Phase 3: Tools for the Agent**
16. Build **RAG Tool** (wraps the retriever + LLM chain from Phase 2).
17. Build **Web Search Tool** (using Tavily API or SerpAPI).
18. Build **Calculator Tool** (simple Python eval-safe math tool).
19. Build **SQL Tool** (query a small SQLite DB, e.g., "products" or "employees" table).
20. Give each tool a clear name + description (critical for agent routing accuracy).

### **Phase 4: Agentic Orchestration**
21. Set up LangGraph (or LangChain AgentExecutor) with all 4 tools registered.
22. Define the agent's system prompt: when to use which tool, and how to reason step-by-step (ReAct pattern).
23. Add conversation memory so follow-up questions retain context.
24. Test multi-step queries, e.g.: *"What's our refund policy (RAG), and what's 15% of $200 (Calculator)?"* — confirms the agent can chain multiple tools in one turn.

### **Phase 5: Guardrails & Reliability**
25. Add a fallback: if RAG retrieval confidence is low, tell the user "I don't have this in the documents" instead of hallucinating.
26. Add input validation/sanitization (especially for the SQL and Calculator tools — avoid injection/unsafe eval).
27. Add logging of agent decisions (which tool was picked and why) — great for demo storytelling.

### **Phase 6: Frontend**
28. Build a Streamlit chat UI (fastest path) with:
    - Chat window
    - Document upload widget (adds new files to the vector store live)
    - A collapsible "Agent Reasoning" panel showing which tool was used per step
29. (Optional, more advanced) Replace with a React frontend calling the FastAPI backend for a more "product-like" feel.

### **Phase 7: Testing**
30. Write a test script with 10–15 sample questions covering:
    - Pure RAG questions
    - Pure web-search questions
    - Pure calculation questions
    - Pure SQL questions
    - Multi-tool combined questions
31. Manually verify correctness and tool-selection accuracy.

### **Phase 8: Deployment**
32. Dockerize the app (Dockerfile + docker-compose for backend + frontend).
33. Deploy to a free/low-cost host: HuggingFace Spaces (Streamlit-friendly), Render, or Railway.
34. Add environment variable configuration on the host platform.

### **Phase 9: Documentation & Portfolio Polish**
35. Write a strong `README.md`: problem statement, architecture diagram, setup steps, demo GIF/screenshot, tech stack, and "what I learned."
36. Record a 60–90 second demo video/GIF showing a multi-tool query in action.
37. Push final code to GitHub, tag a `v1.0` release.

---

## 5. Recommended Folder Structure

```
genai-rag-agent-demo/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── agent/
│   │   ├── orchestrator.py     # LangGraph agent definition
│   │   ├── prompts.py          # System prompts
│   │   └── memory.py
│   ├── rag/
│   │   ├── loader.py           # Document loading
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py     # ChromaDB setup
│   │   └── retriever.py
│   ├── tools/
│   │   ├── rag_tool.py
│   │   ├── web_search_tool.py
│   │   ├── calculator_tool.py
│   │   └── sql_tool.py
│   └── db/
│       └── sample.db            # SQLite demo database
├── frontend/
│   └── streamlit_app.py
├── data/
│   └── sample_docs/              # Sample PDFs for RAG demo
├── tests/
│   └── test_queries.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 6. How to Attach a New Repository to GitHub

Once your local project folder is ready:

```bash
# 1. Initialize git in your project folder (if not already done)
git init

# 2. Add a .gitignore (important — don't commit .env, __pycache__, venv, vector DB files)
echo "venv/
.env
__pycache__/
*.pyc
chroma_db/
.DS_Store" > .gitignore

# 3. Stage and commit your files
git add .
git commit -m "Initial commit: project skeleton"

# 4. Create a new empty repository on GitHub.com
#    - Go to github.com → click "+" → "New repository"
#    - Name it (e.g., genai-rag-agent-demo)
#    - DO NOT initialize with a README/gitignore (avoids merge conflicts)
#    - Click "Create repository"

# 5. Connect your local repo to the GitHub repo (GitHub shows you this exact command after creating it)
git remote add origin https://github.com/<your-username>/genai-rag-agent-demo.git

# 6. Rename your branch to main (if needed)
git branch -M main

# 7. Push your code
git push -u origin main
```

**After this**, every future update is just:
```bash
git add .
git commit -m "Describe your change"
git push
```

**Tip:** Use a Personal Access Token (PAT) or SSH key for authentication since GitHub no longer accepts plain passwords over HTTPS.

---

## 7. Success Criteria (What Makes This "Powerful" for a Portfolio)

- ✅ Demonstrates **RAG** (real document grounding, not hardcoded answers)
- ✅ Demonstrates **true agentic behavior** (dynamic tool selection, not a fixed pipeline)
- ✅ Handles **multi-step, multi-tool reasoning** in a single query
- ✅ Has **guardrails** against hallucination and unsafe tool use
- ✅ Is **deployed live** with a public link
- ✅ Has a **clean README + architecture diagram** — recruiters/engineers judge projects by README quality first

---

## Next Steps

Once you confirm this plan, we'll proceed **step by step starting with Phase 0/1**: environment setup, folder structure, and initializing the GitHub repository — then move into building the RAG pipeline.
