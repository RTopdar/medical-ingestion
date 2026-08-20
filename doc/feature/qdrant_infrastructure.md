---
type: Module
title: Qdrant Infrastructure
description: Containerized Qdrant vector database for local development. Docker Compose setup with persistent storage and startup automation.
resource: docker-compose.qdrant.yml, scripts/start_qdrant.sh
tags: infrastructure, vector-db, docker, containerization
status: created
---

# Qdrant Infrastructure

**Package:** Infrastructure (containerized services)  
**Files:** `docker-compose.qdrant.yml`, `scripts/start_qdrant.sh`  
**Status:** ✓ Created (2026-08-13)  
**Purpose:** Provide a reproducible local Qdrant vector database for development, testing, and initial ingestion→embed→store pipeline integration.

## Overview

Qdrant is a vector database optimized for semantic search and similarity retrieval. This project uses Qdrant as the primary vector store backend, running containerized locally via Docker Compose.

**Key properties:**
- **Version:** Qdrant v1.19+ (latest from `qdrant/qdrant:latest` image)
- **Container:** `medical-ingestion-qdrant` (stable name for scripting)
- **Ports:** 
  - `6333` — HTTP REST API
  - `6334` — gRPC protocol (higher throughput for bulk operations)
- **Persistence:** Named volume `qdrant_storage` (survives container restarts, `/qdrant/storage` inside container)
- **Restart policy:** `unless-stopped` (auto-restart on daemon reboot, manual stop stays stopped)

## Files

### docker-compose.qdrant.yml

Docker Compose specification (13 lines, YAML):

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: medical-ingestion-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_storage:
```

**Notes:**
- Single-service setup (no dependencies on external DBs or message queues)
- Volume named `qdrant_storage` — Docker manages lifecycle, mounted at `/qdrant/storage` in container
- Port mappings expose both HTTP (6333) and gRPC (6334) for maximum compatibility

### scripts/start_qdrant.sh

Bash startup script (30 lines):

1. **Checks Docker daemon** — fails early if Docker not running
2. **Tries `docker compose`** — modern Docker CLI (v20.10+)
3. **Falls back to `docker-compose`** — legacy standalone CLI
4. **Final fallback:** `docker run` (if compose CLI/plugin unavailable)
   - Checks if container exists by name (`medical-ingestion-qdrant`)
   - If exists: restarts it
   - If not: creates new container with same parameters as compose file
5. **Prints success message** with dashboard URL

**Idempotent design:** Safe to run multiple times; existing container is restarted, not recreated.

**Usage:**
```bash
bash scripts/start_qdrant.sh
# Output: Qdrant up. Dashboard: http://localhost:6333/dashboard
```

## Architecture Position

**Data flow (wired, current):**

```
[Chunker]
  → Document (chunked)
    → [Embedder] (cache-checks via Chunk Store / Postgres)
      → embeddings + content_hashes
        → [Chunk Store: insert_chunks → Postgres "chunks" table, one row per occurrence]
          → [Chunk Store: sync_to_qdrant → QdrantVectorStore.upsert_one, only new hashes]
            → Qdrant: one point per unique content_hash
              → [RAG Retriever] (planned)
                → [Generator] (planned)
                  → Answer
```

`vector_db/base.py::VectorStore` interface: `upsert_one(content_hash, embedding, metadata, text)` (single point, caller guarantees the hash is new to the store) + `find_by_hash(content_hash)`. `QdrantVectorStore` (`vector_db/qdrant.py`) implements both. Per-occurrence provenance (which patient/document a chunk came from) lives in Postgres, not Qdrant — see [Chunk Store](/doc/feature/chunk_store.md) and [Postgres Storage](/doc/feature/postgres_storage.md). **pgvector was considered and rejected** for vector search — Postgres holds only a JSON `embedding` column for cache-hit checks; Qdrant remains the sole similarity-search backend (see [Postgres Storage](/doc/feature/postgres_storage.md) for the full rationale).

## Why Qdrant

1. **Single binary** — no auxiliary databases, no extra services to manage
2. **Persistent** — unlike FAISS (in-memory), Qdrant stores vectors durably
3. **Feature-complete** — collections, metadata filtering, batch operations, reranking
4. **Mature REST + gRPC** — multiple client options (Python qdrant-client library, HTTP curl, gRPC tools)
5. **Docker-friendly** — official image, zero configuration needed

**Alternatives considered (deferred):**
- **Chroma:** simpler API, but less mature than Qdrant
- **FAISS:** high-performance for huge scale, but in-memory only (requires external persistence layer)
- **Weaviate:** production-grade, but heavier setup (requires more resources)
- **Pinecone:** fully managed, but requires API key + internet connection (not suitable for local dev)

Future: abstract `vector_db/` layer to swap backends without rewriting ingestion/RAG code.

## Getting Started

### Start the Database

From project root:
```bash
bash scripts/start_qdrant.sh
```

Verify it's running:
```bash
curl http://localhost:6333/health
# Expected: {"status":"ok"}
```

### Web Dashboard

Visit `http://localhost:6333/dashboard` in a browser to:
- View collections and statistics
- Inspect stored vectors and metadata
- Run manual queries (debug/exploration)

### Stop the Database

```bash
docker stop medical-ingestion-qdrant
```

Or let it persist across restarts (default `unless-stopped` policy).

### Clean Up

```bash
docker rm medical-ingestion-qdrant
docker volume rm medical-ingestion_qdrant_storage  # if you want to delete stored data
```

## Integration Checklist

- [x] `vector_db/base.py` — abstract `VectorStore` interface (`upsert_one`, `find_by_hash`)
- [x] `vector_db/qdrant.py` — `QdrantVectorStore` implementation (collection management, `upsert_one`, `find_by_hash`)
- [x] Wired: `scripts/ingest_documents.py::embed_and_store` → [Chunk Store](/doc/feature/chunk_store.md)`.sync_to_qdrant()` → `QdrantVectorStore.upsert_one()`
- [ ] Add retrieval API to `vector_db/qdrant.py` (used by RAG layer later)
- [x] `qdrant-client` in `pyproject.toml`
- [ ] Write integration tests (create collection → embed dummy chunks → search → verify ranking)

## Related Concepts

- [Embedder](/doc/feature/embedder.md) — produces vectors, cache-checked via [Chunk Store](/doc/feature/chunk_store.md) (upstream producer)
- [Chunk Store](/doc/feature/chunk_store.md) — Postgres provenance store; calls `upsert_one` only for hashes new to Qdrant
- [Postgres Storage](/doc/feature/postgres_storage.md) — relational side of the split; explains why pgvector was rejected in favor of keeping Qdrant
- [Chunker](/doc/feature/chunker.md) — produces Documents (data source for embedder)
- IMPLEMENTATION_PLAN.md: Infrastructure section, Vector DB layer, Architecture (settled: "pgvector rejected, Qdrant kept")

## Notes

- **Python package:** `qdrant-client` (in `pyproject.toml`), used by `vector_db/qdrant.py::QdrantVectorStore`.
- **Networking:** Container runs on `localhost:6333` (host network or bridge — compose file uses bridge). From host Python code, connect to `localhost:6333`.
- **Data persistence:** All ingested vectors survive container stop/restart. To reset, either delete the volume or use Qdrant's API (`DELETE /collections/{name}`).
