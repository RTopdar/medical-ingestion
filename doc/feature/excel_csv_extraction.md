---
type: Module
title: Excel/CSV Extraction (reference script)
description: Standalone script demonstrating Unstructured-based CSV/Excel loading into raw LangChain Documents.
resource: ingestion/excel_csv_extraction.py
tags: [ingestion, reference, standalone]
status: stable
---

# Excel/CSV Extraction

`ingestion/excel_csv_extraction.py`. Standalone demo/reference script — returns raw `langchain_core.documents.Document`, not the Pydantic `models.documents.Document`. Not wired into [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Functions

- `load_csv_documents(csv_dir="dummy_docs") -> list[Document]` — globs `*.csv`, loads via `UnstructuredLoader`.
- `load_excel_documents(excel_dir="dummy_docs") -> list[Document]` — globs `*.xlsx`, loads via `UnstructuredLoader`, handles multi-sheet workbooks.

Both tag metadata with `file`, `source_file`, `format`.

## Relation to production code

Superseded by `ExcelCSVLoaderService` in [Loaders](/doc/feature/loaders.md) for actual pipeline use — that version adds Pydantic wrapping and text cleaning.

Run directly: `python ingestion/excel_csv_extraction.py` — prints first 3 elements from each format.
