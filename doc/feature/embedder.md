---
type: Module
title: Embedder
description: Converts text into embedding vectors via OpenRouter's /embeddings endpoint, batched and cached to avoid re-paying for duplicate text.
resource: ingestion/embedder.py
tags: [ingestion, embeddings, openrouter]
status: stable
---

# Embedder

`ingestion/embedder.py`. Wraps OpenRouter's `POST /embeddings` endpoint behind an `Embedder` class. First component in the (previously "planned") Embeddings layer — see [Implementation Plan](/IMPLEMENTATION_PLAN.md).

## Components

- `Embedder.__init__(model=None, batch_size=None, cache=None)` — `model` defaults to `settings.embedding_model`, `batch_size` to `settings.embedding_batch_size`, `cache` to a new [Embedding Cache](/doc/feature/embedding_cache.md) at `settings.embedding_cache_db_path`. Reads `settings.openrouter_api_key`/`settings.openrouter_base_url` for auth and endpoint.
- `Embedder.embed(texts)` — the main entry point. For each input text, computes a cache key (`EmbeddingCache.make_key(model, text)`), looks up all keys via `cache.get_many()`, and only calls the OpenRouter API for cache misses, in batches of `batch_size`. New results are written back via `cache.set_many()` before returning. Returns one vector per input text, **in original input order** (not batch/cache order).
- `Embedder.embed_one(text)` — convenience wrapper, `embed([text])[0]`.
- `Embedder._embed_batch(batch)` — the actual HTTP call (`requests.Session.post`); re-sorts the response by the API's `index` field before returning, so batch order is never assumed from response order alone.
- `EmbedderError(RuntimeError)` — raised on non-2xx response, or if the response's embedding count doesn't match the request's text count (defensive check against silent partial responses).

## Data flow

[Chunker](/doc/feature/chunker.md) → `Document` (chunked) → `[doc.page_content for doc in chunks]` → `Embedder.embed()` → cache lookup (hit → skip API; miss → batched OpenRouter call → [Embedding Cache](/doc/feature/embedding_cache.md) write) → `list[list[float]]`, same order as input.

## Why the cache

Cost-saving measure for billion-scale ingestion. Medical corpora have significant repeated text (boilerplate consent language, repeated section headers, and any re-ingestion run re-processing the same source documents) — the cache makes identical `(model, text)` pairs a guaranteed cache hit rather than a re-billed API call.

## Callers

None yet — not wired into `scripts/ingest_documents.py`. This is a real gap: the ingestion pipeline currently stops at chunking and does not call `Embedder`.

## Related

- [Embedding Cache](/doc/feature/embedding_cache.md) — the sqlite-backed cache this module depends on
- [Chunker](/doc/feature/chunker.md) — upstream, produces the `Document` chunks this module embeds
