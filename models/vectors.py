import hashlib
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class IngestedDocument(SQLModel, table=True):
    """Whole-document dedup gate — skip re-ingesting an already-seen document."""

    __tablename__ = "documents"

    content_hash: str = Field(
        primary_key=True, description="sha256 of whole normalized document content"
    )
    source: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def make_content_hash(content: str) -> str:
        normalized = re.sub(r"\s+", " ", content.strip())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class Chunk(SQLModel, table=True):
    """One row per chunk occurrence — same content_hash can repeat across many
    rows (different document/patient/source), each carrying its own metadata.
    embedding is stored here purely for cache-hit lookup; Qdrant is the only
    similarity-search backend and holds one point per unique content_hash."""

    __tablename__ = "chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_hash: str = Field(
        index=True,
        description="sha256(model:normalized_text) — not unique, many rows may share a hash",
    )
    text: str = Field(description="Chunk page_content, verbatim")
    model: str = Field(description="Embedding model used")
    embedding: list[float] = Field(
        sa_column=Column(JSON), description="Cache-hit lookup only, not searched"
    )
    metadata_: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
        description="source, source_type, patient_mrn, document_id, ...",
    )
    section_path: Optional[list[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Hierarchical section path (e.g., ['Introduction', 'Background']), null if no heading structure available",
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number from PDF metadata, null if not available",
    )
    document_content_hash: Optional[str] = Field(default=None, foreign_key="documents.content_hash")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def make_content_hash(model: str, text: str) -> str:
        """Deterministic cache key: sha256 of model + whitespace-normalized text."""
        normalized = re.sub(r"\s+", " ", text.strip())
        payload = f"{model}:{normalized}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class FailedEmbedding(SQLModel, table=True):
    """DLQ for embedding attempts that failed after retry exhaustion."""

    __tablename__ = "failed_embeddings"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_hash: Optional[str] = Field(default=None)
    text: str
    error: str
    model: str
    attempt_count: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmbeddingRequest(BaseModel):
    text: str = PydanticField(..., description="Text to embed")
    model: Optional[str] = None


class EmbeddingResult(BaseModel):
    text: str
    embedding: list[float]
    model: str
    dimension: int
