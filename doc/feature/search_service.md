---
type: Module
title: Search Service + Main REPL
description: Production retrieval + generation orchestrator — embed query, RRF-fuse dense+sparse, cross-encoder rerank, stream grounded LLM answer with inline citations. Wired into main.py as the interactive REPL.
resource: retrieval/search.py
tags: [retrieval, rag, orchestration, main, citations]
status: stable
---

# Search Service + Main REPL

`retrieval/search.py::SearchService` is the production search path — orchestrates the full retrieval + generation stack. `main.py` (rewritten from a hello-world stub) is the interactive REPL built on it.

## Components

- `embed_query(text) -> list[float]` — module-level function, embeds via direct OpenRouter `/embeddings` POST (not the `openrouter` MCP server — see [Cross-Encoder Reranker](reranker.md)'s guard note, same applies here: runtime app traffic, not agent tool calls).
- `SearchService.__init__()` — constructs a `BM25Index` and loads it from disk (`settings.bm25_index_path`), a `HybridRetriever(QdrantVectorStore(), bm25_index)`, and a `Reranker()`. Fails loudly if the BM25 index hasn't been built yet (`scripts/ingest_documents.py` must run first).
- `search(query, top_k=5, fetch_k=20) -> list[dict]` — `embed_query()` → `HybridRetriever.search()` (RRF-fused, `fetch_k` candidates) → `Reranker.rerank()` (reordered to `top_k`) → `_enrich_with_citations()` (adds `citation_index`/`citation` to each result) → cached on `self.last_results`.
- `answer(query, chunks, citations=None)` — generator, streams a grounded LLM response via `ChatOpenRouter(model=settings.chat_model, streaming=True)`. Chunks are numbered `[N]` in the prompt (renumbered from `[Chunk N]`) and, when `citations` is passed, each chunk gets an appended `[Source: ...]` marker. Prompt instructs the model to cite inline using `[1]`, `[2]`, etc. `citations` param is optional/backward-compatible — omitting it just drops the source markers, chunk numbering still happens.
- `main.py::display_results()` — prints relevance score plus a `Citation: [i] {source} (doc_id: {doc_id})` line per result, falling back to raw `metadata.source` if `citation` is absent (defensive, pre-enrichment results).
- `main.py::main()` — REPL loop: constructs `SearchService()`, reads queries from stdin, calls `search()` then `display_results()`, builds a `citations` list from each result's `citation` dict, streams `answer(query, chunks, citations)` token-by-token while accumulating the full answer text, then calls `SearchService.extract_citations_from_answer()` on the accumulated text and prints a dedup'd "Citations found in answer" block mapping each cited `[N]` back to its source/doc_id. `quit`/`exit`/Ctrl-C to stop.

## Citation mapping (6 layers)

Added commit `894b995`. Threads citation identity from Qdrant payload through to the CLI, across `retrieval/search.py` + `main.py`:

1. **Metadata extraction** — `_enrich_with_citations()` pulls `source`/`document_id` out of each result's `metadata` dict (defaults `"Unknown"`/`"N/A"` on missing/`None` values).
2. **Chunk-level citation markers** — `answer()` appends `[Source: ...]` to each chunk's text in the LLM context block.
3. **Result struct enrichment** — every `search()` result gains `citation_index` (1-indexed rank) and a `citation` dict (`source`, `document_id`, `rank`).
4. **LLM prompt injection** — prompt appends an instruction line telling the model to cite inline as `[1]`, `[2]`, etc., matching the chunk numbering it's shown.
5. **Citation parsing** — `SearchService.extract_citations_from_answer(answer_text, num_results)` (static method), regex `\[(\d+)\]` over the streamed answer, filtered to the valid `1..num_results` range so out-of-range/hallucinated indices are dropped.
6. **CLI citation display** — `main.py::main()` renders a dedup'd, ordered "Citations found in answer" block after the streamed answer, resolving each cited index back to its `citation` dict.

Citation identity is rank-based (`citation_index`, 1-indexed position in the reranked list), not a stable per-chunk ID — re-running the same query with a different corpus state can shift which source maps to `[N]`. This is acceptable for a single-turn REPL exchange but would need a stable key (e.g. `content_hash`) if citations ever needed to survive across turns.

## Data flow

Query → `embed_query()` → [Hybrid Search Retrieval](hybrid_search_retrieval.md)`.search()` (RRF over Qdrant + BM25) → [Cross-Encoder Reranker](reranker.md)`.rerank()` → `_enrich_with_citations()` (citation dict per result) → `answer()` streams grounded LLM response with inline `[N]` citations via LangChain `ChatOpenRouter` → `extract_citations_from_answer()` parses cited indices → `main.py` renders sourced citation block.

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
- [Hybrid Search Retrieval](hybrid_search_retrieval.md) — upstream RRF fusion, source of results this module enriches with citations
