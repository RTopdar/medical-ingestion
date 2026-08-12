"""Inspect the clinical trials SQLite DB from the terminal — counts, sample rows, join preview,
and the exact Document (page_content + metadata) each row turns into for the chunker."""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ingestion.loaders.sql_loader import SQLDataLoaderService
from settings import settings
from storage.sql import SQLLoaderService


def print_table(headers: list[str], rows: list[tuple], max_col_width: int = 40) -> None:
    """Print a simple fixed-width table."""
    widths = [len(h) for h in headers]
    str_rows = [[str(cell)[:max_col_width] for cell in row] for row in rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in str_rows:
        print(fmt_row(row))


def print_counts(title: str, counter: Counter) -> None:
    print(f"\n{title}")
    for value, count in counter.most_common():
        bar = "#" * count
        print(f"  {str(value):25s} {count:3d} {bar}")


def main(db_path: str = settings.sqlite_db_path, sample_size: int = 10):
    loader = SQLLoaderService(db_path)

    trials = loader.query()
    print("=" * 70)
    print(f"CLINICAL TRIALS DB — {db_path}")
    print("=" * 70)
    print(f"Total trials: {len(trials)}")

    if not trials:
        print("No data. Run scripts/seed_clinical_trials_db.py first.")
        return

    print_counts("By status", Counter(t.status for t in trials))
    print_counts("By phase", Counter(t.phase or "UNSPECIFIED" for t in trials))
    print_counts(
        "By condition",
        Counter((t.condition or "UNSPECIFIED").split(",")[0].strip() for t in trials),
    )

    print(f"\nSample rows (up to {sample_size}, joined with eligibility):")
    joined = loader.query_with_eligibility()[:sample_size]
    headers = ["nct_id", "title", "status", "phase", "sex", "min_age", "max_age"]
    rows = [
        (
            t.nct_id,
            t.title,
            t.status,
            t.phase or "-",
            e.sex if e else "-",
            e.minimum_age if e else "-",
            e.maximum_age if e else "-",
        )
        for t, e in joined
    ]
    print_table(headers, rows)

    print(
        f"\nEnrollment: min={min((t.enrollment_count or 0) for t in trials)}, "
        f"max={max((t.enrollment_count or 0) for t in trials)}, "
        f"avg={sum((t.enrollment_count or 0) for t in trials) // len(trials)}"
    )

    print_document_preview(db_path)


def print_document_preview(db_path: str, count: int = 1) -> None:
    """Show exactly what SQLDataLoaderService hands the chunker: page_content + flat metadata."""
    docs = SQLDataLoaderService(db_path=Path(db_path)).load()
    if not docs:
        return

    print("\n" + "=" * 70)
    print(f"DOCUMENT PREVIEW — what reaches the chunker (SQLDataLoaderService.load())")
    print("=" * 70)

    for doc in docs[:count]:
        print(f"\npage_content ({len(doc.page_content)} chars):")
        print("  " + doc.page_content.replace("\n", "\n  "))

        print(f"\nmetadata ({len(doc.metadata)} keys, all flat scalars):")
        key_width = max(len(k) for k in doc.metadata)
        for k, v in doc.metadata.items():
            print(f"  {k.ljust(key_width)} : {v!r}")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else settings.sqlite_db_path
    main(db_path)
