---
type: Module
title: Chunker
description: Splits langchain_core.documents.Document into smaller Documents for RAG using RecursiveCharacterTextSplitter's native split_documents().
resource: ingestion/chunker.py
tags: [ingestion, rag]
status: stable
---

# Chunker

`ingestion/chunker.py`. Converts `list[langchain_core.documents.Document]` into a shorter, chunked `list[langchain_core.documents.Document]` — same type in and out (rewritten 2026-08-12; previously converted a Pydantic `Document` into a Pydantic `Chunk`, see [Data Models](/doc/feature/models.md)).

## Components

- `ChunkerConfig` — `chunk_size` and `chunk_overlap`, both default from `settings.py` (`settings.chunk_size`, `settings.chunk_overlap`), not hardcoded. Unchanged by the 2026-08-12 rewrite.
- `ChunkerService.chunk(documents)` — wraps `langchain_text_splitters.RecursiveCharacterTextSplitter(chunk_size=..., chunk_overlap=..., add_start_index=True)` and calls its native `split_documents(documents)` — one line. This splits `page_content`, propagates each source document's `metadata` dict onto every resulting chunk, and (via `add_start_index=True`) adds `metadata["start_index"]` itself. The previous manual `str.find()`-based `start_idx`/`end_idx` reconstruction and hand-copied `Metadata` are gone — LangChain's splitter now does both natively.

## Data flow

[Loaders](/doc/feature/loaders.md) → `Document` → `ChunkerService.chunk()` → `Document` (chunked, smaller `page_content`, `metadata["start_index"]` added).

## Callers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md)

## Note

`ChunkerConfig` has no `separators` field and there is no `RecursiveChunker` class — only `ChunkerService`. A caller using either will raise at construction/import time. (Still accurate after the 2026-08-12 rewrite — `ChunkerConfig` itself did not change, only `ChunkerService.chunk()`'s internals and its input/output type.)
