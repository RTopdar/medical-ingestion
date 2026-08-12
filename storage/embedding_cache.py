"""SQLite content-addressable cache for embedding vectors — hash(model, text) -> vector.

Avoids re-paying OpenRouter for texts already embedded (duplicate chunks,
re-ingestion, retries). Uses raw sqlite3, not SQLModel — single key-value
table, no relations to model.

**Thread-safe concurrent access:** WAL mode enables multiple readers/writers
without lock contention. Each thread creates its own EmbeddingCache instance
(new sqlite3.connect call); they share the same db_path file. WAL handles
isolation and concurrent access safely.

**Cache lifecycle:** Unbounded growth in production. Future migration to
vector DB (hash as column, vector DB owns eviction via TTL/LRU) or
periodic VACUUM + size-cap logic recommended. See failed_embeddings for
persistent failures that may need eviction/retry logic separately.
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
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.isolation_level = None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                hash TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT,
                text TEXT NOT NULL,
                error TEXT NOT NULL,
                model TEXT NOT NULL,
                attempt_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def add_failed(self, text: str, error: str, model: str, text_hash: str | None = None) -> None:
        """Record a failed embedding attempt for later inspection/retry."""
        self._conn.execute(
            """
            INSERT INTO failed_embeddings (hash, text, error, model, attempt_count)
            VALUES (?, ?, ?, ?, 1)
            """,
            (text_hash, text, error, model),
        )
        self._conn.commit()

    def get_failed(self, limit: int = 100) -> list[dict]:
        """Fetch recent failed embeddings for inspection or retry."""
        rows = self._conn.execute(
            """
            SELECT id, hash, text, error, model, attempt_count, created_at
            FROM failed_embeddings
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "hash": row[1],
                "text": row[2],
                "error": row[3],
                "model": row[4],
                "attempt_count": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
