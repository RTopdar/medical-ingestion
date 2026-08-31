"""Interactive medical document search — hybrid retrieval (dense + BM25, RRF-fused),
cross-encoder reranked, with a grounded LLM answer streamed per query.
"""

import sys

from retrieval.search import SearchService


def display_results(results: list[dict]) -> None:
    print(f"\nFound {len(results)} result(s):\n")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        text = result.get("text") or "[No text]"
        metadata = result.get("metadata", {}) or {}
        source = metadata.get("source", "Unknown source")

        print(f"\nResult #{i} (relevance: {result['relevance_score']:.4f})")
        print(f"   Source: {source}")
        print(f"   Content Hash: {result.get('content_hash', 'N/A')}")
        print(f"\n   Chunk:")
        print(f"   {text[:300]}{'...' if len(text) > 300 else ''}")
    print("\n" + "-" * 80)


def main():
    print("\nMedical Ingestion Search")
    print("=" * 80)
    print("Hybrid retrieval (dense + BM25) + cross-encoder reranking, grounded LLM answers.")
    print("Type 'quit' or 'exit' to stop.\n")

    try:
        service = SearchService()
    except Exception as e:
        print(f"\nFailed to start search service: {e}")
        print("Run scripts/ingest_documents.py first to build the BM25 index.\n")
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
            results = service.search(query)
            if not results:
                print("\nNo results found.\n")
                continue

            display_results(results)

            chunks = [r.get("text") or "" for r in results]
            print("\nLLM Answer:\n")
            for token in service.answer(query, chunks):
                print(token, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
