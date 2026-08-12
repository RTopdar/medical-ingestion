"""Embedding service backed by OpenRouter's /embeddings endpoint."""

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

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
        keys = [self.cache.make_key(self.model, text) for text in texts]
        cached = self.cache.get_many(keys)

        miss_indices = [i for i, key in enumerate(keys) if key not in cached]
        for start in range(0, len(miss_indices), self.batch_size):
            batch_indices = miss_indices[start : start + self.batch_size]
            batch_texts = [texts[i] for i in batch_indices]
            batch_keys = [keys[i] for i in batch_indices]

            try:
                batch_vectors = self._embed_batch(batch_texts)
            except EmbedderError as e:
                for text, key in zip(batch_texts, batch_keys):
                    self.cache.add_failed(text, str(e), self.model, key)
                raise

            new_entries = {keys[i]: vector for i, vector in zip(batch_indices, batch_vectors)}
            self.cache.set_many(self.model, new_entries)
            cached.update(new_entries)

        return [cached[key] for key in keys]

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

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
