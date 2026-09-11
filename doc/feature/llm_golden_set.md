---
type: Module
title: LLM Answer Golden Set
description: RAGAS-style eval dataset generator for the grounded LLM answer-generation step (SearchService.answer) — query, verbatim contexts, distractor contexts, reference answer, difficulty tag.
resource: eval/llm_golden_set.py
tags: [eval, rag, golden-set, ragas, citations, llm]
status: stable
---

# LLM Answer Golden Set

`eval/llm_golden_set.py` generates `eval/llm_golden_set.json` — an eval dataset for the LLM answer-generation step (`retrieval/search.py::SearchService.answer`, the RAG grounded-answer + citation step), distinct from [Retrieval Golden Set](retrieval_golden_set.md) which evals search ranking only.

## Components

- `GOLDEN_SET` — 37 items, each `{query, relevant_doc_ids, contexts, distractor_contexts, ground_truth, difficulty}`:
  - `contexts` — verbatim real excerpts from `dummy_docs/pmc_documents.json`, so faithfulness/recall checks are grounded in the actual corpus (not invented text).
  - `distractor_contexts` — verbatim excerpts from unrelated docs, used for context_precision stress and no-answer refusal tests.
  - `ground_truth` — reference answer for correctness scoring.
  - `difficulty` — `easy` (12 items) / `medium` (12 items, straightforward grounded answers), `hard_distractor` (9 items, relevant + irrelevant contexts mixed to stress ranking/precision), `no_match` (4 items, only distractors present — pipeline should refuse/say "not in documents" rather than hallucinate).
- `main()` — validates all non-empty `relevant_doc_ids` exist in `dummy_docs/pmc_documents.json`, writes `eval/llm_golden_set.json`.

## Supports RAGAS-style metrics

- **faithfulness** — generated answer vs `contexts` (no unsupported claims)
- **answer_relevancy** — generated answer vs `query`
- **context_precision** — relevant `contexts` ranked above `distractor_contexts`
- **context_recall** — `contexts` vs `ground_truth` (all needed info present)
- **answer_correctness** — generated answer vs `ground_truth`

Consumed by [RAGAS Eval Runner](ragas_runner.md), which scores `SearchService.answer` output (live pipeline, not this file's pre-baked `contexts`) against this dataset using RAGAS — closes the "no eval runner exists yet" gap from earlier versions of this doc.

## Related

- [RAGAS Eval Runner](ragas_runner.md) — scores the live pipeline against this dataset
- [Retrieval Golden Set](retrieval_golden_set.md) — sibling golden set for the retrieval-ranking step, same doc corpus and generator pattern
- [Search Service + Main REPL](search_service.md) — `SearchService.answer` is the system under eval
- [Citation Mapping](citation_mapping.md) — inline `[N]` citation behavior this eval indirectly covers via faithfulness/correctness
