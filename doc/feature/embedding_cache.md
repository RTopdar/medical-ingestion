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

Single table `embedding_cache(hash PRIMARY KEY, model, embedding)` — `embedding` is stored as a JSON-serialized text column (`json.dumps`/`json.loads`), not a native array type, since sqlite has no vector column type.

## Components

- `EmbeddingCache.__init__(db_path)` — opens/creates the sqlite file (creating parent dirs if needed) and the table if it doesn't exist.
- `EmbeddingCache.make_key(model, text)` — `staticmethod`. Deterministic key: `sha256(f"{model}:{text.strip()}")`. Content-addressable — same `(model, text)` pair always produces the same key, so identical text always hits the cache regardless of when/how it was first embedded. Keying includes `model` so switching embedding models doesn't return stale vectors from a different model.
- `EmbeddingCache.get_many(keys)` — batch lookup, returns `{key: vector}` for hits only; missing keys are simply absent from the result dict (no exception).
- `EmbeddingCache.set_many(model, items)` — batch upsert (`INSERT OR REPLACE`) of `{key: vector}` pairs for a given model.
- `EmbeddingCache.close()` — closes the sqlite connection.

## Data flow

[Embedder](/doc/feature/embedder.md) computes keys via `make_key()` → `get_many()` for cache hits → API call only for misses → `set_many()` persists new vectors → subsequent `embed()` calls (including future ingestion runs) hit cache instead of calling OpenRouter again.

## Settings

`settings.embedding_cache_db_path` (env `EMBEDDING_CACHE_DB_PATH`, default `./data/embedding_cache.db`).

## Exports

Re-exported from `storage/__init__.py` alongside `SQLLoaderService`: `from storage import EmbeddingCache`.

## Callers

- [Embedder](/doc/feature/embedder.md) — sole caller, via `ingestion/embedder.py`

## Related

- [SQL Loader (Storage Layer)](/doc/feature/sql_loader.md) — the other `storage/` module; uses SQLModel instead of raw sqlite3 because it has real relations (FK join), unlike this single-table cache
