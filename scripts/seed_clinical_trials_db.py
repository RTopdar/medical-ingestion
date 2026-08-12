#!/usr/bin/env python3
"""Fetch dummy trial data from ClinicalTrials.gov and seed the SQLite DB."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.clinicaltrials_fetcher import fetch_dummy_trials
from settings import settings
from storage.sql import SQLLoaderService

CONDITIONS = ["diabetes", "cancer", "hypertension", "asthma", "alzheimer"]


def main(count_per_condition: int = 20):
    loader = SQLLoaderService(settings.sqlite_db_path)

    total = 0
    for condition in CONDITIONS:
        trials, eligibility_records = fetch_dummy_trials(condition, count=count_per_condition)
        written = loader.seed(trials, eligibility_records)
        total += written
        print(f"  Seeded {written} trials for '{condition}'")

    print(f"\nDone. {total} rows written to {settings.sqlite_db_path}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(count_per_condition=count)
