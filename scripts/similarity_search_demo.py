#!/usr/bin/env python3
"""Interactive similarity search demo — ask questions and get top-3 chunks with sources."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from settings import settings
from vector_db.qdrant import QdrantVectorStore
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage


def stream_llm_response(query: str, context_chunks: list[str]) -> None:
    """Stream LLM response via LangChain OpenRouter, grounding in search results."""
    # Build context from chunks
    context_str = "\n\n".join([f"[Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])

    prompt = f"""You are a medical expert. Answer the following question based ONLY on the provided medical documents.

Question: {query}

Context from medical documents:
{context_str}

Provide a clear, concise answer based on the documents. If the answer is not in the documents, say so."""

    try:
        print("\n🤖 LLM Response:\n")
        llm = ChatOpenRouter(
            model=settings.chat_model,
            temperature=0.7,
            streaming=True,
        )

        for chunk in llm.stream([HumanMessage(content=prompt)]):
            if chunk.content:
                print(chunk.content, end="", flush=True)

        print("\n")
    except Exception as e:
        print(f"❌ Streaming error: {e}\n")


def embed_query(text: str) -> list[float]:
    """Embed text via OpenRouter API."""
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
    )
    resp = session.post(
        f"{settings.openrouter_base_url}/embeddings",
        json={"model": settings.embedding_model, "input": [text]},
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"Embedding failed ({resp.status_code}): {resp.text}")
    data = resp.json().get("data", [])
    if not data:
        raise RuntimeError("No embedding returned")
    return data[0]["embedding"]


def search_similarity(query: str, top_k: int = 3) -> None:
    """Search for similar chunks, display results, and stream LLM response."""
    qdrant_store = QdrantVectorStore()

    # Embed the query
    query_embedding = embed_query(query)

    # Search in Qdrant
    results = qdrant_store.search(query_vector=query_embedding, limit=top_k)

    if not results:
        print("\n❌ No results found.\n")
        return

    print(f"\n✅ Found {len(results)} result(s):\n")
    print("-" * 80)

    chunks = []
    for i, result in enumerate(results, 1):
        if not result or not hasattr(result, "payload") or not result.payload:
            print(f"⚠️  Skipping malformed result: {result}")
            continue
        payload = result.payload
        text = payload.get("text") or payload.get("content") or "[No text]"
        source = payload.get("source", "Unknown source")
        score = result.score

        print(f"\n📌 Result #{i} (Similarity Score: {score:.4f})")
        print(f"   Source: {source}")
        print(f"   Content Hash: {payload.get('content_hash', 'N/A')}")
        print(f"\n   Chunk:")
        print(f"   {text[:300]}{'...' if len(text) > 300 else ''}")
        print()

        chunks.append(text)

    print("-" * 80)

    # Stream LLM response
    if chunks:
        stream_llm_response(query, chunks)


def main():
    """Main REPL loop."""
    print("\n🔍 Medical Ingestion Similarity Search Demo")
    print("=" * 80)
    print("Enter questions to search through ingested chunks.")
    print("Type 'quit' or 'exit' to stop.\n")

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
            search_similarity(query)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
