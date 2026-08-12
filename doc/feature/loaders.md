---
type: Module
title: Loaders
description: Document loaders for PDF, text, Excel/CSV, JSON, and SQL sources, organized as a package. Loader classes are Pydantic BaseModels (config); every .load() returns langchain_core.documents.Document directly.
resource: ingestion/loaders/
tags: [ingestion, langchain]
status: stable
---

# Loaders

`ingestion/loaders/`. Production loader stack. Loader classes themselves are still Pydantic `BaseModel`s (config/validation), but every `.load()` returns `list[langchain_core.documents.Document]` directly (migrated 2026-08-12 from a Pydantic `models.documents.Document` wrapper — see [Data Models](/doc/feature/models.md)). Content lives in `doc.page_content` (not `.content`); metadata is a plain dict accessed via `doc.metadata["key"]` (not `.metadata.extra["key"]`).

Split from a single 439-line `loaders.py` into a package under [AGENTS.md](/AGENTS.md) rule #7 (500-line file cap) — kept as the reference pattern for future splits.

## Files

- `base.py` — `LoaderConfig` (shared: `source_dir`, `clean_text`) and `clean_text()` helper (shared by all loaders that clean extracted text). Unaffected by the Document-type migration.
- `pdf.py` — `PDFLoaderService`, wraps `DoclingLoader`. `DoclingLoader.load()` already returns LangChain Documents internally; the loader builds a metadata dict (`source`, `source_type`, `title`, `tags`, `page_number`, `element_type`, `section`, `bbox`, `char_span`, `content_layer`, parsed from Docling's `dl_meta`) and constructs `Document(page_content=content, metadata=metadata)` directly — same metadata extraction logic as before the migration, just no intermediate Pydantic wrapping.
- `text.py` — `TextLoaderService`, plain `.txt` files, no chunking, recursive glob. Builds a metadata dict (`source`, `source_type`, `title`, `tags`) directly — simplest of the five migrations.
- `excel_csv.py` — `ExcelCSVLoaderService`, wraps `UnstructuredLoader` for `.csv` and `.xlsx` via a shared `_load(file_path, source_type)` method (refactored from near-duplicate `_load_csv`/`_load_excel`). **Gained** metadata richness in the migration: `metadata = dict(lc_doc.metadata)` keeps ALL of Unstructured's native metadata, with `source`/`source_type`/`title`/`tags` added on top — previously the Pydantic wrapper kept only `extra["element_type"]` and discarded the rest.
- `json_loader.py` — `JSONLoaderService`, loads `.json` files (single object or array). Extracts content from `content`/`text`/`body`/`description` fields; flattens nested metadata to dot-notation (`_flatten_metadata`, unchanged static method); auto-extracts domain fields when present (`patient_info`, `clinical_data`, `provider`, `surgical_data`, `publication_info`, `authors`, `article_metadata`, `research_data`, `source`) — same extraction logic as before the migration, now building a flat metadata dict directly instead of populating a `Metadata.extra` dict.
- `sql_loader.py` — `SQLDataLoaderService`, wraps `storage.SQLLoaderService` and converts joined `(ClinicalTrial, Eligibility | None)` rows into Documents with fully flattened metadata. See [SQL Loader](/doc/feature/sql_loader.md) — this is a distinct concept doc since it also covers the `storage/` persistence layer it wraps.
- `factory.py` — `LoaderFactory`, static constructors: `pdf_loader`, `text_loader`, `excel_csv_loader`, `json_loader`, `sql_loader`.
- `__init__.py` — re-exports everything above, so `from ingestion.loaders import LoaderFactory` (and any other symbol) works exactly as it did when this was one file. Callers never needed to change import paths across either migration.

## Consumers

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) calls `LoaderFactory.json_loader` / `pdf_loader` / `excel_csv_loader`.
- Output feeds [Chunker](/doc/feature/chunker.md).

## Related standalone reference scripts (not part of this class hierarchy)

Live under `ingestion/loaders/individual-scripts/` (moved from `ingestion/` root; paths below reflect current location). Each already worked directly with `langchain_core.documents.Document` before the main loader migration, so the migration made the production loaders architecturally identical in output type to these, not the other way around.

- [PDF Extraction](/doc/feature/pdf_extraction.md)
- [JSON Extraction](/doc/feature/json_extraction.md)
- [Excel/CSV Extraction](/doc/feature/excel_csv_extraction.md)
- [Basic Document Ingestion](/doc/feature/basic_document_ingestion.md)
- [PMC Fetcher](/doc/feature/pmc_fetcher.md)
- [PMC JSON Converter](/doc/feature/pmc_json_converter.md)
- [ClinicalTrials Fetcher](/doc/feature/clinicaltrials_fetcher.md)
