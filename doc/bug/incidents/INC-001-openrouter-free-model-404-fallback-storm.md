---
type: Incident
title: RAGAS eval crashes — OpenRouter `free` alias 404s on wire, silent Groq fallback storm
description: litellm strips the openrouter/ provider prefix, so openrouter/free goes on the wire as bare "free" and 404s; router silently fails over to Groq every call, draining the 8k TPM cap and crashing the eval run.
status: resolved
resource: llm/chat_router.py, llm/config.py
tags: [llm, litellm, openrouter, groq, fallback, router, ragas, eval]
---

# RAGAS eval crashes — OpenRouter `free` alias 404 on wire

Affects: [Chat Router](/doc/feature/chat_router.md)

## Root cause

litellm strips the `openrouter/` provider prefix from the model id it sends to OpenRouter on the wire. So `chat_model=openrouter/free` was sent to OpenRouter as bare `model: "free"`, and OpenRouter rejects a bare `free` with 404 `"No endpoints available for openrouter/free"`. Empirically confirmed: `model="openrouter/free"` -> 200, `model="free"` -> 404.

Consequence: the openrouter-primary deployment 404'd on every call and the router silently failed over to Groq every time. Under the eval's tight 37-record loop Groq's ~8k TPM cap drained within a few calls, leaving no viable provider and crashing the run with `litellm.NotFoundError: OpenrouterException` plus a Groq `RateLimitError`. Interactive main.py masked the bug because human-paced queries let litellm's default 5s cooldown recover between calls.

## Resolution method

- Added `_openrouter_wire_model_id()` in `llm/chat_router.py`: double-prefixes only root-level OpenRouter aliases (`openrouter/free` -> `openrouter/openrouter/free`) so litellm sends the fully-qualified `openrouter/free` id; real model ids (with a `/` after the prefix) are untouched.
- Secondary hardening:
  - openrouter-primary sets `model_info={"cooldown_time": 0}` — a transient 404 no longer cooldowns/stalls the deployment for 5s (keeps it per-call available, matching the old stateless direct call).
  - groq-fallback sets `max_tokens=1024` — survives the ~8k TPM cap for `gpt-oss-120b` over more calls.
  - `LiteLLMDeployment.model_info: dict` added in `llm/config.py` to pass the per-deployment setting through (litellm requires `model_info` to be a dict, not None).
- Verified: wire shows `model='openrouter/free'` -> 200, stream/non-stream both OK, 23 unit tests pass, `eval.ragas_runner --limit 1` completes with all `200 OK`.

## Final status

Resolved.