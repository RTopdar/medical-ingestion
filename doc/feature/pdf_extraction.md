---
type: Module
title: PDF Extraction (reference script)
description: Standalone script demonstrating Docling-based PDF loading into raw LangChain Documents.
resource: ingestion/loaders/individual-scripts/pdf_extraction.py
tags: [ingestion, reference, standalone]
status: stable
---

# PDF Extraction

`ingestion/loaders/individual-scripts/pdf_extraction.py` (moved from `ingestion/pdf_extraction.py`). Standalone demo/reference script — returns raw `langchain_core.documents.Document`. Not wired into [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Function

`load_pdf_documents(pdf_dir="dummy_docs") -> list[Document]` — globs `*.pdf`, loads via `DoclingLoader`, tags each doc's metadata with `file`, `source_file`, `format`.

## Relation to production code

`PDFLoaderService` in [Loaders](/doc/feature/loaders.md) is now architecturally identical in output type (both return `langchain_core.documents.Document`, since the 2026-08-12 migration removed `PDFLoaderService`'s Pydantic wrapping) — the production version differs only in doing text cleaning and richer Docling metadata extraction (page number, bbox, section headings) rather than the flat `file`/`source_file`/`format` tagging here.

Run directly: `python ingestion/loaders/individual-scripts/pdf_extraction.py` — prints first 3 loaded elements.
