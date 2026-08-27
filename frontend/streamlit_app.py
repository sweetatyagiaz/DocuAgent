"""
Streamlit frontend for DocuAgent (Phase 6).

Run with:
    streamlit run frontend/streamlit_app.py

Features:
- Chat window with conversation memory (via the agent's thread_id)
- Document upload widget that ingests new files into the vector store live
- A collapsible "Agent Reasoning" panel showing which tool(s) fired per turn
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.agent.orchestrator import invoke_agent
from app.agent.memory import new_thread_id
from app.rag.retriever import ingest_file, ingest_directory, get_store

st.set_page_config(page_title="DocuAgent", page_icon="🤖", layout="wide")

# --- Session state init -----------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = new_thread_id()
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"/"assistant", "content": str, "tool_calls": [...]}
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []

# --- Sidebar: document upload + status --------------------------------------
with st.sidebar:
    st.header("📄 Documents")
    st.caption("Upload files to add them to the agent's knowledge base (RAG).")

    if st.button("📥 Load sample documents (Acme handbook)", use_container_width=True):
        with st.spinner("Ingesting data/sample_docs/..."):
            n = ingest_directory("data/sample_docs")
        st.session_state.ingested_files.append(f"sample_docs/ ({n} chunks)")
        st.success(f"Ingested {n} chunks from the sample documents.")


    uploaded_files = st.file_uploader(
        "Upload PDF, TXT, or DOCX files",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name in st.session_state.ingested_files:
                continue
            with tempfile.NamedTemporaryFile(
                delete=False, suffix="_" + uploaded_file.name
            ) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                n_chunks = ingest_file(tmp_path)
                # ingest_file uses the filename portion of the temp path as the source,
                # so re-ingest with the original name for a cleaner citation
                os.rename(tmp_path, os.path.join(os.path.dirname(tmp_path), uploaded_file.name))
                st.session_state.ingested_files.append(uploaded_file.name)
                st.success(f"Ingested '{uploaded_file.name}' ({n_chunks} chunks)")
            except Exception as e:
                st.error(f"Failed to ingest {uploaded_file.name}: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    if st.session_state.ingested_files:
        st.write("**Uploaded this session:**")
        for f in st.session_state.ingested_files:
            st.write(f"- {f}")

    try:
        doc_count = get_store().count()
        st.caption(f"Vector store contains {doc_count} chunks total (including sample docs).")
    except Exception:
        pass

    st.divider()
    st.header("🛠️ Available Tools")
    st.markdown(
        "- **document_search** — your uploaded documents\n"
        "- **web_search** — live web (needs `TAVILY_API_KEY`)\n"
        "- **calculator** — safe math evaluation\n"
        "- **sql_query** — demo products/employees database"
    )

    st.divider()
    if st.button("🔄 New conversation"):
        st.session_state.thread_id = new_thread_id()
        st.session_state.messages = []
        st.rerun()

    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY")) and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here"
    if not api_key_set:
        st.warning("⚠️ ANTHROPIC_API_KEY not set in .env — the agent will not be able to respond. "
                   "Add your key and restart the app.")

# --- Main chat area ----------------------------------------------------------
st.title("🤖 DocuAgent")
st.caption("RAG + Agentic AI demo — ask about your documents, do math, query the database, or search the web.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            with st.expander(f"🔍 Agent Reasoning ({len(msg['tool_calls'])} tool call(s))"):
                for tc in msg["tool_calls"]:
                    st.markdown(f"**Tool:** `{tc['tool']}`")
                    st.markdown(f"**Input:** `{tc['input']}`")
                    output_preview = str(tc.get("output", ""))[:500]
                    st.markdown(f"**Output:** {output_preview}")
                    st.markdown("---")

user_input = st.chat_input("Ask about your documents, do math, query data, or search the web...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = invoke_agent(user_input, st.session_state.thread_id)
        st.markdown(result["answer"])
        if result["tool_calls"]:
            with st.expander(f"🔍 Agent Reasoning ({len(result['tool_calls'])} tool call(s))"):
                for tc in result["tool_calls"]:
                    st.markdown(f"**Tool:** `{tc['tool']}`")
                    st.markdown(f"**Input:** `{tc['input']}`")
                    output_preview = str(tc.get("output", ""))[:500]
                    st.markdown(f"**Output:** {output_preview}")
                    st.markdown("---")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "tool_calls": result["tool_calls"],
    })
