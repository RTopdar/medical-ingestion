---
type: Module
title: Alembic Migrations
description: Postgres schema migration tooling wired to SQLModel.metadata, replacing bare create_all for existing tables.
resource: migrations/
tags: [postgres, alembic, migrations, sqlmodel]
status: stable
---

# Alembic Migrations

`migrations/` (Alembic) manages Postgres schema evolution for the SQLModel tables defined in `models/vectors.py` (`Chunk`, `FailedEmbedding`, `IngestedDocument`) and `models/clinical_trial.py`.

## Why

`storage/postgres.py::init_db()`'s `SQLModel.metadata.create_all(engine)` only creates missing tables — it never alters an existing table's columns/types/constraints. Once a table already has a live schema, changing a model field (add/rename/remove/retype) drifts silently from what's actually in Postgres, surfacing as a runtime `UndefinedColumn` error rather than a caught migration-time failure.

## Structure

- `alembic.ini` — Alembic config at project root.
- `migrations/env.py` — wires Alembic's autogenerate to `SQLModel.metadata` by importing `models/vectors.py` (so table metadata is registered before autogenerate diffs against the live DB).
- `migrations/versions/7468fa8fd0b2_baseline.py` — baseline revision capturing the schema as of the Postgres migration (chunks/failed_embeddings/documents tables).
- `migrations/script.py.mako` — revision template.

## Workflow (see AGENTS.md rule #6b / CLAUDE.md rule #6b)

```bash
source .venv/bin/activate
alembic revision --autogenerate -m "<description>"   # review — autogenerate misses renames, some type/constraint changes
alembic upgrade head
```

`create_all` remains fine only for bootstrapping a brand-new table with no prior migration history; never hand-write `ALTER TABLE` against the live DB.

## Related

- [Data Models](models.md) — `models/vectors.py`, the SQLModel table definitions this tooling migrates
- [Postgres Storage](postgres_storage.md) — `storage/postgres.py::init_db()`, the `create_all` bootstrap this supplements
