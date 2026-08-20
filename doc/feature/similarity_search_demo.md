---
type: Script
title: Similarity Search Demo
description: Interactive REPL for vector similarity search and grounded LLM response streaming via Qdrant and LangChain OpenRouter.
resource: scripts/similarity_search_demo.py
tags: [retrieval, rag, vector-search, llm-streaming, interactive]
status: stable
---

# Similarity Search Demo

`scripts/similarity_search_demo.py`. Interactive command-line REPL that bridges ingestion, retrieval, and RAG:

1. **Query embedding** via OpenRouter `/embeddings` endpoint
2. **Vector search** against Qdrant (top-3 chunks by similarity)
3. **LLM response streaming** via LangChain OpenRouter ChatOpenRouter, grounded in search results

## Purpose

Demonstration and testing tool for end-to-end RAG pipelines: verify that ingested documents are retrievable, that Qdrant similarity scoring works, and that LLM synthesis of search results streams correctly.

## Usage

```bash
# Start Qdrant and Postgres first (if not already running)
bash scripts/start_qdrant.sh
bash scripts/start_postgres.sh

# Ingest documents (populates Qdrant with vectors)
python scripts/ingest_documents.py

# Run the interactive demo
python scripts/similarity_search_demo.py
```

```
🔍 Medical Ingestion Similarity Search Demo
================================================================================
Enter questions to search through ingested chunks.
Type 'quit' or 'exit' to stop.

Question: What are the symptoms of type 2 diabetes?
```

At each prompt, the script:
1. Embeds the question via OpenRouter (blocking)
2. Searches Qdrant for 3 most-similar chunks
3. Displays each chunk with metadata (source, similarity score, content preview)
4. Streams an LLM response grounded in those chunks via LangChain OpenRouter

## Flow

### Step 1: Embed Query

`embed_query(text: str) -> list[float]`:
- Calls `settings.openrouter_base_url + "/embeddings"`
- Uses `settings.embedding_model` (default: `openai/text-embedding-3-small`)
- Returns raw embedding vector from first element of API response

### Step 2: Search Qdrant

`search_similarity(query: str, top_k: int = 3)`:
- Creates `QdrantVectorStore()` instance (connected to local Qdrant at `settings.qdrant_url`)
- Calls `.search(query_vector=embedding, limit=top_k)` → `list[qdrant_client.models.ScoredPoint]`
- Each result has `.payload` (metadata dict) and `.score` (cosine similarity, 0–1)

### Step 3: Display Results

For each result:
- **Result #**: enumeration
- **Similarity Score**: decimal 0.0–1.0 from Qdrant
- **Source**: metadata field `source` (file path or data source name)
- **Content Hash**: metadata field `content_hash` (for deduplication audit)
- **Chunk preview**: first 300 characters of `text` or `content` field

### Step 4: Stream LLM Response

`stream_llm_response(query: str, context_chunks: list[str])`:
- Builds a system prompt: "You are a medical expert. Answer based ONLY on these documents..."
- Concatenates all search results as numbered chunks: `[Chunk 1] ... [Chunk 2] ...`
- Calls `ChatOpenRouter(model=settings.chat_model, streaming=True)`
- Streams response via `.stream([HumanMessage(content=prompt)])`
- Prints to stdout in real time as chunks arrive

## Configuration

All settings come from `settings.py`:

- `openrouter_api_key` — env `OPENROUTER_API_KEY` (required; bearer token for OpenRouter)
- `openrouter_base_url` — env `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)
- `embedding_model` — env `EMBEDDING_MODEL` (default: `openai/text-embedding-3-small`)
- `chat_model` — env `CHAT_MODEL` (default: `gpt-4-turbo`, or any OpenRouter model slug)
- `qdrant_url` — env `QDRANT_URL` (default: `http://localhost:6333`)

## Error Handling

- **Embedding API failure**: Prints `❌ Embedding failed (status_code): response_text`, exits current search
- **Qdrant connection error**: Caught by `QdrantVectorStore()` initialization
- **Malformed Qdrant results**: Logs `⚠️ Skipping malformed result` if payload is missing/empty, continues to next
- **LLM streaming error**: Prints `❌ Streaming error: exception`, continues to next prompt
- **Keyboard interrupt** (Ctrl+C): Prints `Goodbye!`, exits gracefully

## Dependencies

- `langchain-openrouter` — ChatOpenRouter streaming via LangChain
- `langchain-core` — HumanMessage type
- `requests` — direct calls to OpenRouter `/embeddings` (not via LangChain, for simplicity)
- `vector_db.qdrant::QdrantVectorStore` — local Qdrant client wrapper
- `settings` — config (OpenRouter keys, model names, Qdrant URL)

## Related

- [Embedder](/doc/feature/embedder.md) — how embeddings are generated and cached during ingestion
- [Chunk Store](/doc/feature/chunk_store.md) — Postgres dedup and metadata storage
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — Qdrant Docker setup and startup
- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — populates Qdrant with vectors, prerequisite for demo to have data
