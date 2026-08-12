"""Embedding service backed by OpenRouter's /embeddings endpoint."""

import requests

from settings import settings
from storage.embedding_cache import EmbeddingCache


class EmbedderError(RuntimeError):
    """Raised when the OpenRouter embeddings request fails."""


class Embedder:
    """Generates text embeddings via OpenRouter, with a sqlite cache to skip repeat API calls."""

    def __init__(
        self,
        model: str | None = None,
        batch_size: int | None = None,
        cache: EmbeddingCache | None = None,
    ):
        self.model = model or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self.cache = cache or EmbeddingCache(settings.embedding_cache_db_path)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            }
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts, using the cache where possible and batching API calls
        for cache misses to stay under the request size limit.

        Args:
            texts: Non-empty strings to embed.

        Returns:
            One embedding vector per input text, in the same order.
        """
        keys = [self.cache.make_key(self.model, text) for text in texts]
        cached = self.cache.get_many(keys)

        miss_indices = [i for i, key in enumerate(keys) if key not in cached]
        for start in range(0, len(miss_indices), self.batch_size):
            batch_indices = miss_indices[start : start + self.batch_size]
            batch_texts = [texts[i] for i in batch_indices]
            batch_vectors = self._embed_batch(batch_texts)

            new_entries = {keys[i]: vector for i, vector in zip(batch_indices, batch_vectors)}
            self.cache.set_many(self.model, new_entries)
            cached.update(new_entries)

        return [cached[key] for key in keys]

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

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
