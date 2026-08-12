"""SQLite persistence for clinical trial records — schema, seed, and query.

Normalized into two tables: `clinical_trials` (trial-level facts, from
identificationModule/statusModule/designModule) and `eligibility` (criteria,
1:1 via nct_id FK, from eligibilityModule) — mirrors the ClinicalTrials.gov
API's own module split rather than fabricating patient-level rows the API
never exposes.

Queries go through SQLModel (Session + select) so a future backend swap
(e.g. Postgres/pgvector) only touches the engine URL, not query code.
Table names come from settings.py via ClinicalTrial.__tablename__ /
Eligibility.__tablename__ — never hardcoded here.

This module only persists and queries rows (ClinicalTrial/Eligibility in,
ClinicalTrial/Eligibility out) — converting query results into `Document`
objects for the ingestion pipeline is `ingestion.loaders.sql_loader`'s job,
matching how every other source (PDF/Excel/JSON) separates loading from
storage.
"""

from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, col, create_engine, select

from models.clinical_trial import ClinicalTrial, Eligibility


class SQLLoaderService:
    """Persists and queries normalized ClinicalTrial/Eligibility records via SQLModel."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(f"sqlite:///{self.db_path}")
        SQLModel.metadata.create_all(self.engine)

    def seed(self, trials: list[ClinicalTrial], eligibility_records: list[Eligibility]) -> int:
        """
        Insert or replace trial + eligibility records.

        Args:
            trials: ClinicalTrial models to store
            eligibility_records: Eligibility models to store, 1:1 with trials by nct_id

        Returns:
            Number of trial rows written
        """
        with Session(self.engine) as session:
            for trial in trials:
                session.merge(trial)
            for eligibility in eligibility_records:
                session.merge(eligibility)
            session.commit()
        return len(trials)

    def query(self, *predicates) -> list[ClinicalTrial]:
        """
        Query trial records (trial-level only, no join).

        Args:
            *predicates: SQLModel column expressions, e.g. ClinicalTrial.status == "RECRUITING"

        Returns:
            List of ClinicalTrial models
        """
        with Session(self.engine) as session:
            statement = select(ClinicalTrial).where(*predicates)
            return list(session.exec(statement).all())

    def query_with_eligibility(self, *predicates) -> list[tuple[ClinicalTrial, Eligibility | None]]:
        """
        Query trials joined with their eligibility record.

        Args:
            *predicates: SQLModel column expressions on ClinicalTrial, e.g. ClinicalTrial.status == "RECRUITING"

        Returns:
            List of (ClinicalTrial, Eligibility | None) tuples
        """
        with Session(self.engine) as session:
            statement = (
                select(ClinicalTrial, Eligibility)
                .join(
                    Eligibility,
                    isouter=True,
                    onclause=col(Eligibility.nct_id) == col(ClinicalTrial.nct_id),
                )
                .where(*predicates)
            )
            return list(session.exec(statement).all())
