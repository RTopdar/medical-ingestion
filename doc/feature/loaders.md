---
type: Module
title: Loaders
description: Pydantic-based document loaders for PDF, text, Excel/CSV, and JSON sources.
resource: ingestion/loaders.py
tags: [ingestion, pydantic]
status: stable
---

# Loaders

`ingestion/loaders.py`. Production loader stack — every loader here returns `models.documents.Document` (Pydantic), not raw LangChain `Document`. See [Data Models](/doc/feature/models.md).

## Components

- `LoaderConfig` — shared config: `source_dir`, `clean_text`.
- `PDFLoaderService` — wraps `DoclingLoader`. Extracts page number, bbox, char span, element type, section headings from Docling's `dl_meta`.
- `TextLoaderService` — plain `.txt` files, no chunking, recursive glob.
- `ExcelCSVLoaderService` — wraps `UnstructuredLoader` for `.csv` and `.xlsx`.
- `JSONLoaderService` — loads `.json` files (single object or array). Extracts content from `content`/`text`/`body`/`description` fields; flattens nested metadata to dot-notation (`_flatten_metadata`); auto-extracts domain fields when present (`patient_info`, `clinical_data`, `provider`, `surgical_data`, `publication_info`, `authors`, `article_metadata`, `research_data`, `source`).
- `LoaderFactory` — static constructors: `pdf_loader`, `text_loader`, `excel_csv_loader`, `json_loader`.

## Consumers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) calls `LoaderFactory.json_loader` / `pdf_loader` / `excel_csv_loader`.
- Output feeds [Chunker](/doc/feature/chunker.md).

## Related standalone scripts (not part of this class hierarchy)

- [PDF Extraction](/doc/feature/pdf_extraction.md)
- [JSON Extraction](/doc/feature/json_extraction.md)
- [Excel/CSV Extraction](/doc/feature/excel_csv_extraction.md)
