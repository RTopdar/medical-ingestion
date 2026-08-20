"""Postgres-backed repository for chunk provenance, embedding cache, document dedup, and DLQ.

Replaces storage/embedding_cache.py + storage/document_cache.py (sqlite). Postgres is the
sole embedding cache-check source (find_by_hash) and holds one row per chunk *occurrence*
(content_hash repeats across documents/patients). Qdrant stays the only similarity-search
backend and gets exactly one point per unique content_hash — sync_to_qdrant upserts only
hashes not already present there.
"""

from sqlalchemy import Engine
from sqlmodel import Session, select

from models.vectors import Chunk, FailedEmbedding, IngestedDocument
from vector_db.base import VectorStore


class ChunkStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def find_by_hash(self, content_hash: str) -> list[float] | None:
        """Cache-check: has this (model, text) been embedded before?"""
        with Session(self.engine) as session:
            row = session.exec(
                select(Chunk).where(Chunk.content_hash == content_hash).limit(1)
            ).first()
            return row.embedding if row else None

    def insert_chunks(self, rows: list[Chunk]) -> None:
        """Always insert one row per chunk occurrence, even on cache-hit, for provenance."""
        if not rows:
            return
        with Session(self.engine) as session:
            session.add_all(rows)
            session.commit()

    def sync_to_qdrant(self, rows: list[Chunk], qdrant_store: VectorStore) -> int:
        """Upsert to Qdrant only for content_hashes not already present there.
        Returns the number of new points written."""
        seen_hashes: set[str] = set()
        new_count = 0
        for row in rows:
            if row.content_hash in seen_hashes:
                continue
            seen_hashes.add(row.content_hash)
            if qdrant_store.find_by_hash(row.content_hash) is not None:
                continue
            qdrant_store.upsert_one(row.content_hash, row.embedding, row.metadata_, row.text)
            new_count += 1
        return new_count

    def add_failed(self, text: str, error: str, model: str, content_hash: str | None = None) -> None:
        with Session(self.engine) as session:
            session.add(FailedEmbedding(content_hash=content_hash, text=text, error=error, model=model))
            session.commit()

    def get_failed(self, limit: int = 100) -> list[FailedEmbedding]:
        with Session(self.engine) as session:
            statement = select(FailedEmbedding).order_by(FailedEmbedding.created_at.desc()).limit(limit)
            return list(session.exec(statement).all())

    def document_seen(self, content_hash: str) -> bool:
        with Session(self.engine) as session:
            row = session.get(IngestedDocument, content_hash)
            return row is not None

    def mark_document_seen(self, content_hash: str, source: str) -> None:
        with Session(self.engine) as session:
            if session.get(IngestedDocument, content_hash) is None:
                session.add(IngestedDocument(content_hash=content_hash, source=source))
                session.commit()
