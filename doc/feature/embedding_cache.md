---
type: Module
title: Embedding Cache
description: Raw-sqlite3 content-addressable key-value store mapping (model, text) -> embedding vector, so Embedder never re-pays for the same text twice.
resource: storage/embedding_cache.py
tags: [storage, embeddings, sqlite]
status: stable
---

# Embedding Cache

`storage/embedding_cache.py`. `EmbeddingCache` class — single key-value table, no relations to any other model, so it uses raw `sqlite3` rather than SQLModel (contrast with [SQL Loader / storage layer](/doc/feature/sql_loader.md), which uses SQLModel because it has a real relational schema with a foreign key join). Consistent with the project's ORM decision: SQLModel only where there are real relationships to model, plain `sqlite3` for simple key-value persistence.

## Schema

Two tables:

1. **`embedding_cache(hash PRIMARY KEY, model, embedding)`** — main cache. `embedding` is stored as a JSON-serialized text column (`json.dumps`/`json.loads`), not a native array type, since sqlite has no vector column type.
2. **`failed_embeddings(id, hash, text, error, model, attempt_count, created_at)`** — Dead-Letter Queue (DLQ). Records failed embedding attempts (text, error message, model, timestamp) for later inspection and optional manual retry. Populated by `Embedder.embed()` when a batch fails after all retries are exhausted.

## Components

- `EmbeddingCache.__init__(db_path)` — opens/creates the sqlite file (creating parent dirs if needed) and both tables if they don't exist. **Enables WAL mode** (`PRAGMA journal_mode=WAL`) and **autocommit** (`isolation_level=None`) for thread-safe concurrent reads/writes without lock contention.
- `EmbeddingCache.make_key(model, text)` — `staticmethod`. Deterministic key: `sha256(f"{model}:{normalized_text}")`, where normalization collapses internal whitespace (`\s+ -> " "`) but only applies to the key, not to the text sent to the embedding API. Content-addressable — same `(model, text)` pair always produces the same key, so identical text (even with different spacing) always hits the cache regardless of when/how it was first embedded. Keying includes `model` so switching embedding models doesn't return stale vectors from a different model.
- `EmbeddingCache.get_many(keys)` — batch lookup, returns `{key: vector}` for hits only; missing keys are simply absent from the result dict (no exception).
- `EmbeddingCache.set_many(model, items)` — batch upsert (`INSERT OR REPLACE`) of `{key: vector}` pairs for a given model.
- `EmbeddingCache.add_failed(text, error, model, text_hash=None)` — records a failed embedding attempt to the `failed_embeddings` DLQ table. Called by `Embedder.embed()` when a batch fails after all retries. Stores the text, error message, model, and optional cache hash for later inspection.
- `EmbeddingCache.get_failed(limit=100)` — retrieves recent failed embeddings from the DLQ, ordered by creation timestamp (newest first). Returns a list of dicts with keys: `id`, `hash`, `text`, `error`, `model`, `attempt_count`, `created_at`. Useful for operational inspection, debugging, and deciding on manual retry strategies.
- `EmbeddingCache.close()` — closes the sqlite connection.

## Concurrency

WAL mode + autocommit enable thread-safe concurrent access:

- **WAL mode** (`PRAGMA journal_mode=WAL`) — Write-Ahead Logging allows multiple readers and writers to access the database simultaneously without blocking. Readers see a snapshot of the database at their query start time; writers create new snapshots without blocking readers.
- **Autocommit** (`isolation_level=None`) — each SQL statement commits immediately, reducing transaction lock hold time.
- **Per-thread connections** — each thread creates its own `EmbeddingCache` instance (calls `sqlite3.connect()` separately), all sharing the same `db_path` file. SQLite's WAL file-locking handles coordination between threads.

**Rationale:** Bulk ingestion pipelines may parallelize embedding across multiple threads. Without WAL, database access would serialize, becoming a bottleneck. WAL + per-thread connections let all threads read/write concurrently, improving throughput.

**Unbounded growth warning:** The cache and DLQ tables grow without bound in production. Future enhancements should add periodic `VACUUM` + size-cap logic or migrate to a vector DB that owns cache eviction (TTL, LRU). The DLQ may need its own lifecycle management (archive old failures, re-attempt old entries, or periodically truncate).

## Data flow

[Embedder](/doc/feature/embedder.md) computes keys via `make_key()` → `get_many()` for cache hits → API call only for misses (wrapped in retry logic) → success: `set_many()` persists new vectors → subsequent `embed()` calls (including future ingestion runs) hit cache instead of calling OpenRouter again; failure: `add_failed()` logs to DLQ → exception propagates.

## Settings

`settings.embedding_cache_db_path` (env `EMBEDDING_CACHE_DB_PATH`, default `./data/embedding_cache.db`).

## Exports

Re-exported from `storage/__init__.py` alongside `SQLLoaderService`: `from storage import EmbeddingCache`.

## Callers

- [Embedder](/doc/feature/embedder.md) — sole caller, via `ingestion/embedder.py`

## Related

- [SQL Loader (Storage Layer)](/doc/feature/sql_loader.md) — the other `storage/` module; uses SQLModel instead of raw sqlite3 because it has real relations (FK join), unlike this single-table cache
