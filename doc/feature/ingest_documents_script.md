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

1. `ingest_json_documents(data_dir="dummy_docs")` — via `LoaderFactory.json_loader`, see [Loaders](/doc/feature/loaders.md).
2. `ingest_pdf_documents(data_dir="data/pdf")` — via `LoaderFactory.pdf_loader`. Tolerates `FileNotFoundError` (no PDFs present).
3. `ingest_csv_excel_documents(data_dir="data/csv")` — via `LoaderFactory.excel_csv_loader`. Tolerates `FileNotFoundError`.
4. `chunk_documents(documents)` — builds `ChunkerConfig(chunk_size=512, chunk_overlap=100)` and calls `ChunkerService(config=config).chunk(documents)`. See [Chunker](/doc/feature/chunker.md).
5. `main()` prints a summary: document count, chunk count, average chunk size.

## Run

```bash
source .venv/bin/activate
python scripts/ingest_documents.py
```

## History

Originally referenced a nonexistent `RecursiveChunker` class and a `separators` kwarg not present in `ChunkerConfig` — would have raised on import/construction. Fixed to use the real `ChunkerService`/`ChunkerConfig` API. Flagged by the `doc-sync` agent, fixed same session.
