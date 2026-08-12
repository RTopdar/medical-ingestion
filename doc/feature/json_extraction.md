---
type: Module
title: JSON Extraction (reference script)
description: Standalone script demonstrating JSON loading into raw LangChain Documents.
resource: ingestion/loaders/individual-scripts/json_extraction.py
tags: [ingestion, reference, standalone]
status: stable
---

# JSON Extraction

`ingestion/loaders/individual-scripts/json_extraction.py` (moved from `ingestion/json_extraction.py`). Standalone demo/reference script — returns raw `langchain_core.documents.Document`. Not wired into [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md).

## Function

`load_json_documents(json_dir="dummy_docs") -> list[Document]` — globs `*.json`, treats each top-level object (or each item of a top-level list) as one Document. Content pulled from `content`/`text`/`body`/`description`; remaining fields become flat metadata plus `file`, `source_file`, `format`.

## Relation to production code

`JSONLoaderService` in [Loaders](/doc/feature/loaders.md) is now architecturally identical in output type (both return `langchain_core.documents.Document`, since the 2026-08-12 migration removed `JSONLoaderService`'s Pydantic wrapping) — the production version differs only in doing nested metadata flattening (dot-notation) and domain-specific field extraction (patient info, clinical data, publication info, etc.) rather than the flat tagging here.

Run directly: `python ingestion/loaders/individual-scripts/json_extraction.py` — prints first 3 loaded elements.
