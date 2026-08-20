---
type: Module
title: Data Models
description: Pydantic models — the single source of truth for all data structures per AGENTS.md rule 6, except document/chunk data which is plain langchain_core.documents.Document.
resource: models/
tags: [models, pydantic]
status: stable
---

# Data Models

`models/`. Per [AGENTS.md](/AGENTS.md) rule 6, every data structure in the codebase is a Pydantic model defined here — no plain dicts/tuples/ad-hoc classes in feature modules. **Exception (2026-08-12):** document/chunk data is no longer a custom Pydantic wrapper — see `models/documents.py` below.

## `models/documents.py`

No longer defines `Document`, `Chunk`, or `Metadata` classes (removed 2026-08-12). The file is kept as a docstring-only stub — not deleted — so any stale `from models.documents import Document` (or `Chunk`/`Metadata`) import fails loudly at import time instead of silently breaking downstream.

These were superseded by `langchain_core.documents.Document` (`page_content: str`, `metadata: dict`), used directly by every [Loader](/doc/feature/loaders.md) and by [Chunker](/doc/feature/chunker.md). Metadata is a plain dict populated by convention rather than a typed schema: `source`, `source_type`, `title`, `tags`, plus source-specific keys (see each loader's own doc for its exact key set). `models/__init__.py` no longer exports `Document`/`Chunk`/`Metadata`.

**Rationale (inferred from code, confirmed in IMPLEMENTATION_PLAN.md):** every real loader either already produced LangChain Documents internally (Docling, Unstructured) or gained nothing from the extra Pydantic conversion step, and in `ExcelCSVLoaderService`'s case the wrapper was actively discarding Unstructured's native metadata down to one field. See [Loaders](/doc/feature/loaders.md) and [Chunker](/doc/feature/chunker.md) for the new mechanics.

## `models/vectors.py`

Rewritten for the Postgres migration (SQLite `EmbeddingCache`/`DocumentCache` → Postgres). Plain-Pydantic `Vector` model removed (superseded by `Chunk`, below).

- `Chunk` — `SQLModel(table=True)`, table `chunks`. One row per chunk **occurrence** — the same `content_hash` intentionally repeats across rows when identical text appears in multiple documents/patients, so `content_hash` is indexed but **not unique**. Fields: `id` (PK), `content_hash`, `text`, `model`, `embedding` (`list[float]`, JSON column — cache-lookup only, never searched), `metadata_` (dict, JSON column aliased `"metadata"` — carries `source`, `source_type`, `patient_mrn`, `document_id`, etc.), `created_at`. `Chunk.make_content_hash(model, text)` — `staticmethod`, `sha256(f"{model}:{normalized_text}")`, same logic as the old `EmbeddingCache.make_key`.
- `FailedEmbedding` — `SQLModel(table=True)`, table `failed_embeddings`. DLQ, same shape as the old sqlite DLQ table (`content_hash`, `text`, `error`, `model`, `attempt_count`, `created_at`).
- `IngestedDocument` — `SQLModel(table=True)`, table `documents`. `content_hash` primary key, `source`, `ingested_at`. Whole-document dedup gate, replaces the deleted `DocumentCache`. `IngestedDocument.make_content_hash(content)` — `staticmethod`.
- `EmbeddingRequest` — plain `BaseModel`, `text`, `model`. API-boundary type only, unchanged.
- `EmbeddingResult` — plain `BaseModel`, `text`, `embedding`, `model`, `dimension`. API-boundary type only, unchanged.

Consumed by [Chunk Store](/doc/feature/chunk_store.md) (`storage/chunk_store.py`) and [Postgres Storage](/doc/feature/postgres_storage.md) (`storage/postgres.py::init_db`).

## `models/rag.py`

- `RetrievedContext` — `chunk: langchain_core.documents.Document` (retyped 2026-08-12 from the removed `Chunk` model; `class Config: arbitrary_types_allowed = True` added to permit the non-Pydantic type), `similarity_score`, `rank`.
- `RAGQuery` — `query`, `top_k`, `filters`.
- `RAGResponse` — `query`, `answer`, `retrieved_contexts`, `model`, `source_citations`.

Not yet wired to any retrieval/generation service in the codebase.

## `models/clinical_trial.py`

`ClinicalTrial` and `Eligibility` are `SQLModel(table=True)` subclasses, not plain `BaseModel` — the **same class** is both the Pydantic data contract (used everywhere `models/` is used) and the SQLAlchemy ORM table-row class (used by [SQL Loader](/doc/feature/sql_loader.md) to build/query the DB). `Field(...)` comes from `sqlmodel`, not `pydantic`. Each class's `__tablename__` is not hardcoded — it's set from `settings.clinical_trials_table` / `settings.eligibility_table` (read at import time), so renaming a table only requires a settings/env change, never a change to this file.

- `ClinicalTrial` — `nct_id` (`Field(primary_key=True)`), `title`, `status`, `phase`, `condition`, `sponsor`, `summary`, `start_date`, `enrollment_count`. Normalized record from the ClinicalTrials.gov API v2 (`identificationModule`/`statusModule`/`designModule`/etc).
- `Eligibility` — `nct_id` (`Field(primary_key=True, foreign_key="clinical_trials.nct_id")`, 1:1 with `ClinicalTrial`), `sex`, `minimum_age`, `maximum_age`, `std_ages`, `healthy_volunteers`, `population`. Normalized record from the API's `eligibilityModule`, split into its own model/table rather than folded into `ClinicalTrial` — mirrors the API's own module boundary instead of fabricating patient-level rows the API never exposes.

Both produced by [ClinicalTrials Fetcher](/doc/feature/clinicaltrials_fetcher.md) (`parse_trial()` / `parse_eligibility()`) — construction is identical to plain Pydantic models, `SQLModel(table=True)` doesn't change call sites — and stored/queried by [SQL Loader](/doc/feature/sql_loader.md) as two normalized SQLite tables (DDL auto-derived from these class definitions) joined via `query_with_eligibility()`, which also converts the joined pair to `Document` for the shared chunk pipeline.
