"""SQLite content-addressable cache for embedding vectors — hash(model, text) -> vector.

Avoids re-paying OpenRouter for texts already embedded (duplicate chunks,
re-ingestion, retries). Uses raw sqlite3, not SQLModel — single key-value
table, no relations to model.
"""

import hashlib
import json
import re
import sqlite3
from pathlib import Path


class EmbeddingCache:
    """Content-addressable store mapping (model, text) -> embedding vector."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                hash TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def make_key(model: str, text: str) -> str:
        """
        Deterministic cache key: sha256 of model + whitespace-normalized text.

        Normalization (strip + collapse internal whitespace) applies only to
        the key, not the text passed to the embedding API — chunks that
        differ solely in spacing/newlines hit the same cache entry, but
        stored/embedded text is never altered.
        """
        normalized = re.sub(r"\s+", " ", text.strip())
        payload = f"{model}:{normalized}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get_many(self, keys: list[str]) -> dict[str, list[float]]:
        """Fetch cached embeddings for the given keys. Missing keys are absent from the result."""
        if not keys:
            return {}
        placeholders = ",".join("?" for _ in keys)
        rows = self._conn.execute(
            f"SELECT hash, embedding FROM embedding_cache WHERE hash IN ({placeholders})",
            keys,
        ).fetchall()
        return {key: json.loads(embedding) for key, embedding in rows}

    def set_many(self, model: str, items: dict[str, list[float]]) -> None:
        """Store embeddings for the given cache keys."""
        if not items:
            return
        self._conn.executemany(
            "INSERT OR REPLACE INTO embedding_cache (hash, model, embedding) VALUES (?, ?, ?)",
            [(key, model, json.dumps(vector)) for key, vector in items.items()],
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
