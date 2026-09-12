---
type: Module
title: Chat Router (litellm fallback chain)
description: Single reusable litellm.Router wrapper providing an OpenRouter -> Groq -> OpenRouter chat fallback chain, consumed by both answer generation and the RAGAS judge LLM.
resource: llm/chat_router.py
tags: [llm, litellm, groq, openrouter, fallback, router, chat]
status: stable
---

# Chat Router

`llm/` package (`llm/config.py` + `llm/chat_router.py`). Replaces the previous per-call `ChatOpenRouter` construction in `retrieval/search.py` and `eval/ragas_adapters.py` with one shared `litellm.Router`-backed service, so the OpenRouter->Groq->OpenRouter fallback chain is defined exactly once.

## Why

Prior to this feature, both `SearchService.answer()` and the RAGAS judge LLM built `ChatOpenRouter` directly, per call, with no fallback if OpenRouter had an outage or rate-limited. `litellm.Router` gives provider-level fallback (retry on a different provider, not just a different model on the same provider) without hand-rolling retry/failover logic twice.

## Components

- `llm/config.py` — strict pydantic (`ConfigDict(strict=True, extra="forbid")`) models describing a litellm Router configuration, so no raw dict is ever handed to `litellm.Router` unvalidated:
  - `LiteLLMModelParams` — model/api_key/api_base/temperature/max_tokens/timeout. `model` is validated to require a provider prefix (e.g. `groq/llama-3.3-70b`, `openrouter/...`) via `must_have_provider_prefix`.
  - `LiteLLMDeployment` — `model_name` + `litellm_params`, one entry in `Router`'s `model_list`.
  - `ChatRouterConfig` — `deployments` list + ordered `fallback_chain` of `model_name`s. `chain_references_known_deployments` validator rejects a chain entry that doesn't match a declared deployment.
- `llm/chat_router.py::ChatRouterService` — owns one `litellm.Router` built from a validated `ChatRouterConfig`.
  - `.complete(messages, **kwargs)` / `.stream(messages, **kwargs)` — both call `router.completion(model=fallback_chain[0], ...)`; litellm's Router internally walks the `fallbacks` mapping on failure, not the caller.
  - `.from_settings(settings)` classmethod — builds the project's standard 3-step chain: `["openrouter-primary", "groq-fallback", "openrouter-primary"]` (OpenRouter primary → Groq → retry OpenRouter once more), not a simple 2-provider fallback. Deployment configs pull `settings.chat_model`/`settings.openrouter_api_key`/`settings.openrouter_base_url` (primary) and `settings.groq_chat_model`/`settings.groq_api_key` (fallback).

## Settings

Two new fields on `settings.Settings` (now a `pydantic_settings.BaseSettings` subclass — see below), both consumed only by `ChatRouterService.from_settings`:

- `groq_api_key` (env `GROQ_API_KEY`, default `""`)
- `groq_chat_model` (env `GROQ_CHAT_MODEL`, default `groq/openai/gpt-oss-120b`)

## Callers

- [Search Service + Main REPL](search_service.md) — `SearchService.__init__` builds one `self.chat_router = ChatRouterService.from_settings(settings)`; `answer()` streams through `.stream(...)` instead of constructing `ChatOpenRouter` per call. Public generator behavior (yields string chunks) unchanged.
- [RAGAS Adapters](ragas_adapters.md) — `build_ragas_llm()` builds a `ChatRouterService` via `.from_settings(...)`, then wraps `service._router` in `langchain_litellm.ChatLiteLLMRouter(router=..., model=...)`, then in ragas's `LangchainLLMWrapper`. A `_ensure_openrouter_prefix()` helper normalizes bare model ids (the old `ChatOpenRouter`-era convention still documented in `.env.example` for `RAGAS_JUDGE_MODEL`) to `openrouter/...`, since litellm requires explicit provider prefixes unlike the old direct client.

## Not touched

Embeddings (`ingestion/embedder.py`) and reranking (`retrieval/reranker.py`) still call OpenRouter directly via raw HTTP — Groq has no embeddings/rerank API, so there is nothing to fall back to there.

## Related

- [Search Service + Main REPL](search_service.md)
- [RAGAS Adapters](ragas_adapters.md)
- [Embedder](embedder.md)
