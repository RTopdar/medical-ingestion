#!/usr/bin/env python3
"""Interactive BM25 search demo — ask questions and get top-5 chunks with scores."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from retrieval.bm25 import BM25Index


def search_bm25(index: BM25Index, query: str, top_k: int = 5) -> None:
    """Search the BM25 index and display results."""
    results = index.search(query, top_k=top_k)

    if not results:
        print("\n❌ No results found.\n")
        return

    print(f"\n✅ Found {len(results)} result(s):\n")
    print("-" * 80)

    for i, (entry, score) in enumerate(results, 1):
        text = entry.get("text", "[No text]")
        content_hash = entry.get("content_hash", "N/A")
        metadata = entry.get("metadata", {}) or {}
        source = metadata.get("source", "Unknown source")

        print(f"\n📌 Result #{i} (BM25 Score: {score:.4f})")
        print(f"   Source: {source}")
        print(f"   Content Hash: {content_hash}")
        print(f"\n   Chunk:")
        print(f"   {text[:300]}{'...' if len(text) > 300 else ''}")
        print()

    print("-" * 80)


def main():
    """Main REPL loop."""
    print("\n🔍 Medical Ingestion BM25 Search Demo")
    print("=" * 80)
    print("Enter questions to search through the BM25 sparse index.")
    print("Type 'quit' or 'exit' to stop.\n")

    index = BM25Index()
    try:
        index.load()
    except Exception as e:
        print(f"\n❌ Failed to load BM25 index: {e}")
        print("Run scripts/ingest_documents.py first to build the index.\n")
        sys.exit(1)

    while True:
        try:
            query = input("Question: ").strip()
        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            sys.exit(0)

        if not query:
            print("Please enter a question.\n")
            continue

        if query.lower() in ("quit", "exit"):
            print("\nGoodbye!\n")
            sys.exit(0)

        try:
            search_bm25(index, query)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
