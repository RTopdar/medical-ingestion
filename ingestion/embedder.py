"""Embedding service backed by OpenRouter's /embeddings endpoint."""

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from models.vectors import Chunk
from settings import settings
from storage.chunk_store import ChunkStore
from storage.postgres import engine as default_engine


class EmbedderError(RuntimeError):
    """Raised when the OpenRouter embeddings request fails."""


class Embedder:
    """Generates text embeddings via OpenRouter, using Postgres (ChunkStore) as a
    read-only cache to skip repeat API calls. Does not persist embeddings itself —
    that's the ingest script's job (one Chunk row per occurrence, plus Qdrant sync)."""

    def __init__(
        self,
        model: str | None = None,
        batch_size: int | None = None,
        chunk_store: ChunkStore | None = None,
    ):
        self.model = model or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self.chunk_store = chunk_store or ChunkStore(default_engine)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            }
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts, using Postgres as a cache and batching API calls
        for cache misses to stay under the request size limit.

        Failed batches are logged to the DLQ (failed_embeddings table) for inspection
        and are NOT retried automatically in this call — the embedder will raise
        EmbedderError after retry exhaustion.

        Args:
            texts: Non-empty strings to embed.

        Returns:
            One embedding vector per input text, in the same order.

        Raises:
            EmbedderError: If a batch fails after all retries are exhausted.
        """
        hashes = [Chunk.make_content_hash(self.model, text) for text in texts]
        resolved: dict[str, list[float]] = {}
        for content_hash in set(hashes):
            cached = self.chunk_store.find_by_hash(content_hash)
            if cached is not None:
                resolved[content_hash] = cached

        miss_indices = [i for i, h in enumerate(hashes) if h not in resolved]
        for start in range(0, len(miss_indices), self.batch_size):
            batch_indices = miss_indices[start : start + self.batch_size]
            batch_texts = [texts[i] for i in batch_indices]
            batch_hashes = [hashes[i] for i in batch_indices]

            try:
                batch_vectors = self._embed_batch(batch_texts)
            except EmbedderError as e:
                for text, content_hash in zip(batch_texts, batch_hashes):
                    self.chunk_store.add_failed(text, str(e), self.model, content_hash)
                raise

            for content_hash, vector in zip(batch_hashes, batch_vectors):
                resolved[content_hash] = vector

        return [resolved[h] for h in hashes]

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

    def embed_with_hashes(self, texts: list[str]) -> tuple[list[list[float]], list[str]]:
        """Embed texts and return their content hashes alongside the vectors, so callers
        can build Chunk rows without recomputing keys."""
        hashes = [Chunk.make_content_hash(self.model, text) for text in texts]
        return self.embed(texts), hashes

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        resp = self._session.post(
            f"{settings.openrouter_base_url}/embeddings",
            json={"model": self.model, "input": batch},
            timeout=60,
        )
        if not resp.ok:
            raise EmbedderError(f"OpenRouter embeddings request failed ({resp.status_code}): {resp.text}")

        data = resp.json().get("data", [])
        if len(data) != len(batch):
            raise EmbedderError(f"Expected {len(batch)} embeddings, got {len(data)}")

        return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
