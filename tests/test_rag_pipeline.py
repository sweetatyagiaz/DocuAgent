"""
Manual/automated test for the Phase 2 RAG pipeline.

Run with:  python -m tests.test_rag_pipeline
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.retriever import ingest_directory, retrieve
from app.rag.rag_chain import answer_question

DATA_DIR = "data/sample_docs"

TEST_QUERIES = [
    "What is the refund policy for annual plans?",
    "How many PTO days do employees get?",
    "Do I need approval to work fully remote?",
    "What is the capital of France?",  # should show low relevance / not covered
]


def main():
    print("=== Step 1: Ingesting sample documents ===")
    num_chunks = ingest_directory(DATA_DIR)
    print(f"Ingested {num_chunks} chunks from '{DATA_DIR}'\n")

    print("=== Step 2: Running retrieval tests ===\n")
    for query in TEST_QUERIES:
        print(f"Q: {query}")
        results = retrieve(query, k=2)
        for r in results:
            preview = r["text"][:120].replace("\n", " ")
            print(f"   [{r['source']} | dist={r['distance']:.4f}] {preview}...")
        print()

    print("=== Step 3: Full RAG chain (retrieve + prompt build) ===\n")
    result = answer_question(TEST_QUERIES[0], k=2)
    print(f"Q: {TEST_QUERIES[0]}")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")


if __name__ == "__main__":
    main()
