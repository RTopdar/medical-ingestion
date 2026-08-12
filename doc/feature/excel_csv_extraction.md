---
type: Module
title: Excel/CSV Extraction (reference script)
description: Standalone script demonstrating Unstructured-based CSV/Excel loading into raw LangChain Documents.
resource: ingestion/loaders/individual-scripts/excel_csv_extraction.py
tags: [ingestion, reference, standalone]
status: stable
---

# Excel/CSV Extraction

`ingestion/loaders/individual-scripts/excel_csv_extraction.py` (moved from `ingestion/excel_csv_extraction.py`). Standalone demo/reference script — returns raw `langchain_core.documents.Document`. Not wired into [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Functions

- `load_csv_documents(csv_dir="dummy_docs") -> list[Document]` — globs `*.csv`, loads via `UnstructuredLoader`.
- `load_excel_documents(excel_dir="dummy_docs") -> list[Document]` — globs `*.xlsx`, loads via `UnstructuredLoader`, handles multi-sheet workbooks.

Both tag metadata with `file`, `source_file`, `format` (a smaller metadata set than production — this script does not keep `UnstructuredLoader`'s full native metadata).

## Relation to production code

`ExcelCSVLoaderService` in [Loaders](/doc/feature/loaders.md) is now architecturally identical in output type (both return `langchain_core.documents.Document`, since the 2026-08-12 migration removed `ExcelCSVLoaderService`'s Pydantic wrapping) — the production version differs by doing text cleaning and preserving all of `UnstructuredLoader`'s native metadata (`dict(lc_doc.metadata)`) rather than the flat `file`/`source_file`/`format` tagging here.

Run directly: `python ingestion/loaders/individual-scripts/excel_csv_extraction.py` — prints first 3 elements from each format.
