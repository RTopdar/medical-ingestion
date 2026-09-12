---
type: Module
title: RAGAS Adapters
description: LangChain-shaped wrappers so RAGAS's judge LLM and embeddings run on this repo's existing OpenRouter stack (ChatOpenRouter + Embedder) — no new provider or credential.
resource: eval/ragas_adapters.py
tags: [eval, rag, ragas, openrouter, embeddings, llm]
status: stable
---

# RAGAS Adapters

`eval/ragas_adapters.py`. RAGAS's `evaluate()` needs a judge LLM (`ragas.llms.LangchainLLMWrapper`) and embeddings (`ragas.embeddings.LangchainEmbeddingsWrapper`), both wrapping LangChain-shaped objects. This module supplies both by delegating to what the repo already has — [Chat Router](/doc/feature/chat_router.md) (`ChatRouterService`, OpenRouter -> Groq -> OpenRouter fallback) for chat, [Embedder](/doc/feature/embedder.md) for embeddings — rather than introducing a second embeddings implementation or a new LLM provider.

## Components

- `build_ragas_llm(model=None)` — builds a `ChatRouterService.from_settings(...)` (with `chat_model` overridden to the resolved judge model), wraps `service._router` in `langchain_litellm.ChatLiteLLMRouter(router=..., model=service.config.fallback_chain[0])`, then wraps that in `LangchainLLMWrapper`. Model resolution: explicit `model` arg → `settings.ragas_judge_model` → `settings.chat_model`, then normalized via `_ensure_openrouter_prefix()` (litellm requires an explicit `openrouter/` provider prefix; the old `ChatOpenRouter` client didn't). Previously wrapped `ChatOpenRouter(model=..., temperature=0)` directly — now goes through the same fallback chain as live answer generation. Temperature 0 for consistent judging, independent of the live pipeline's answer-generation temperature (`SearchService.answer` uses 0.7).
- `build_ragas_embeddings()` — wraps a fresh `Embedder()` instance in `LangchainEmbeddingsWrapper`. `Embedder` (see [Embedder](/doc/feature/embedder.md)) now implements `langchain_core.embeddings.Embeddings` (`embed_documents`/`embed_query`, both delegating to its existing `embed`/`embed_one`) specifically so this same class serves both ingestion's batched corpus embedding and RAGAS's judge embeddings — one OpenRouter embeddings implementation, not two.

## Known upstream bug: ragas hard-imports langchain_community.chat_models.vertexai

`ragas` (confirmed on 0.3.9 through 0.4.3, the latest at integration time) unconditionally imports `langchain_community.chat_models.vertexai.ChatVertexAI` at package import time (`ragas/llms/base.py`), purely to add it to an internal list of "known LangChain LLM classes supporting the legacy `.generate()` batch API." That submodule only exists if the optional `langchain-google-vertexai` package is installed — which `langchain_community` does not declare as a real dependency — so a plain `import ragas` crashes with `ModuleNotFoundError` on a clean install, regardless of which LLM provider is actually used.

This repo never uses VertexAI (`ChatOpenRouter` exclusively), so pulling in the full Google Cloud SDK (`langchain-google-vertexai` → `google-cloud-aiplatform`, `google-auth`, etc.) purely to satisfy this dead import was rejected as wasteful. Instead, `ragas_adapters.py` registers a minimal stub module in `sys.modules["langchain_community.chat_models.vertexai"]` (a placeholder `ChatVertexAI` class, never instantiated) **before** importing `ragas`. Any module that imports `ragas` must import `eval.ragas_adapters` first (or transitively) for the stub to take effect — see the import ordering note in [RAGAS Eval Runner](ragas_runner.md).

This is a workaround for an upstream defect, not an architectural choice — remove the stub block once ragas fixes the unconditional import (track via ragas's GitHub issues).

## Related

- [RAGAS Eval Runner](ragas_runner.md) — consumes these factories to run `ragas.evaluate()` against the live pipeline
- [Embedder](/doc/feature/embedder.md) — now `Embeddings`-shaped so it can be reused here
- [Chat Router](/doc/feature/chat_router.md) — `ChatRouterService`/`ChatLiteLLMRouter` usage this module wraps for the judge LLM
- [Search Service + Main REPL](/doc/feature/search_service.md) — the other caller of `ChatRouterService`, for live answer generation
</content>
