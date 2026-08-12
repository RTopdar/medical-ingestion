---
type: Module
title: PDF Extraction (reference script)
description: Standalone script demonstrating Docling-based PDF loading into raw LangChain Documents.
resource: ingestion/pdf_extraction.py
tags: [ingestion, reference, standalone]
status: stable
---

# PDF Extraction

`ingestion/pdf_extraction.py`. Standalone demo/reference script — returns raw `langchain_core.documents.Document`, not the Pydantic `models.documents.Document`. Not wired into [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Function

`load_pdf_documents(pdf_dir="dummy_docs") -> list[Document]` — globs `*.pdf`, loads via `DoclingLoader`, tags each doc's metadata with `file`, `source_file`, `format`.

## Relation to production code

Superseded by `PDFLoaderService` in [Loaders](/doc/feature/loaders.md) for actual pipeline use — that version adds Pydantic wrapping, text cleaning, and richer Docling metadata extraction (page number, bbox, section headings).

Run directly: `python ingestion/pdf_extraction.py` — prints first 3 loaded elements.
