---
type: Module
title: PMC JSON Converter
description: Fetches PMC papers and writes them as structured JSON matching JSONLoaderService's expected schema.
resource: ingestion/loaders/individual-scripts/pmc_json_converter.py
tags: [ingestion, external-api, pubmed, json]
status: stable
---

# PMC JSON Converter

`ingestion/loaders/individual-scripts/pmc_json_converter.py` (moved from `ingestion/pmc_json_converter.py`). Production data-fetch path — same PMC E-utilities API as [PMC Fetcher](/doc/feature/pmc_fetcher.md), but outputs one structured JSON file instead of per-paper `.txt` files.

## Functions

- `search_pmc_papers(query, max_results=5) -> list[dict]` — PMC `esearch`.
- `fetch_pmc_full_text(pmcid) -> dict` — PMC `efetch` (XML). Extracts title, abstract, full text, authors (name/affiliation), publication date, keywords, journal, volume, issue, pages.
- `papers_to_json(papers, output_path) -> str` — maps each paper into the nested schema consumed by `JSONLoaderService` (see [Loaders](/doc/feature/loaders.md)): `id` (`PMC-{pmcid}`), `content` (abstract + full text), `source`, `publication_info`, `article_metadata`, `authors`, `research_data`, `tags`.
- `fetch_and_save_json(query="diabetes management", count=3) -> str` — orchestrates the full fetch, writes to `dummy_docs/pmc_documents.json`.

## CLI

`python ingestion/loaders/individual-scripts/pmc_json_converter.py "<query>" [count]`

## Data flow

PMC E-utilities API → `papers_to_json` → `dummy_docs/pmc_documents.json` → `JSONLoaderService.load()` → `Document` → [Chunker](/doc/feature/chunker.md).

See [INGESTION_GUIDE.md](/INGESTION_GUIDE.md) for the full worked example.
