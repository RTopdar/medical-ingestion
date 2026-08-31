---
type: Module
title: Hybrid Search Retrieval
description: Reciprocal rank fusion (RRF) over dense (Qdrant) and sparse (BM25) search — the fusion layer of the production retrieval stack.
resource: retrieval/hybrid.py
tags: [retrieval, rrf, hybrid-search, qdrant, bm25]
status: stable
---

# Hybrid Search Retrieval

`retrieval/hybrid.py`. `HybridRetriever.search()` fuses [Qdrant](/doc/feature/qdrant_infrastructure.md) dense search with [BM25 Sparse Index](/doc/feature/bm25_index.md) sparse search via reciprocal rank fusion (RRF).

## Components

- `HybridRetriever.__init__(qdrant_store, bm25_index, rrf_k=60)` — takes a `QdrantVectorStore` and a `BM25Index`; `rrf_k` is the RRF smoothing constant.
- `search(query, query_embedding, top_k=5, fetch_k=20) -> list[dict]` — runs `qdrant_store.search(query_vector=query_embedding, limit=fetch_k)` (dense) and `bm25_index.search(query, top_k=fetch_k)` (sparse) in parallel-by-call, fuses by rank: `score += 1 / (rrf_k + rank + 1)` per hit per source, summed across both sources when a `content_hash` appears in both. Returns the top `top_k` fused results as `{content_hash, score, text, metadata}` dicts.

## Why fuse by rank, not raw score

Cosine similarity (Qdrant) and BM25 score live on unrelated, uncalibrated scales — combining them directly would let whichever source happens to produce larger numbers dominate. Reciprocal rank fusion sidesteps calibration entirely by only using each hit's rank position within its own source's result list. (inferred from code)

## Why content_hash keying needs no id-mapping

Both Qdrant and BM25 are built from the same deduped `content_hash` set produced by `ChunkStore` (see [Chunk Store](/doc/feature/chunk_store.md)) — a hit from either source can be merged into the other's results by `content_hash` directly, no separate identity-resolution step needed.

## Callers

- [Search Service](/doc/feature/search_service.md)`::search()` — production path, output goes to [Cross-Encoder Reranker](/doc/feature/reranker.md).
- `scripts/hybrid_search_demo.py` — standalone exploration script exercising this module without reranking (see [Hybrid Search Demo](/doc/feature/hybrid_search_demo.md)).

## Related

- [BM25 Sparse Index](/doc/feature/bm25_index.md) — sparse half of fusion
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — dense half of fusion
- [Cross-Encoder Reranker](/doc/feature/reranker.md) — second-pass reordering of this module's output
- [Search Service](/doc/feature/search_service.md) — orchestrator that calls this module
