---
type: Module
title: Ingest Pipeline Script
description: Entry-point script wiring loaders and chunker into one full ingestion run.
resource: scripts/ingest_documents.py
tags: [pipeline, entry-point]
status: stable
---

# Ingest Pipeline Script

`scripts/ingest_documents.py`. The pipeline entry point — the only script that combines all three production loaders with the chunker in one run.

## Flow

All documents are `langchain_core.documents.Document` throughout (loaders and chunker migrated 2026-08-12 — see [Loaders](/doc/feature/loaders.md), [Chunker](/doc/feature/chunker.md), [Data Models](/doc/feature/models.md)). The SQL path (`LoaderFactory.sql_loader`) is not yet included in this script's flow — see [SQL Loader](/doc/feature/sql_loader.md) Status.

1. `ingest_json_documents(data_dir="dummy_docs")` — via `LoaderFactory.json_loader`, see [Loaders](/doc/feature/loaders.md).
2. `ingest_pdf_documents(data_dir="data/pdf")` — via `LoaderFactory.pdf_loader`. Tolerates `FileNotFoundError` (no PDFs present).
3. `ingest_csv_excel_documents(data_dir="data/csv")` — via `LoaderFactory.excel_csv_loader`. Tolerates `FileNotFoundError`.
4. `chunk_documents(documents) -> list[Document]` — builds `ChunkerConfig(chunk_size=512, chunk_overlap=100)` and calls `ChunkerService(config=config).chunk(documents)`. See [Chunker](/doc/feature/chunker.md).
5. `main()` prints a summary: document count, chunk count, average chunk size (`sum(len(c.page_content) for c in chunks) // len(chunks)`).

## Import/attribute changes (2026-08-12 migration)

`Document` now imported from `langchain_core.documents` instead of `models.documents`. Print statements updated for the new type: no `doc.id` (LangChain `Document` has no required id field), `doc.metadata.get('title')` instead of `doc.title`, `doc.page_content` instead of `doc.content`, `doc.metadata` (plain dict) instead of `doc.metadata.extra`.

## Run

```bash
source .venv/bin/activate
python scripts/ingest_documents.py
```

## History

Originally referenced a nonexistent `RecursiveChunker` class and a `separators` kwarg not present in `ChunkerConfig` — would have raised on import/construction. Fixed to use the real `ChunkerService`/`ChunkerConfig` API. Flagged by the `doc-sync` agent, fixed same session.
