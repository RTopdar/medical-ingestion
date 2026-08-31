---
type: Module
title: BM25 Sparse Index
description: Sparse lexical retrieval index over the deduped chunk corpus, companion to Qdrant's dense index; keyed by content_hash so it fuses with dense results with no id-mapping.
resource: retrieval/bm25.py
tags: [retrieval, bm25, sparse-search, hybrid-retrieval]
status: stable
---

# BM25 Sparse Index

`retrieval/bm25.py`. `BM25Index` wraps `bm25s.BM25`. Rebuilt from scratch on every ingestion run over the full deduped chunk corpus (`ChunkStore.get_all_chunks()`) — `bm25s` has no incremental-add API, so a fresh corpus means a fresh index every run.

## Components

- `BM25Index.__init__(index_dir=None)` — defaults to `settings.bm25_index_path` (env `BM25_INDEX_PATH`, default `./data/bm25_index`).
- `build(chunks: list[Chunk])` — dedupes input to one entry per unique `content_hash` (first occurrence wins), mirroring how `ChunkStore.sync_to_qdrant` dedupes before writing to Qdrant. Tokenizes text via `bm25s.tokenize(..., stopwords="en")` and indexes.
- `save()` / `load()` — persist/restore the index + corpus to/from `index_dir` via `bm25s`'s native save/load.
- `search(query, top_k=5) -> list[tuple[dict, float]]` — returns `(corpus_entry, score)` pairs, highest score first. Each corpus entry carries `content_hash`, `text`, `metadata`.

## Why content_hash keying

Both Qdrant (dense) and BM25 (sparse) are built from the same deduped hash set produced by `ChunkStore`. Keying both stores' results by `content_hash` lets [Hybrid Search Retrieval](/doc/feature/hybrid_search_retrieval.md) fuse them directly — no separate id-mapping layer needed.

## Callers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md)`::rebuild_bm25_index()` — rebuilds on every ingestion run, including the early-exit path when no new documents are found (BM25 has no incremental update).
- [Hybrid Search Retrieval](/doc/feature/hybrid_search_retrieval.md) — sparse half of RRF fusion.
- `scripts/bm25_search_demo.py` — standalone exploration script exercising this module in isolation (see [BM25 Search Demo](/doc/feature/bm25_search_demo.md)).

## Related

- [Chunk Store](/doc/feature/chunk_store.md) — source of the deduped chunk corpus this index is built from
- [Hybrid Search Retrieval](/doc/feature/hybrid_search_retrieval.md) — fuses this with Qdrant dense search
