---
type: Bundle Index
title: medical-ingestion architecture
description: OKF bundle indexing the ingestion pipeline's modules, models, and pipeline scripts.
status: stable
---

# medical-ingestion — Architecture Bundle

OKF (Open Knowledge Format v0.2) bundle. Each file below is one concept document. Traverse via links, not by reading this repo's source tree directly, when answering "how does X work" questions.

## Concepts

- [Loaders](/doc/feature/loaders.md) — `ingestion/loaders.py`, source-format ingestion (PDF, Excel/CSV, JSON)
- [Chunker](/doc/feature/chunker.md) — `ingestion/chunker.py`, Document → Chunk splitting
- [PDF Extraction](/doc/feature/pdf_extraction.md) — `ingestion/pdf_extraction.py`, standalone Docling-based reference script
- [JSON Extraction](/doc/feature/json_extraction.md) — `ingestion/json_extraction.py`, standalone LangChain-Document reference script
- [Excel/CSV Extraction](/doc/feature/excel_csv_extraction.md) — `ingestion/excel_csv_extraction.py`, standalone reference script
- [PMC Fetcher](/doc/feature/pmc_fetcher.md) — `ingestion/pmc_fetcher.py`, PubMed Central raw fetch
- [PMC JSON Converter](/doc/feature/pmc_json_converter.md) — `ingestion/pmc_json_converter.py`, PMC → structured JSON for `JSONLoaderService`
- [Basic Document Ingestion](/doc/feature/basic_document_ingestion.md) — `ingestion/basic_document_ingestion.py`, standalone reference script
- [Data Models](/doc/feature/models.md) — `models/documents.py`, `models/vectors.py`, `models/rag.py`
- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — `scripts/ingest_documents.py`, full pipeline entry point

## Related

- [doc/index.md](/doc/index.md) — index of indexes for both `doc/` bundles
- [doc/bug/index.md](/doc/bug/index.md) — incident index (bug side of `doc/`)
- [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions (kept in sync by `doc-sync` agent)
