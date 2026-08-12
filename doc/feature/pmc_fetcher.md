---
type: Module
title: PMC Fetcher
description: Fetches full-text papers from PubMed Central and saves them as plain-text files.
resource: ingestion/loaders/individual-scripts/pmc_fetcher.py
tags: [ingestion, external-api, pubmed]
status: stable
---

# PMC Fetcher

`ingestion/loaders/individual-scripts/pmc_fetcher.py` (moved from `ingestion/pmc_fetcher.py`). Earlier/simpler sibling of [PMC JSON Converter](/doc/feature/pmc_json_converter.md) — outputs flat `.txt` files instead of structured JSON.

## Functions

- `search_pmc_papers(query, max_results=10) -> list[dict]` — PMC `esearch` via NCBI E-utilities, returns list of `{pmcid}`.
- `fetch_pmc_full_text(pmcid) -> dict` — PMC `efetch` (XML), parses title/abstract/full body text with `xml.etree.ElementTree`.
- `save_paper(paper, index) -> str` — writes to `dummy_docs/pubmed/{NN}_{sanitized_title}.txt` in a fixed `TITLE / PMC ID / ABSTRACT / FULL TEXT` text layout.
- `fetch_dummy_papers(query="medical research", count=6) -> list[str]` — orchestrates search → fetch → save, 0.5s sleep between requests for the 3 req/sec PubMed rate limit.

## API

`PMC_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"`. No auth required. See [Medical Data Sources strategy](/AGENTS.md) for the broader PubMed/PMC/ClinicalTrials.gov integration approach.

## CLI

`python ingestion/loaders/individual-scripts/pmc_fetcher.py "<query>" [count]`

## Consumers

Output `.txt` files can be read by `basic_document_ingestion.py::load_single_dummy_pubmed` — see [Basic Document Ingestion](/doc/feature/basic_document_ingestion.md).
