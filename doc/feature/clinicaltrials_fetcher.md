---
type: Module
title: ClinicalTrials Fetcher
description: Fetches structured trial records from the ClinicalTrials.gov API v2 and parses them into ClinicalTrial models.
resource: ingestion/clinicaltrials_fetcher.py
tags: [ingestion, external-api, clinicaltrials, storage]
status: stable
---

# ClinicalTrials Fetcher

`ingestion/clinicaltrials_fetcher.py`. Live — used by `scripts/seed_clinical_trials_db.py` — so it stays at the `ingestion/` root rather than moving into `ingestion/loaders/individual-scripts/` with the dead reference scripts. Same fetch/parse/CLI style as [PMC Fetcher](/doc/feature/pmc_fetcher.md), but hits ClinicalTrials.gov instead of PubMed, and returns [`ClinicalTrial`/`Eligibility`](/doc/feature/models.md) model instances directly instead of writing files — its output feeds [SQL Loader](/doc/feature/sql_loader.md) rather than the filesystem. Unaffected by the SQLModel migration in `storage/sql.py` and `models/clinical_trial.py`, and unaffected by the loaders' 2026-08-12 migration to `langchain_core.documents.Document` — `parse_trial()`/`parse_eligibility()` construct `ClinicalTrial`/`Eligibility` models the same way regardless of either change; those are ORM row models, not document/chunk data.

## Functions

- `search_trials(condition, max_results=20) -> list[dict]` — `GET /studies` with `query.cond=<condition>`, returns each study's raw `protocolSection` dict.
- `parse_trial(study) -> ClinicalTrial` — pulls `identificationModule`, `statusModule`, `conditionsModule`, `designModule`, `sponsorCollaboratorsModule`, `descriptionModule` out of `protocolSection` into a [`ClinicalTrial`](/doc/feature/models.md) model. Takes the first entry of `designModule.phases` as `phase`; joins `conditionsModule.conditions` into a comma-separated `condition` string; reads `designModule.enrollmentInfo.count` into `enrollment_count`.
- `parse_eligibility(study) -> Eligibility` — pulls `eligibilityModule` out of `protocolSection` into an [`Eligibility`](/doc/feature/models.md) model (`sex`, `minimumAge`, `maximumAge`, joined `stdAges`, `healthyVolunteers`, `studyPopulation`). 1:1 with the `ClinicalTrial` parsed from the same study, keyed by `nct_id`.
- `fetch_dummy_trials(condition="diabetes", count=20) -> tuple[list[ClinicalTrial], list[Eligibility]]` — orchestrates search → parse (both `parse_trial` and `parse_eligibility` per study), skipping and logging any study that fails to parse (e.g. missing `nctId`), 0.1s sleep between parses as rate-limit courtesy. Returns two parallel lists, 1:1 by `nct_id`. **Breaking change**: previously returned `list[ClinicalTrial]` only.

## API

`CTGOV_API = "https://clinicaltrials.gov/api/v2"`. No auth required. See [Medical Data Sources strategy](/AGENTS.md) and the `ClinicalTrials.gov API v2` entry in [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) Data Sources.

Tested live against the real API (not stubbed) — 50 trials (+ eligibility records) fetched and round-tripped through `seed`/`query`/`query_with_eligibility`/`load` successfully, against the SQLModel-based [SQL Loader](/doc/feature/sql_loader.md).

## CLI

`python ingestion/clinicaltrials_fetcher.py "<condition>" [count]`

## Consumers

- `scripts/seed_clinical_trials_db.py` calls `fetch_dummy_trials` for a fixed condition list (diabetes, cancer, hypertension, asthma, alzheimer) and passes both returned lists to `SQLLoaderService.seed(trials, eligibility_records)`. See [SQL Loader](/doc/feature/sql_loader.md).
