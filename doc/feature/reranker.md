---
type: Module
title: Cross-Encoder Reranker
description: OpenRouter /rerank endpoint wrapper, second-pass reorder over the RRF-fused hybrid search shortlist.
resource: retrieval/reranker.py
tags: [retrieval, reranking, openrouter, cross-encoder]
status: stable
---

# Cross-Encoder Reranker

`retrieval/reranker.py::Reranker` calls OpenRouter's dedicated `POST /rerank` endpoint — **not** `/chat/completions` — to jointly score query+document pairs, as a second pass over [Hybrid Search Retrieval](hybrid_search_retrieval.md)'s RRF-fused shortlist.

## Why a separate pass from RRF

RRF fuses by rank only (see [Hybrid Search Retrieval](hybrid_search_retrieval.md)) — it never looks at query/document content jointly. A cross-encoder reranker scores each fused candidate against the actual query text, which is more accurate but far more expensive per-candidate, so it only runs over the already-shrunk fused shortlist (`fetch_k`, not the full corpus).

## Behavior

- `__init__(model=None, timeout=30)` — `model` defaults to `settings.reranker_model` (env `RERANKING_MODEL`, default `nvidia/llama-nemotron-rerank-vl-1b-v2:free`).
- `rerank(query, candidates, top_n=None)` — `candidates` is a list of dicts each carrying a `text` key (the fused output of `HybridRetriever.search()`). POSTs `{model, query, documents}` to `https://openrouter.ai/api/v1/rerank`. Returns candidates in relevance order, each annotated with a `relevance_score` key. Empty candidate list short-circuits to `[]` without an API call.
- Raises `RuntimeError` on a non-2xx response.

## OpenRouter MCP guard note

This module makes a direct HTTP call to OpenRouter's REST API (`requests`), not via the `openrouter` MCP server — the MCP server's allowed toolset (AGENTS.md rule #11) is for agent-time doc/model lookups, not runtime application traffic. No conflict: the guard applies to agent tool calls, not to code the agent writes that itself calls OpenRouter APIs at runtime.

## Related

- [Hybrid Search Retrieval](hybrid_search_retrieval.md) — produces this module's input shortlist
- [Search Service + Main REPL](search_service.md) — caller, final orchestration stage
