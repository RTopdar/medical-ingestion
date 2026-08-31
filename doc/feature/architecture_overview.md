---
name: architecture_overview
type: Concept
title: System Architecture Overview
description: High-level system design — how ingestion, storage, retrieval, and RAG layers interconnect
status: stable
---

# Architecture Overview

medical-ingestion is a modular RAG pipeline. Five layers compose end-to-end:

## 1. Ingestion (load & parse)

**Package:** `ingestion/loaders/`  
**Output:** `langchain_core.documents.Document` (text + metadata)

Loads from multiple sources:
- **PDF** — Docling (structured extraction)
- **Text, Excel/CSV, JSON** — LangChain's native loaders
- **SQL** — SQLModel-backed query, flattened to documents
- **APIs** — ClinicalTrials.gov v2, PubMed Central

Each loader is standalone, composable, testable. See [Loaders](/doc/feature/loaders.md).

## 2. Chunking (split & propagate metadata)

**Module:** `ingestion/chunker.py`  
**Input:** Document → **Output:** Document[] (chunked)

LangChain's recursive text splitter with configurable overlap. Metadata (source, page, author) propagates to every chunk. See [Chunker](/doc/feature/chunker.md).

## 3. Storage & Cache (provenance + dedup + DLQ)

**Package:** `storage/`

### Postgres (relational store)
- **Module:** `storage/postgres.py`, `storage/chunk_store.py`
- **Purpose:** Chunk provenance (which doc→chunk), embedding cache-check, document-level dedup, failed-embedding DLQ
- **Tables:** `chunks` (cache), `failed_embeddings` (retry queue), `ingested_documents` (dedup state)
- **See:** [Chunk Store](/doc/feature/chunk_store.md), [Postgres Storage](/doc/feature/postgres_storage.md), [Alembic Migrations](/doc/feature/alembic_migrations.md)

### SQLite (reference data)
- **Module:** `storage/sql.py`
- **Purpose:** Seed clinical-trials data (2 normalized tables + FK join)
- **Tables:** `clinical_trials`, `eligibility`
- **See:** [SQL Loader](/doc/feature/sql_loader.md)

## 4. Embeddings (vectorization + OpenRouter API)

**Module:** `ingestion/embedder.py`

For each chunk:
1. Check Postgres cache (hash-based) — reuse if found
2. Call OpenRouter `/embeddings` if miss
3. Retry on transient failure (tenacity backoff)
4. Log failures to DLQ, continue

**See:** [Embedder](/doc/feature/embedder.md), [Chunk Store](/doc/feature/chunk_store.md)

## 5. Vector DB (similarity search backend)

**Package:** `vector_db/`, Docker service: `docker-compose.qdrant.yml`

**Engine:** Qdrant v1.19+ (local HTTP 6333 + gRPC 6334)

- Stores embeddings + chunk metadata as points
- Supports dense vector search + payload filtering
- Persistent volume (`volumes/qdrant/`) survives restarts
- **See:** [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md)

## Retrieval & Generation (RAG pipeline, production)

**Package:** `retrieval/` + `scripts/main.py` REPL

Two-stage search then LLM:

1. **Stage 1: Fuse dense + sparse**
   - Dense: Qdrant vector similarity
   - Sparse: BM25 lexical index
   - Fuse: Reciprocal rank fusion (RRF)
   - **See:** [Hybrid Search Retrieval](/doc/feature/hybrid_search_retrieval.md), [BM25 Sparse Index](/doc/feature/bm25_index.md)

2. **Stage 2: Rerank**
   - OpenRouter `/rerank` cross-encoder on shortlist
   - **See:** [Cross-Encoder Reranker](/doc/feature/reranker.md)

3. **Stage 3: Generate**
   - Grounded LLM response over reranked context
   - **See:** [Search Service](/doc/feature/search_service.md)

## End-to-End Flow

```
ingest_documents.py
  ├─ Loader (PDF/JSON/SQL/API)
  ├─ Chunker (split + propagate metadata)
  ├─ Embedder (OpenRouter cache-check, DLQ on fail)
  ├─ ChunkStore (Postgres: cache, provenance, dedup, DLQ)
  └─ Qdrant sync (upsert points + payloads)

similarity_search_demo.py / search_service.py
  ├─ Embed user query (cache-checked)
  ├─ Hybrid search (dense Qdrant + sparse BM25)
  ├─ Rerank (OpenRouter cross-encoder)
  └─ Generate (LLM + streaming)
```

## Data Models

**Core tables:**
- `ingested_documents` — document-level dedup state, created_at, updated_at
- `chunks` — chunk hash, embedding vector, metadata (source, page, doc_id), created_at
- `failed_embeddings` — retry queue for chunks that hit API errors
- `clinical_trials`, `eligibility` — reference data for seed + SQL loader

**See:** [Data Models](/doc/feature/models.md)

## Configuration

Settings from environment (`.env` or shell):
- `OPENROUTER_API_KEY` — embeddings + rerank + LLM
- `POSTGRES_DSN` — chunk store
- `QDRANT_URL` — vector search
- `EMBEDDING_MODEL` — which embedding endpoint
- `CHUNK_SIZE`, `CHUNK_OVERLAP` — chunking params

**See:** README Configuration section.

## Observability

**Structured JSON logging** across all layers:
- Event name + semantic context (module, operation, status)
- Structured fields (chunk_id, doc_id, error_code)
- Stdout stream + optional file sink

**See:** [Logging Configuration](/doc/feature/logging_config.md)

## Key Design Decisions

| Decision | Reasoning | Docs |
|----------|-----------|------|
| Postgres for cache, not pgvector | pgvector had initialization overhead; Qdrant is faster, simpler | [Postgres Storage](/doc/feature/postgres_storage.md) |
| LangChain Document + metadata | Familiar format, built-in splitter, works with all loaders | [Models](/doc/feature/models.md) |
| Alembic for schema migrations | Committed, reproducible, no drift on existing tables | [Alembic Migrations](/doc/feature/alembic_migrations.md) |
| Hybrid search (dense + sparse) | Precision (dense) + recall (sparse) — neither alone is complete | [Hybrid Search](/doc/feature/hybrid_search_retrieval.md) |

---

## Next Steps

- **Learn one module:** Pick a concept doc from [Architecture Bundle Index](/doc/feature/index.md)
- **See it work:** Run `uv run scripts/similarity_search_demo.py` (interactive REPL, no setup needed if services running)
- **Extend:** Add a new loader, chunker strategy, or reranker — modules are standalone + testable
- **Troubleshoot:** Check [doc/bug/index.md](/doc/bug/index.md) for known incidents
