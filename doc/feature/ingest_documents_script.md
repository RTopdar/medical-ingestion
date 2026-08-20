---
type: Module
title: Ingest Pipeline Script
description: Entry-point script wiring loaders and chunker into one full ingestion run.
resource: scripts/ingest_documents.py
tags: [pipeline, entry-point]
status: stable
---

# Ingest Pipeline Script

`scripts/ingest_documents.py`. The pipeline entry point — full run: load → chunk → embed → Postgres → Qdrant.

## Flow

All documents are `langchain_core.documents.Document` throughout (loaders and chunker migrated 2026-08-12 — see [Loaders](/doc/feature/loaders.md), [Chunker](/doc/feature/chunker.md), [Data Models](/doc/feature/models.md)). All progress and diagnostics are logged via [Structured Logging](/doc/feature/logging_config.md) (migrated from `print()` 2026-08-20). The SQL path (`LoaderFactory.sql_loader`) is not yet included in this script's flow — see [SQL Loader](/doc/feature/sql_loader.md) Status.

1. `ingest_json_documents(data_dir="dummy_docs")` / `ingest_pdf_documents` / `ingest_csv_excel_documents` — via `LoaderFactory`, see [Loaders](/doc/feature/loaders.md). Each tolerates `FileNotFoundError` (no files of that type present). Logs semantic events: `loading_*_documents` (entry), `loaded_*_documents` (success), `*_load_error` (failure with error context).
2. `init_db()` — [Postgres Storage](/doc/feature/postgres_storage.md), creates `chunks`/`failed_embeddings`/`documents` tables if missing.
3. `filter_seen_documents(documents, chunk_store)` — whole-document dedup via [Chunk Store](/doc/feature/chunk_store.md)`.document_seen()`/`.mark_document_seen()`. Logs `filtered_seen_documents` event with skip count. Surviving documents get their content_hash threaded into `metadata["document_id"]` for downstream chunk provenance (new field — no loader previously emitted this).
4. `chunk_documents(documents) -> list[Document]` — `ChunkerConfig(chunk_size=512, chunk_overlap=100)` + `ChunkerService.chunk()`. Logs `chunking_documents` (entry) and `chunked_documents` (completion with chunk count). See [Chunker](/doc/feature/chunker.md).
5. `embed_and_store(chunks)` — via [Embedder](/doc/feature/embedder.md)`.embed_with_hashes()`, builds one `Chunk` SQLModel row per chunk (content_hash, text, model, embedding, metadata_ including `document_id`). Logs: `embedding_chunks` (entry), `embedded_chunks` (completion with count + dimension), `storing_chunk_rows` (persist entry), `inserted_chunk_rows` (completion), `synced_qdrant` (completion with new_points + cache_hits). Before insert, **per-run dedup:** within the same ingestion run, drops any rows with identical `(content_hash, metadata)` pair (seen within this batch before), logs count skipped via `dropped_duplicate_rows`. Then calls `chunk_store.insert_chunks()` (batched ~100, one row per *unique* occurrence within this run) then `chunk_store.sync_to_qdrant()` (only new content_hashes, relative to Qdrant, get a point). See [Chunk Store](/doc/feature/chunk_store.md).
6. `main()` logs an `ingestion_summary` event at completion with document count, chunk count, and average chunk size.

## Import/attribute changes (2026-08-12 migration)

`Document` now imported from `langchain_core.documents` instead of `models.documents`. Print statements updated for the new type: no `doc.id` (LangChain `Document` has no required id field), `doc.metadata.get('title')` instead of `doc.title`, `doc.page_content` instead of `doc.content`, `doc.metadata` (plain dict) instead of `doc.metadata.extra`.

## Run

```bash
source .venv/bin/activate
bash scripts/start_postgres.sh   # Postgres for provenance/cache
bash scripts/start_qdrant.sh     # Qdrant for vector search
python scripts/ingest_documents.py
```

## History

- 2026-08-20: All `print()` statements migrated to structured logging via [Structured Logging](/doc/feature/logging_config.md). Every pipeline stage (load, chunk, embed, store, Qdrant sync) now emits semantic JSON events with context fields (counts, hashes, errors). Logs messages: document/chunk/embed counts, deduplication decisions, vector store sync results. See Flow section above for event names at each stage.
- Originally referenced a nonexistent `RecursiveChunker` class and a `separators` kwarg not present in `ChunkerConfig` — would have raised on import/construction. Fixed to use the real `ChunkerService`/`ChunkerConfig` API. Flagged by the `doc-sync` agent, fixed same session.
- Embed → store stage migrated from sqlite `EmbeddingCache`/`DocumentCache` to Postgres [Chunk Store](/doc/feature/chunk_store.md): `filter_seen_documents` and `embed_and_store` rewritten accordingly (see Flow above).

## Related

- [Chunk Store](/doc/feature/chunk_store.md), [Postgres Storage](/doc/feature/postgres_storage.md) — the persistence layer this script drives
- [Qdrant Infrastructure](/doc/feature/qdrant_infrastructure.md) — vector-search sync target
