---
type: Incident
title: RAGAS eval crash — OpenRouter `free` alias silently returns HTTP 200 with empty content
description: OpenRouter's openrouter/free root-level auto-router alias occasionally returns a well-formed 200 streaming completion with entirely empty delta.content across all chunks, tripping RAGAS's non-empty-answer assertion; not detectable by litellm's Router since nothing is malformed or erroring.
status: resolved
resource: llm/chat_router.py
tags: [llm, litellm, openrouter, streaming, ragas, eval, router]
---

# RAGAS eval crash — OpenRouter `free` alias silent empty completion

Affects: [Chat Router](/doc/feature/chat_router.md)

Related: [INC-001](/doc/bug/incidents/INC-001-openrouter-free-model-404-fallback-storm.md) — same `openrouter/free` alias, different failure mode (hard 404 + cooldown storm there, silent 200-with-empty-content here).

## Root cause

`eval/ragas_runner.py` crashed with `AssertionError: expected non-empty str answer` on query 29/37 ("What is the purpose of the NHRI-RP-1 genomic reference panel for Taiwan?"), while the other 36 queries in the same run succeeded.

OpenRouter's `openrouter/free` alias is a root-level auto-router across free community models. Per-request, per-routed-to-model, it can intermittently return an HTTP 200 success response with a well-formed streaming completion in which every chunk's `delta.content` is empty — not an error, not a 404, just a content-less success. This is a property of whichever free model OpenRouter happened to route to for that specific call, so it's non-deterministic and non-systemic (only 1 of 37 calls hit it in this run).

litellm's `Router` has no mechanism to detect or retry this: the response is schema-valid at the HTTP/litellm level, so no cooldown, fallback, or retry logic triggers. This is a distinct failure mode from INC-001 (bare `free` 404 on the wire) — that one was a request-shape bug fixed by fully-qualifying the model id; this one is a genuine intermittent upstream quirk of the free-tier alias that no request-shape fix can prevent.

## Resolution method

Modified `ChatRouterService.stream()` in `llm/chat_router.py` (lines ~57-75):

- Materializes all chunks from the router's streaming `completion()` call into a list (was previously a lazy generator pass-through).
- Checks whether any chunk has non-empty `delta.content`.
- If all chunks are empty on the first attempt, logs a warning and retries the same completion call once.
- If the retry also comes back empty, yields the (possibly still-empty) chunks from the second attempt rather than looping further — avoids masking a genuinely persistent problem behind infinite retries.
- `complete()` (non-streaming path, used elsewhere) is untouched — not implicated by this bug, which is specific to streamed chunk aggregation.

## Final status

Resolved.
