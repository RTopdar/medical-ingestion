---
type: Module
title: Search Service + Main REPL
description: Production retrieval + generation orchestrator — embed query, RRF-fuse dense+sparse, cross-encoder rerank, stream grounded LLM answer. Wired into main.py as the interactive REPL.
resource: retrieval/search.py
tags: [retrieval, rag, orchestration, main]
status: stable
---

# Search Service + Main REPL

`retrieval/search.py::SearchService` is the production search path — orchestrates the full retrieval + generation stack. `main.py` (rewritten from a hello-world stub) is the interactive REPL built on it.

## Components

- `embed_query(text) -> list[float]` — module-level function, embeds via direct OpenRouter `/embeddings` POST (not the `openrouter` MCP server — see [Cross-Encoder Reranker](reranker.md)'s guard note, same applies here: runtime app traffic, not agent tool calls).
- `SearchService.__init__()` — constructs a `BM25Index` and loads it from disk (`settings.bm25_index_path`), a `HybridRetriever(QdrantVectorStore(), bm25_index)`, and a `Reranker()`. Fails loudly if the BM25 index hasn't been built yet (`scripts/ingest_documents.py` must run first).
- `search(query, top_k=5, fetch_k=20) -> list[dict]` — `embed_query()` → `HybridRetriever.search()` (RRF-fused, `fetch_k` candidates) → `Reranker.rerank()` (reordered to `top_k`).
- `answer(query, chunks)` — generator, streams a grounded LLM response via `ChatOpenRouter(model=settings.chat_model, streaming=True)`. Builds a prompt instructing the model to answer only from the provided chunks, numbered `[Chunk N]`.
- `main.py::main()` — REPL loop: constructs `SearchService()`, reads queries from stdin, calls `search()` then `display_results()` (prints relevance score, source, content hash, text preview), then streams `answer()` token-by-token to stdout. `quit`/`exit`/Ctrl-C to stop.

## Data flow

Query → `embed_query()` → [Hybrid Search Retrieval](hybrid_search_retrieval.md)`.search()` (RRF over Qdrant + BM25) → [Cross-Encoder Reranker](reranker.md)`.rerank()` → `answer()` streams grounded LLM response via LangChain `ChatOpenRouter`.

## Why this supersedes the planned `rag/` module

Earlier planning (see IMPLEMENTATION_PLAN.md Future Enhancements) described a dedicated `rag/` module with retriever + generator classes as a future step past `scripts/similarity_search_demo.py`'s dense-only demo. That landed as `retrieval/` instead — same intent (reusable, production-grade retrieval + generation), different name, and with hybrid+rerank built in from the start rather than added later. (inferred from code)

## Not the production path

`scripts/similarity_search_demo.py`, `scripts/bm25_search_demo.py`, and `scripts/hybrid_search_demo.py` are throwaway exploration scripts for testing pieces of the stack in isolation — none of them call `SearchService`; they re-implement fragments of it directly for demo purposes.

## Related

- [Hybrid Search Retrieval](hybrid_search_retrieval.md)
- [Cross-Encoder Reranker](reranker.md)
- [BM25 Sparse Index](bm25_index.md)
- [Qdrant Infrastructure](qdrant_infrastructure.md)
- [Similarity Search Demo](similarity_search_demo.md) — earlier dense-only demo, superseded as the production path by this module
