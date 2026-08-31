---
type: Module
title: BM25 Search Demo
description: Standalone exploration script for exercising retrieval/bm25.py::BM25Index in isolation, sparse-only, no dense fusion or reranking.
resource: scripts/bm25_search_demo.py
tags: [retrieval, bm25, demo, reference-script]
status: stable
---

# BM25 Search Demo

`scripts/bm25_search_demo.py`. Interactive REPL that loads the persisted [BM25 Sparse Index](bm25_index.md) and searches it directly — no Qdrant, no fusion, no reranking, no LLM answer. Displays top-5 results with BM25 score, source, content hash, and a text preview.

## Status

Throwaway exploration script, not called by [Search Service](search_service.md) or `main.py` — the production path fuses BM25 with dense search and reranks (see [Hybrid Search Retrieval](hybrid_search_retrieval.md)). Useful for isolating whether a retrieval quality issue is BM25-specific.

## Usage

```bash
python scripts/ingest_documents.py   # build the BM25 index first
python scripts/bm25_search_demo.py
```

## Related

- [BM25 Sparse Index](bm25_index.md) — the module this exercises
- [Hybrid Search Demo](hybrid_search_demo.md) — same pattern, one layer up (adds dense fusion)
- [Search Service](search_service.md) — the actual production path
