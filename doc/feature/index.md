---
type: Bundle Index
title: medical-ingestion architecture
description: OKF bundle indexing the ingestion pipeline's modules, models, and pipeline scripts.
status: stable
---

# medical-ingestion — Architecture Bundle

OKF (Open Knowledge Format v0.2) bundle. Each file below is one concept document. Traverse via links, not by reading this repo's source tree directly, when answering "how does X work" questions.

## Concepts

- [Loaders](/doc/feature/loaders.md) — `ingestion/loaders/`, source-format ingestion package (PDF, text, Excel/CSV, JSON, SQL); every loader returns `langchain_core.documents.Document` directly (migrated 2026-08-12)
- [Chunker](/doc/feature/chunker.md) — `ingestion/chunker.py`, Document → Document (chunked) splitting via LangChain's native `split_documents()`
- [PDF Extraction](/doc/feature/pdf_extraction.md) — `ingestion/loaders/individual-scripts/pdf_extraction.py`, standalone Docling-based reference script
- [JSON Extraction](/doc/feature/json_extraction.md) — `ingestion/loaders/individual-scripts/json_extraction.py`, standalone LangChain-Document reference script
- [Excel/CSV Extraction](/doc/feature/excel_csv_extraction.md) — `ingestion/loaders/individual-scripts/excel_csv_extraction.py`, standalone reference script
- [PMC Fetcher](/doc/feature/pmc_fetcher.md) — `ingestion/loaders/individual-scripts/pmc_fetcher.py`, PubMed Central raw fetch
- [PMC JSON Converter](/doc/feature/pmc_json_converter.md) — `ingestion/loaders/individual-scripts/pmc_json_converter.py`, PMC → structured JSON for `JSONLoaderService`
- [Basic Document Ingestion](/doc/feature/basic_document_ingestion.md) — `ingestion/loaders/individual-scripts/basic_document_ingestion.py`, standalone reference script
- [ClinicalTrials Fetcher](/doc/feature/clinicaltrials_fetcher.md) — `ingestion/clinicaltrials_fetcher.py`, ClinicalTrials.gov API v2 fetch
- [SQL Loader (Storage Layer)](/doc/feature/sql_loader.md) — `storage/` (persistence: SQLModel-backed SQLite seed/query, two normalized tables, FK join, predicate-based query API) + `ingestion/loaders/sql_loader.py` (`SQLDataLoaderService`, converts joined rows to flat-metadata `Document`)
- [Embedder](/doc/feature/embedder.md) — `ingestion/embedder.py`, `Document` (chunked) → embedding vectors via OpenRouter `/embeddings`, cache-first
- [Embedding Cache](/doc/feature/embedding_cache.md) — `storage/embedding_cache.py`, raw-sqlite3 content-addressable `(model, text) -> vector` store backing the Embedder
- [Data Models](/doc/feature/models.md) — `models/documents.py` (stub — Document/Chunk/Metadata removed, superseded by `langchain_core.documents.Document`), `models/vectors.py`, `models/rag.py`, `models/clinical_trial.py`
- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — `scripts/ingest_documents.py`, full pipeline entry point

## Related

- [doc/index.md](/doc/index.md) — index of indexes for both `doc/` bundles
- [doc/bug/index.md](/doc/bug/index.md) — incident index (bug side of `doc/`)
- [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions (kept in sync by `doc-sync` agent)
