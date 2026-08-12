---
type: Module
title: Basic Document Ingestion (reference script)
description: Standalone script for loading and chunking plain-text files with raw LangChain splitters.
resource: ingestion/basic_document_ingestion.py
tags: [ingestion, reference, standalone]
status: stable
---

# Basic Document Ingestion

`ingestion/basic_document_ingestion.py`. Earliest reference script in the repo — works directly with `langchain_core.documents.Document` and `langchain_text_splitters`, no Pydantic models, no `models/` involvement.

## Functions

- `load_text_file(file_path) -> list[Document]` — reads one `.txt` file.
- `ingest_single_file(file_path, chunk_size=1000, chunk_overlap=300) -> list[Document]` — load + `RecursiveCharacterTextSplitter`.
- `ingest_from_directory(directory_path, chunk_size=1000, chunk_overlap=3) -> list[Document]` — recursive glob over `**/*.txt`, chunks each.
- `load_single_dummy_pubmed() -> list[Document]` — convenience wrapper hardcoded to `dummy_docs/pubmed/full_paper_diabetes.txt`, a file produced by [PMC Fetcher](/doc/feature/pmc_fetcher.md).

## Relation to production code

Superseded by [Loaders](/doc/feature/loaders.md)' `TextLoaderService` + [Chunker](/doc/feature/chunker.md)'s `ChunkerService` for actual pipeline use.

Run directly: `python ingestion/basic_document_ingestion.py` — chunks all files in `dummy_docs/pubmed`.
