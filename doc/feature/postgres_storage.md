---
type: Module
title: Postgres Storage
description: SQLAlchemy engine + SQLModel table setup for chunk provenance, embedding cache, document dedup, and the failed-embedding DLQ. Relational-only — not a vector search backend.
resource: storage/postgres.py
tags: [storage, postgres, sqlmodel, infrastructure]
status: stable
---

# Postgres Storage

`storage/postgres.py`. Minimal engine/session setup module — mirrors `storage/sql.py`'s pattern (`SQLModel.metadata.create_all()`, no migrations anywhere in this repo), just pointed at Postgres instead of sqlite. **Built on SQLModel** for type-safe ORM queries — all table schemas are inferred from typed Pydantic models ([Data Models](/doc/feature/models.md): `Chunk`, `FailedEmbedding`, `IngestedDocument`), and all queries use the `select()` API with typed column references (e.g., `select(Chunk)` where `Chunk.content_hash` has full IDE autocomplete and type hints).

## Components

- `engine: Engine` — `create_engine(settings.postgres_dsn)`, module-level singleton, imported by [Chunk Store](/doc/feature/chunk_store.md) and `scripts/ingest_documents.py` as the default engine.
- `init_db()` — `SQLModel.metadata.create_all(engine)`, creates the `chunks`, `failed_embeddings`, and `documents` tables (from [Data Models](/doc/feature/models.md)'s `Chunk`/`FailedEmbedding`/`IngestedDocument`) if missing. Called once at pipeline start in `scripts/ingest_documents.py::main()`.

## Settings

`settings.postgres_dsn` (env `POSTGRES_DSN`, default `postgresql://postgres:postgres@localhost:5432/medical_ingestion`).

## Architecture decision: pgvector rejected, Qdrant kept for similarity search

**pgvector was explicitly considered and rejected mid-design.** Postgres's `embedding` column on the `chunks` table (see [Data Models](/doc/feature/models.md)) is a plain JSON list — used **only** for cache-hit-avoidance lookups (skip re-paying OpenRouter for duplicate text via `ChunkStore.find_by_hash`), never for similarity search. [Qdrant](/doc/feature/qdrant_infrastructure.md) remains the sole vector-search backend. This is a deliberate reversal from an earlier plan direction that considered using pgvector for combined relational+vector storage (see the superseded "ORM for relational storage" decision in [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md)) — the final split is: Postgres for relational provenance/cache, Qdrant for vector search, no vector extension in Postgres. `docker-compose.postgres.yml` uses a plain `postgres:16` image, no pgvector extension.

## Infrastructure

- `docker-compose.postgres.yml` — mirrors `docker-compose.qdrant.yml`'s pattern (see [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md)). Plain `postgres:16` image.
- `scripts/start_postgres.sh` — mirrors `scripts/start_qdrant.sh`'s idempotent startup pattern.

## Data flow

`scripts/ingest_documents.py::main()` calls `init_db()` once before the pipeline runs → [Chunk Store](/doc/feature/chunk_store.md) uses `engine` for all Postgres reads/writes.

## Related

- [Chunk Store](/doc/feature/chunk_store.md) — the repository class that operates against this engine
- [Data Models](/doc/feature/models.md) — `Chunk`, `FailedEmbedding`, `IngestedDocument` SQLModel table classes
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — the vector-search backend this module deliberately does not replace
