from pathlib import Path

from pydantic import BaseModel
from langchain_core.documents import Document

from models.clinical_trial import ClinicalTrial, Eligibility
from storage.sql import SQLLoaderService


class SQLDataLoaderService(BaseModel):
    """Load clinical trial records from SQLite with fully flattened metadata.

    Wraps storage.SQLLoaderService (persistence/query) and converts the
    joined ClinicalTrial + Eligibility rows into LangChain Documents — every
    field kept as its own scalar metadata key (no nested dicts), for maximum
    metadata preservation before chunking.
    """

    db_path: Path

    class Config:
        arbitrary_types_allowed = True

    def load(self, *predicates) -> list[Document]:
        """
        Load trials (joined with eligibility) as Documents with flat metadata.

        Args:
            *predicates: SQLModel column expressions on ClinicalTrial, e.g. ClinicalTrial.status == "RECRUITING"

        Returns:
            List of Documents, metadata fully flattened (scalar values only)
        """
        store = SQLLoaderService(self.db_path)
        documents = []

        for trial, eligibility in store.query_with_eligibility(*predicates):
            content_parts = [trial.title, trial.summary or ""]
            if eligibility:
                content_parts.append(
                    f"Eligibility: sex={eligibility.sex}, "
                    f"age={eligibility.minimum_age}-{eligibility.maximum_age}, "
                    f"healthy_volunteers={eligibility.healthy_volunteers}"
                )
            content = "\n\n".join(part for part in content_parts if part)

            metadata = self._flatten_metadata(trial, eligibility)
            metadata["source"] = f"sqlite:{self.db_path}"
            metadata["source_type"] = "db"
            metadata["title"] = trial.title
            metadata["tags"] = [trial.status] + ([trial.phase] if trial.phase else [])

            documents.append(Document(page_content=content, metadata=metadata))
        return documents

    @staticmethod
    def _flatten_metadata(trial: ClinicalTrial, eligibility: Eligibility | None) -> dict:
        """Flatten trial + eligibility fields into a single scalar dict (no nesting)."""
        metadata = trial.model_dump(exclude={"title"})

        if eligibility:
            for key, value in eligibility.model_dump(exclude={"nct_id"}).items():
                metadata[f"eligibility_{key}"] = value

        return {k: v for k, v in metadata.items() if v is not None}
