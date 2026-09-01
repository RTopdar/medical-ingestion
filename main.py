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
        citation = result.get("citation", {})
        source = citation.get("source") or metadata.get("source", "Unknown source")
        doc_id = citation.get("document_id", "N/A")

        print(f"\nResult #{i} (relevance: {result['relevance_score']:.4f})")
        print(f"   Citation: [{i}] {source} (doc_id: {doc_id})")
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
            citations = [r.get("citation", {}) for r in results]
            print("\nLLM Answer:\n")
            answer_text = ""
            for token in service.answer(query, chunks, citations):
                answer_text += token
                print(token, end="", flush=True)
            print("\n")

            cited_indices = service.extract_citations_from_answer(answer_text, len(results))
            if cited_indices:
                print("-" * 80)
                print(f"Citations found in answer: {cited_indices}")
                for idx in dict.fromkeys(cited_indices):
                    if idx <= len(results):
                        result = results[idx - 1]
                        citation = result.get("citation", {})
                        print(f"   [{idx}] {citation.get('source', 'Unknown')} (doc_id: {citation.get('document_id', 'N/A')})")
                print("-" * 80 + "\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
