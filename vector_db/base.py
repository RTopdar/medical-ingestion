"""Abstract vector store interface — Qdrant is the first/only implementation."""

from abc import ABC, abstractmethod


class VectorStore(ABC):
    """Stores one point per unique content_hash. Postgres (storage/chunk_store.py) owns
    per-occurrence provenance and calls upsert_one only for hashes new to this store."""

    @abstractmethod
    def upsert_one(
        self, content_hash: str, embedding: list[float], metadata: dict, text: str
    ) -> None:
        """Write a single point for a content_hash not already present in the store."""

    @abstractmethod
    def find_by_hash(self, content_hash: str) -> list[float] | None:
        """Look up an existing embedding by content hash. Returns None on miss."""
