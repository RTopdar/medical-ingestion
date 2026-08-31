---
type: Module
title: Hybrid Search Demo
description: Standalone exploration script for retrieval/hybrid.py::HybridRetriever — dense+sparse RRF fusion plus a streamed LLM answer, but no reranking step.
resource: scripts/hybrid_search_demo.py
tags: [retrieval, hybrid-search, rrf, demo, reference-script]
status: stable
---

# Hybrid Search Demo

`scripts/hybrid_search_demo.py`. Interactive REPL: embeds the query directly via OpenRouter (duplicates `retrieval/search.py::embed_query` rather than importing it), runs [Hybrid Search Retrieval](hybrid_search_retrieval.md)`.search()` (RRF fusion of Qdrant + BM25), displays top-5 fused results with RRF score/source/content hash/preview, then streams a grounded LLM answer via `ChatOpenRouter` — same prompt template as [Search Service](search_service.md)`.answer()`, reimplemented locally rather than imported.

## Status

Throwaway exploration script — exercises fusion without the reranking step, so results are ordered by RRF score alone, not by the cross-encoder. Not called by [Search Service](search_service.md) or `main.py`. Useful for isolating whether a retrieval quality issue is fusion-specific vs. reranking-specific.

## Usage

```bash
python scripts/ingest_documents.py   # build the BM25 index + Qdrant collection first
python scripts/hybrid_search_demo.py
```

## Related

- [Hybrid Search Retrieval](hybrid_search_retrieval.md) — the module this exercises
- [BM25 Search Demo](bm25_search_demo.md) — same pattern, one layer down (sparse only)
- [Search Service](search_service.md) — the actual production path (adds reranking)
