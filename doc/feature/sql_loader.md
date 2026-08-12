---
type: Module
title: SQL Loader (Storage Layer)
description: SQLModel-backed (SQLite) persistence for ClinicalTrial + Eligibility records (storage/), plus a dedicated loader (ingestion/loaders/sql_loader.py) that converts joined rows into langchain_core.documents.Document with flattened metadata for the shared chunk pipeline.
resource: storage/, ingestion/loaders/sql_loader.py
tags: [storage, sqlite, sqlmodel, orm, database, clinicaltrials]
status: stable
---

# SQL Loader (Storage Layer)

Two modules, split by responsibility (as of 2026-08-12):

- `storage/` — pure persistence: schema, seed, query. Never returns `Document`, never imports `models.documents` or `langchain_core.documents`.
- `ingestion/loaders/sql_loader.py` — the actual "loader" in the [Loaders](/doc/feature/loaders.md) sense: wraps `storage.SQLLoaderService` and converts query results into `langchain_core.documents.Document`.

This mirrors how PDF/Excel/JSON already separate loading from storage, and fixes an architectural inconsistency flagged mid-migration: `storage/` previously had a `.load()` method that returned `Document`, which meant the storage layer knew about the ingestion pipeline's document type. That conversion now lives with the other loaders. First module in the `storage` layer described in [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) Components #8 — a relational-DB path that runs parallel to the file-based [Loaders](/doc/feature/loaders.md), converging on the same `Document` type downstream (chunking only — no `Chunk` type exists anymore, see [Data Models](/doc/feature/models.md)). Built entirely on **SQLModel** (Pydantic + SQLAlchemy ORM) — no raw SQL strings anywhere in either module.

## Files

- `storage/sql.py` — `SQLLoaderService`, the only class in the package. Pure persistence only (no `Document`-returning method).
- `storage/__init__.py` — re-exports `SQLLoaderService`.
- `ingestion/loaders/sql_loader.py` — `SQLDataLoaderService`, registered as `LoaderFactory.sql_loader(db_path)`. Wraps `storage.SQLLoaderService` internally in `.load()`.

## Schema

Two normalized tables, mirroring the ClinicalTrials.gov API's own module boundary (`identificationModule`/`statusModule`/`designModule` vs `eligibilityModule`) rather than fabricating fake patient-level rows — the real API never exposes per-patient data (PHI). (inferred rationale from code, confirmed in IMPLEMENTATION_PLAN.md)

- `clinical_trials` — `nct_id` (primary key), `title`, `status`, `phase`, `condition`, `sponsor`, `summary`, `start_date`, `enrollment_count`.
- `eligibility` — `nct_id` (primary key, FK to `clinical_trials.nct_id`, 1:1), `sex`, `minimum_age`, `maximum_age`, `std_ages`, `healthy_volunteers`, `population`.

Table DDL is **not hand-written** — it's derived from the [`ClinicalTrial`/`Eligibility`](/doc/feature/models.md) `SQLModel(table=True)` class definitions via `SQLModel.metadata.create_all()`. Table names are not hardcoded in `storage/sql.py` either: they come from `ClinicalTrial.__tablename__`/`Eligibility.__tablename__`, which each model sets from `settings.clinical_trials_table`/`settings.eligibility_table` at class-definition time — renaming a table only requires a settings/env change, never a code change here or in `models/clinical_trial.py`.

## `SQLLoaderService` (`storage/sql.py`)

Pure persistence — no `Document`-returning method (`.load()` removed 2026-08-12, see `SQLDataLoaderService` below).

