"""Postgres-backed repository for chunk provenance, embedding cache, document dedup, and DLQ.

Replaces storage/embedding_cache.py + storage/document_cache.py (sqlite). Postgres is the
sole embedding cache-check source (find_by_hash) and holds one row per chunk *occurrence*
(content_hash repeats across documents/patients). Qdrant stays the only similarity-search
backend and gets exactly one point per unique content_hash — sync_to_qdrant upserts only
hashes not already present there.
"""

from sqlalchemy import Engine, desc
from sqlmodel import Session, select

from models.vectors import Chunk, FailedEmbedding, IngestedDocument
from vector_db.base import VectorStore


class ChunkStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    def find_by_hash(self, content_hash: str) -> list[float] | None:
        """Cache-check: has this (model, text) been embedded before?"""
        with Session(self.engine) as session:
            chunk: Chunk | None = session.exec(
                select(Chunk).where(Chunk.content_hash == content_hash)
            ).first()
            return chunk.embedding if chunk else None

    def insert_chunks(self, rows: list[Chunk]) -> None:
        """Always insert one row per chunk occurrence, even on cache-hit, for provenance."""
        if not rows:
            return
        with Session(self.engine, expire_on_commit=False) as session:
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
            failed = FailedEmbedding(content_hash=content_hash, text=text, error=error, model=model)
            session.add(failed)
            session.commit()

    def get_failed(self, limit: int = 100) -> list[FailedEmbedding]:
        with Session(self.engine) as session:
            failed_list: list[FailedEmbedding] = list(session.exec(
                select(FailedEmbedding).order_by(desc(FailedEmbedding.created_at)).limit(limit)
            ).all())
            return failed_list

    def document_seen(self, content_hash: str) -> bool:
        with Session(self.engine) as session:
            doc: IngestedDocument | None = session.exec(
                select(IngestedDocument).where(IngestedDocument.content_hash == content_hash)
            ).first()
            return doc is not None

    def mark_document_seen(self, content_hash: str, source: str) -> None:
        with Session(self.engine) as session:
            doc: IngestedDocument | None = session.exec(
                select(IngestedDocument).where(IngestedDocument.content_hash == content_hash)
            ).first()
            if doc is None:
                new_doc = IngestedDocument(content_hash=content_hash, source=source)
                session.add(new_doc)
                session.commit()
