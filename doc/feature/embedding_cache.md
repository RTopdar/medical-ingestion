---
type: Module
title: Embedding Cache (removed)
description: Formerly the raw-sqlite3 content-addressable cache backing Embedder. File deleted; replaced by Postgres-backed ChunkStore.
resource: storage/embedding_cache.py
tags: [storage, embeddings, sqlite, deprecated]
status: deprecated
---

# Embedding Cache (removed)

`storage/embedding_cache.py` (and the sibling `storage/document_cache.py`, whole-doc dedup) have been **deleted**. Replaced by:

- [Chunk Store](/doc/feature/chunk_store.md) (`storage/chunk_store.py::ChunkStore`) — Postgres-backed, covers cache-hit lookup (`find_by_hash`), chunk-row persistence (`insert_chunks`), DLQ (`add_failed`/`get_failed`), and whole-document dedup (`document_seen`/`mark_document_seen`), replacing both old sqlite modules in one repository class.
- [Postgres Storage](/doc/feature/postgres_storage.md) (`storage/postgres.py`) — engine/`init_db()` setup, replacing raw `sqlite3.connect()`.
- [Data Models](/doc/feature/models.md) — `Chunk`, `FailedEmbedding`, `IngestedDocument` SQLModel table classes, replacing the hand-written sqlite schema.

**Why:** the old cache keyed embeddings only on `(model, text)`, discarding metadata — identical text across different patients/documents collapsed to one entry, losing provenance. See [Chunk Store](/doc/feature/chunk_store.md) for the full rationale.

Do not use this file as current documentation — kept only so old links resolve to an explanation rather than a 404. See [Chunk Store](/doc/feature/chunk_store.md) for the active implementation.
