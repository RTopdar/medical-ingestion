---
type: Module
title: Chunker
description: Splits Documents into Chunks for RAG using RecursiveCharacterTextSplitter.
resource: ingestion/chunker.py
tags: [ingestion, pydantic, rag]
status: stable
---

# Chunker

`ingestion/chunker.py`. Converts `models.documents.Document` into `models.documents.Chunk` list.

## Components

- `ChunkerConfig` — `chunk_size` and `chunk_overlap`, both default from `settings.py` (`settings.chunk_size`, `settings.chunk_overlap`), not hardcoded.
- `ChunkerService.chunk(documents)` — wraps `langchain_text_splitters.RecursiveCharacterTextSplitter`. Recomputes `start_idx`/`end_idx` against the original document content (`str.find`, walking forward from `char_pos` to avoid false matches on repeated substrings). Copies parent `Metadata` onto each chunk, appends `"chunk"` tag, adds `parent_title` to `extra`.

## Data flow

[Loaders](/doc/feature/loaders.md) → `Document` → `ChunkerService.chunk()` → `Chunk`.

## Callers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md)

## Note

`ChunkerConfig` has no `separators` field and there is no `RecursiveChunker` class — only `ChunkerService`. A caller using either will raise at construction/import time.
