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
- `Embedder.embed(texts)` — the main entry point. For each input text, computes a cache key (`EmbeddingCache.make_key(model, text)`), looks up all keys via `cache.get_many()`, and only calls the OpenRouter API for cache misses, in batches of `batch_size`. New results are written back via `cache.set_many()` before returning. Returns one vector per input text, **in original input order** (not batch/cache order). On batch failure, logs the failed texts and error to the [Embedding Cache](/doc/feature/embedding_cache.md)'s `failed_embeddings` DLQ table via `cache.add_failed()`, then re-raises the error (does not auto-retry at this level — retries happen at the HTTP level, see below).
- `Embedder.embed_one(text)` — convenience wrapper, `embed([text])[0]`.
- `Embedder._embed_batch(batch)` — the actual HTTP call (`requests.Session.post`). **Decorated with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)`** (using tenacity library) — retries up to 3 times on failure with exponential backoff starting at 2 seconds, capping at 10 seconds. Only raises `EmbedderError` if all 3 attempts fail. Re-sorts the response by the API's `index` field before returning, so batch order is never assumed from response order alone.
- `EmbedderError(RuntimeError)` — raised on non-2xx response, or if the response's embedding count doesn't match the request's text count (defensive check against silent partial responses). If raised from `_embed_batch()` after all retries are exhausted, `embed()` catches it, logs the batch to the DLQ, and re-raises.

## Data flow

[Chunker](/doc/feature/chunker.md) → `Document` (chunked) → `[doc.page_content for doc in chunks]` → `Embedder.embed()` → cache lookup (hit → skip API; miss → retry-wrapped `_embed_batch()`) → success: batched OpenRouter call → [Embedding Cache](/doc/feature/embedding_cache.md) write → `list[list[float]]`, same order as input; failure: DLQ write → EmbedderError raised.

## Why the cache

Cost-saving measure for billion-scale ingestion. Medical corpora have significant repeated text (boilerplate consent language, repeated section headers, and any re-ingestion run re-processing the same source documents) — the cache makes identical `(model, text)` pairs a guaranteed cache hit rather than a re-billed API call.

## Retry Strategy

`_embed_batch()` is decorated with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)` (using tenacity library) to handle transient API failures:

- **3 retries** — up to 3 attempts total (1 initial + 2 retries)
- **Exponential backoff** — wait 2-10 seconds between retries (backoff doubles each attempt, capped at 10s)
- **Reraise on exhaustion** — if all 3 attempts fail, the exception propagates to `embed()`, which logs the batch to the [Embedding Cache](/doc/feature/embedding_cache.md)'s DLQ and re-raises

**Rationale:** Transient failures (timeouts, rate-limits, network hiccups) are common in high-throughput API ingestion. Exponential backoff gives the provider time to recover without thundering-herd retries. Bounded retries prevent hanging on persistent errors. DLQ persistence ensures failed texts are never silently lost — failed embeddings can be inspected and manually retried later via `EmbeddingCache.get_failed()`.

## Callers

None yet — not wired into `scripts/ingest_documents.py`. This is a real gap: the ingestion pipeline currently stops at chunking and does not call `Embedder`.

## Related

- [Embedding Cache](/doc/feature/embedding_cache.md) — the sqlite-backed cache this module depends on
- [Chunker](/doc/feature/chunker.md) — upstream, produces the `Document` chunks this module embeds
