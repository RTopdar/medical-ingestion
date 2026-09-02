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
- `ChunkerService._split_by_markdown_headers(text)` — (added 2026-09-02 Task 3) detects and pre-splits markdown-formatted text before chunking. Extracts hierarchical section structure using `MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")])` and builds both `metadata["section_path"]` (ordered list of heading texts, e.g., `["Introduction", "Background", "Clinical Context"]`) and `metadata["section"]` (flattened string display format "H1 > H2 > H3") from the splitter's metadata dict. Both fields coexist: `section_path` is structured (for retrieval/reranking filters), `section` is readable (for injection into chunks and display).
- `ChunkerService.chunk(documents)` — wraps `langchain_text_splitters.RecursiveCharacterTextSplitter(chunk_size=..., chunk_overlap=..., add_start_index=True)` and calls its native `split_documents(documents)` — one line. This splits `page_content`, propagates each source document's `metadata` dict onto every resulting chunk, and (via `add_start_index=True`) adds `metadata["start_index"]` itself. For each input document, first checks `_has_markdown_headers()` — if present, pre-splits via `_split_by_markdown_headers()` and merges source metadata with header-extracted section metadata before chunking; otherwise chunks directly. The previous manual `str.find()`-based `start_idx`/`end_idx` reconstruction and hand-copied `Metadata` are gone — LangChain's splitter now does both natively.

## Data flow

[Loaders](/doc/feature/loaders.md) → `Document` (with optional markdown headers, optional `section` field) → `ChunkerService.chunk()` → `Document` (chunked, smaller `page_content`, `metadata["start_index"]` added, `metadata["section_path"]` + `metadata["section"]` set if markdown headers detected or present from loader).

Markdown headers flow: Text with `# H1` / `## H2` / `### H3` → `_split_by_markdown_headers()` → pre-splits into sections with `section_path` (list) + `section` (string) → merged with source metadata → `RecursiveCharacterTextSplitter` chunks each pre-split section → final chunks carry both section metadata fields + RecursiveCharacterTextSplitter's `start_index`.

## Callers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md)

## Note

`ChunkerConfig` has no `separators` field and there is no `RecursiveChunker` class — only `ChunkerService`. A caller using either will raise at construction/import time. (Still accurate after the 2026-08-12 rewrite — `ChunkerConfig` itself did not change, only `ChunkerService.chunk()`'s internals and its input/output type.)
