---
type: Module
title: Loaders
description: Pydantic-based document loaders for PDF, text, Excel/CSV, and JSON sources, organized as a package.
resource: ingestion/loaders/
tags: [ingestion, pydantic]
status: stable
---

# Loaders

`ingestion/loaders/`. Production loader stack — every loader here returns `models.documents.Document` (Pydantic), not raw LangChain `Document`. See [Data Models](/doc/feature/models.md).

Split from a single 439-line `loaders.py` into a package under [AGENTS.md](/AGENTS.md) rule #7 (500-line file cap) — kept as the reference pattern for future splits.

## Files

- `base.py` — `LoaderConfig` (shared: `source_dir`, `clean_text`) and `clean_text()` helper (shared by all loaders that clean extracted text).
- `pdf.py` — `PDFLoaderService`, wraps `DoclingLoader`. Extracts page number, bbox, char span, element type, section headings from Docling's `dl_meta`.
- `text.py` — `TextLoaderService`, plain `.txt` files, no chunking, recursive glob.
- `excel_csv.py` — `ExcelCSVLoaderService`, wraps `UnstructuredLoader` for `.csv` and `.xlsx`.
- `json_loader.py` — `JSONLoaderService`, loads `.json` files (single object or array). Extracts content from `content`/`text`/`body`/`description` fields; flattens nested metadata to dot-notation (`_flatten_metadata`); auto-extracts domain fields when present (`patient_info`, `clinical_data`, `provider`, `surgical_data`, `publication_info`, `authors`, `article_metadata`, `research_data`, `source`).
- `factory.py` — `LoaderFactory`, static constructors: `pdf_loader`, `text_loader`, `excel_csv_loader`, `json_loader`.
- `__init__.py` — re-exports everything above, so `from ingestion.loaders import LoaderFactory` (and any other symbol) works exactly as it did when this was one file. Callers never needed to change.

## Consumers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) calls `LoaderFactory.json_loader` / `pdf_loader` / `excel_csv_loader`.
- Output feeds [Chunker](/doc/feature/chunker.md).

## Related standalone scripts (not part of this class hierarchy)

- [PDF Extraction](/doc/feature/pdf_extraction.md)
- [JSON Extraction](/doc/feature/json_extraction.md)
- [Excel/CSV Extraction](/doc/feature/excel_csv_extraction.md)
