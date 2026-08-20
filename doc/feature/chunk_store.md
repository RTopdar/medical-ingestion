---
type: Module
title: Chunk Store
description: Postgres-backed repository for chunk provenance, embedding cache-check, whole-document dedup, and the failed-embedding DLQ. Replaces the old sqlite EmbeddingCache + DocumentCache.
resource: storage/chunk_store.py
tags: [storage, postgres, sqlmodel, embeddings, dedup]
status: stable
---

# Chunk Store

`storage/chunk_store.py`. `ChunkStore` class, built on SQLModel `Session`/`select()` against Postgres (`storage/postgres.py`). Replaces two sqlite modules that no longer exist: `storage/embedding_cache.py` (`EmbeddingCache`) and `storage/document_cache.py` (`DocumentCache`) — see [Postgres Storage](/doc/feature/postgres_storage.md) for the engine/table setup and [Data Models](/doc/feature/models.md) for the `Chunk`/`FailedEmbedding`/`IngestedDocument` row classes it operates on.

## Why this replaced EmbeddingCache/DocumentCache

The old dedup keyed embeddings only on `(model, text)`, discarding metadata — identical clinical text appearing in Patient A's file, Patient B's file, and a clinical-trial document all collapsed to a single Qdrant point, losing patient/document lineage. New design still dedupes the expensive OpenRouter API call (via `find_by_hash`), but persists one Postgres row per `(content, occurrence)` so provenance is queryable, e.g. "all Type 2 Diabetes mentions for Patient A" via `SELECT ... WHERE metadata->>'patient_mrn' = ...`. (inferred from code / migration description)

## Components

- `ChunkStore.__init__(engine)` — takes a SQLAlchemy `Engine` (normally `storage.postgres.engine`).
- `find_by_hash(content_hash) -> list[float] | None` — the sole embedding cache-check source. `SELECT` on `Chunk.content_hash`, returns the first match's `embedding` or `None` on miss. Qdrant is **not** queried during embedding anymore — only Postgres.
- `insert_chunks(rows: list[Chunk])` — bulk insert, always one row per chunk occurrence, even on a cache hit (needed for provenance). Caller (ingest script) pre-filters duplicates within the batch before calling (via `(content_hash, metadata)` dedup loop in `embed_and_store()`), so the rows passed here are guaranteed to be unique within that single run. Batches (~100 rows) before calling.
- `sync_to_qdrant(rows: list[Chunk], qdrant_store: VectorStore) -> int` — upserts to Qdrant only for `content_hash`es not already present there; dedupes within the batch itself too, so exactly one Qdrant point is written per unique hash. Returns count of new points written. Calls `qdrant_store.find_by_hash()` then `qdrant_store.upsert_one()` per new hash (see [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md)).
- `add_failed(text, error, model, content_hash=None)` / `get_failed(limit=100)` — DLQ read/write against `FailedEmbedding`, same shape as the old sqlite DLQ table.
- `document_seen(content_hash) -> bool` / `mark_document_seen(content_hash, source)` — whole-document dedup gate, replaces `DocumentCache`. Backed by `IngestedDocument` (content_hash primary key).

## Data flow

[Chunker](/doc/feature/chunker.md) → `Document` (chunked) → [Embedder](/doc/feature/embedder.md)`.embed()` calls `find_by_hash()` per unique hash for cache-hit checks (no writes) → `scripts/ingest_documents.py::embed_and_store` builds one `Chunk` row per chunk occurrence → `insert_chunks()` (Postgres, always) → `sync_to_qdrant()` (Qdrant, only new hashes). Whole-document dedup happens earlier, in `filter_seen_documents()` via `document_seen()`/`mark_document_seen()`, before chunking.

## Callers

- [Embedder](/doc/feature/embedder.md) — `find_by_hash()` only (read-only cache check; no longer writes to any cache itself).
- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — `document_seen`/`mark_document_seen` (dedup gate), `insert_chunks`, `sync_to_qdrant`, `add_failed`/`get_failed` (via `Embedder`).

## Related

- [Postgres Storage](/doc/feature/postgres_storage.md) — engine/`init_db()` this repository runs against
- [Data Models](/doc/feature/models.md) — `Chunk`, `FailedEmbedding`, `IngestedDocument` row classes
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — the similarity-search backend `sync_to_qdrant` writes to
