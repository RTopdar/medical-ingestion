---
type: Module
title: Retrieval Golden Set
description: Hand-picked query -> relevant doc_id(s) eval dataset generator for retrieval quality (BM25/hybrid/reranker), spanning easy/hard/multilingual/no-match cases.
resource: eval/golden_set.py
tags: [eval, retrieval, golden-set, bm25, hybrid, reranker]
status: stable
---

# Retrieval Golden Set

`eval/golden_set.py` generates `eval/golden_set.json` — a fixed query -> `relevant_doc_ids` mapping used to evaluate retrieval quality (BM25, hybrid RRF fusion, cross-encoder reranker) independent of LLM answer generation.

## Components

- `GOLDEN_SET` — list of dicts, each `{query, relevant_doc_ids, difficulty}`. Queries drawn against `dummy_docs/pmc_documents.json`. Difficulty tags: easy (title/keyword overlap), hard (paraphrased, no lexical overlap), multilingual, no_match.
- `main()` — validates every `relevant_doc_ids` entry actually exists in `dummy_docs/pmc_documents.json` (raises `ValueError` on unknown doc_id), then writes `eval/golden_set.json`.

## Scope

Evaluates retrieval ranking only (did the right doc surface, at what rank) — no ground-truth answer text, no context/faithfulness checks. For LLM answer-generation eval (RAGAS-style faithfulness/relevancy/correctness), see [LLM Answer Golden Set](llm_golden_set.md).

No eval runner exists yet for either golden set — these are dataset-generation scripts only; the runner is a future step.

## Related

- [LLM Answer Golden Set](llm_golden_set.md) — sibling golden set for the generation step, same doc corpus
- [Search Service + Main REPL](search_service.md) — production retrieval path this set indirectly validates
- [Hybrid Search Retrieval](hybrid_search_retrieval.md)
- [Cross-Encoder Reranker](reranker.md)
