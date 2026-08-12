---
type: Module
title: Data Models
description: Pydantic models — the single source of truth for all data structures per AGENTS.md rule 6.
resource: models/
tags: [models, pydantic]
status: stable
---

# Data Models

`models/`. Per [AGENTS.md](/AGENTS.md) rule 6, every data structure in the codebase is a Pydantic model defined here — no plain dicts/tuples/ad-hoc classes in feature modules.

## `models/documents.py`

- `Metadata` — `source`, `source_type`, `created_at`, `tags`, `extra` (free-form dict for domain-specific fields).
- `Document` — `id`, `content`, `title`, `metadata: Metadata`.
- `Chunk` — `id`, `document_id`, `content`, `start_idx`, `end_idx`, `metadata: Metadata`.

Produced by [Loaders](/doc/feature/loaders.md), consumed and split into `Chunk` by [Chunker](/doc/feature/chunker.md).

## `models/vectors.py`

- `Vector` — `chunk_id`, `embedding`, `model`, `dimension`.
- `EmbeddingRequest` — `text`, `model`.
- `EmbeddingResult` — `text`, `embedding`, `model`, `dimension`.

Not yet wired to any embedding service in the codebase (no consumer module exists yet).

## `models/rag.py`

- `RetrievedContext` — `chunk: Chunk`, `similarity_score`, `rank`.
- `RAGQuery` — `query`, `top_k`, `filters`.
- `RAGResponse` — `query`, `answer`, `retrieved_contexts`, `model`, `source_citations`.

Not yet wired to any retrieval/generation service in the codebase.