- `__init__(db_path)` — creates the SQLite file's parent dir if needed, builds a SQLAlchemy `Engine` via `create_engine(f"sqlite:///{db_path}")`, and calls `SQLModel.metadata.create_all(self.engine)` to create both tables if they don't exist.
- `seed(trials: list[ClinicalTrial], eligibility_records: list[Eligibility]) -> int` — opens a `Session`, calls `session.merge(obj)` per record for both tables (upsert, safe to re-run/re-seed), commits. Returns the trial row count written.
- `query(*predicates) -> list[ClinicalTrial]` — `select(ClinicalTrial).where(*predicates)`, trial-level only, no join. Returns `ClinicalTrial` model instances directly (they're the ORM row class). **Breaking change** (predates the Document migration): signature changed from `(where: str = "1=1", params: tuple = ())` (raw SQL WHERE string + params) to `(*predicates)` (SQLModel/SQLAlchemy column expressions). Callers now write `loader.query(ClinicalTrial.status == "RECRUITING")` instead of `loader.query("status = ?", ("RECRUITING",))`.
- `query_with_eligibility(*predicates) -> list[tuple[ClinicalTrial, Eligibility | None]]` — `select(ClinicalTrial, Eligibility).join(Eligibility, isouter=True, onclause=col(Eligibility.nct_id) == col(ClinicalTrial.nct_id)).where(*predicates)`. Returns one `(ClinicalTrial, Eligibility | None)` tuple per trial row (eligibility is `None` if no matching row). Same breaking predicate-based signature as `query()`.

## `SQLDataLoaderService` (`ingestion/loaders/sql_loader.py`)

The actual `Document`-producing loader, registered as `LoaderFactory.sql_loader(db_path)`. Config-only Pydantic `BaseModel` (`db_path: Path`), consistent with the other four loaders in [Loaders](/doc/feature/loaders.md).

- `load(*predicates) -> list[langchain_core.documents.Document]` — constructs a `storage.SQLLoaderService(self.db_path)` internally and calls `.query_with_eligibility(*predicates)`. Converts each `(ClinicalTrial, Eligibility | None)` pair into a `Document`: `page_content` is `title + "\n\n" + summary`, plus an appended `"\n\nEligibility: sex=X, age=Y-Z, healthy_volunteers=..."` line when eligibility exists. Metadata is **fully flattened** — deliberately no nested dicts, since vector-store metadata filters (Chroma etc.) generally only support flat scalar values: every `ClinicalTrial` field becomes its own top-level key (via `trial.model_dump(exclude={"title"})`), every `Eligibility` field becomes `eligibility_<field>` (e.g. `eligibility_sex`, `eligibility_minimum_age`), plus `source` (`sqlite:{db_path}`), `source_type` (`"db"`), `title`, and `tags` (`[status, phase]`). `None`-valued fields are dropped. This is a change from the pre-migration `storage/sql.py::SQLLoaderService.load()`, which nested eligibility under a single `extra["eligibility"]` dict — flattening was adopted specifically for metadata-filter compatibility.

## Why SQLModel

Chosen so that if the DB backend later moves to Postgres/pgvector (for combined relational+vector storage), only `create_engine()`'s URL needs to change — query code written against `select()`/column-expression predicates stays stable, unlike raw SQL strings which would need rewriting. Table names are configurable via `settings.py` for the same reason. (Rationale confirmed in IMPLEMENTATION_PLAN.md.)

## Data flow

[ClinicalTrials Fetcher](/doc/feature/clinicaltrials_fetcher.md) → `(ClinicalTrial, Eligibility)` model lists → `SQLLoaderService.seed(trials, eligibility_records)` (SQLModel `session.merge()`) → SQLite, two tables with FK (`settings.sqlite_db_path`, default `./data/medical.db`) → `SQLDataLoaderService.load()` (constructs a `SQLLoaderService` internally, calls `query_with_eligibility()`, a `select().join(isouter=True)`) → `Document` with flattened metadata → [Chunker](/doc/feature/chunker.md) (not yet wired into `scripts/ingest_documents.py` — see Status below).

Tested live: dropped and re-seeded a fresh `./data/medical.db` with 50 trials + eligibility records from the real ClinicalTrials.gov API across 5 conditions, then round-tripped through `query()`, `query_with_eligibility()` (join), and `SQLDataLoaderService.load()` (`Document` conversion, confirmed `langchain_core.documents.base.Document` instances with no dict values in any metadata key) successfully. Also chunked in combination with `JSONLoaderService` output through `ChunkerService.chunk()` — 53 chunks, all with `start_index` present in metadata.

## Consumers

- `scripts/seed_clinical_trials_db.py` — unpacks `trials, eligibility_records = fetch_dummy_trials(...)` and calls `loader.seed(trials, eligibility_records)` for conditions `[diabetes, cancer, hypertension, asthma, alzheimer]`. Uses `storage.SQLLoaderService` directly (persistence only), unaffected by the loader-layer split.
- `LoaderFactory.sql_loader(db_path)` → `SQLDataLoaderService` — the `Document`-producing path, for callers that want chunk-ready output (see Status below for wiring status).

## Status / open gap

`SQLDataLoaderService.load()` output is not yet consumed by [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — the SQLite path is seeded and query/load-verified but still a separate entry point from the main `scripts/ingest_documents.py` run. Wiring it in is a natural next step (inferred from code, not yet decided). This gap predates and is unaffected by the storage/loader split or the Document-type migration.
