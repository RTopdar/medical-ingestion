---
type: Module
title: Embedder
description: Converts text into embedding vectors via OpenRouter's /embeddings endpoint, batched and cache-checked against Postgres to avoid re-paying for duplicate text.
resource: ingestion/embedder.py
tags: [ingestion, embeddings, openrouter, postgres]
status: stable
---

# Embedder

`ingestion/embedder.py`. Wraps OpenRouter's `POST /embeddings` endpoint behind an `Embedder` class. Now wired into `scripts/ingest_documents.py` (full pipeline: load → chunk → embed → Postgres → Qdrant).

**Migration note (Postgres):** `Embedder` no longer owns any cache writes. It used to write cache entries itself via `EmbeddingCache.set_many()`; now it only *reads* via [Chunk Store](/doc/feature/chunk_store.md)`.find_by_hash()` for cache-hit checks. Persisting the `Chunk` rows (one per occurrence) is the ingest script's responsibility — see [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Components

- `Embedder.__init__(model=None, batch_size=None, chunk_store=None)` — `model` defaults to `settings.embedding_model`, `batch_size` to `settings.embedding_batch_size`, `chunk_store` defaults to `ChunkStore(storage.postgres.engine)` (see [Chunk Store](/doc/feature/chunk_store.md)). Reads `settings.openrouter_api_key`/`settings.openrouter_base_url` for auth and endpoint.
- `Embedder.embed(texts)` — the main entry point. For each input text, computes a content hash (`Chunk.make_content_hash(model, text)` — same sha256(model:normalized_text) logic the old `EmbeddingCache.make_key` used), looks up each unique hash via `chunk_store.find_by_hash()`, and only calls the OpenRouter API for cache misses, in batches of `batch_size`. **Writes no cache entries** — read-only. Returns one vector per input text, **in original input order** (not batch/cache order). On batch failure, logs the failed texts and error to the DLQ via `chunk_store.add_failed()`, then re-raises the error.
- `Embedder.embed_one(text)` — convenience wrapper, `embed([text])[0]`.
- `Embedder.embed_with_hashes(texts)` — embeds and also returns each text's content hash, so callers (the ingest script) can build `Chunk` rows without recomputing keys.
- `Embedder._embed_batch(batch)` — the actual HTTP call (`requests.Session.post`). **Decorated with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)`** (tenacity) — up to 3 attempts, exponential backoff 2-10s. Only raises `EmbedderError` if all attempts fail. Re-sorts the response by the API's `index` field before returning.
- `EmbedderError(RuntimeError)` — raised on non-2xx response, or if the response's embedding count doesn't match the request's text count. If raised from `_embed_batch()` after retries are exhausted, `embed()` catches it, logs the batch to the DLQ, and re-raises.

## Data flow

[Chunker](/doc/feature/chunker.md) → `Document` (chunked) → `[doc.page_content for doc in chunks]` → `Embedder.embed_with_hashes()` → cache lookup via [Chunk Store](/doc/feature/chunk_store.md)`.find_by_hash()` (hit → skip API; miss → retry-wrapped `_embed_batch()`) → `list[list[float]]` + hashes, same order as input → caller (`scripts/ingest_documents.py::embed_and_store`) builds `Chunk` rows and persists via `chunk_store.insert_chunks()` + `chunk_store.sync_to_qdrant()`; failure: DLQ write via `chunk_store.add_failed()` → EmbedderError raised.

## Why the cache-check

Cost-saving measure for billion-scale ingestion. Medical corpora have significant repeated text (boilerplate consent language, repeated section headers, and any re-ingestion run re-processing the same source documents) — the cache-check makes identical `(model, text)` pairs a guaranteed skip rather than a re-billed API call, while still persisting one Postgres row per real occurrence for provenance (see [Chunk Store](/doc/feature/chunk_store.md)).

## Retry Strategy

`_embed_batch()` is decorated with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)` (tenacity) to handle transient API failures:

- **3 retries** — up to 3 attempts total (1 initial + 2 retries)
- **Exponential backoff** — wait 2-10 seconds between retries (backoff doubles each attempt, capped at 10s)
- **Reraise on exhaustion** — if all 3 attempts fail, the exception propagates to `embed()`, which logs the batch to the DLQ via `chunk_store.add_failed()` and re-raises

**Rationale:** Transient failures (timeouts, rate-limits, network hiccups) are common in high-throughput API ingestion. Exponential backoff gives the provider time to recover without thundering-herd retries. Bounded retries prevent hanging on persistent errors. DLQ persistence ensures failed texts are never silently lost — failed embeddings can be inspected and manually retried later via `ChunkStore.get_failed()`.

## Callers

- `scripts/ingest_documents.py::embed_and_store` — see [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md). Full pipeline wiring, no longer a gap.

## Related

- [Chunk Store](/doc/feature/chunk_store.md) — Postgres-backed cache-check, persistence, DLQ, and dedup this module depends on (replaces the deleted [Embedding Cache](/doc/feature/embedding_cache.md))
- [Chunker](/doc/feature/chunker.md) — upstream, produces the `Document` chunks this module embeds
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — downstream similarity-search store, synced from `Chunk` rows by `ChunkStore.sync_to_qdrant`
