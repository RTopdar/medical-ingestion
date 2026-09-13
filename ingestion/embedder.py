"""Embedding service backed by litellm's OpenRouter embeddings support, with a
primary -> backup OpenRouter key fallback chain (mirrors llm/chat_router.py)."""

from litellm import Router
from litellm.exceptions import RateLimitError
from langchain_core.embeddings import Embeddings
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from llm.chat_router import _openrouter_wire_model_id
from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams
from models.vectors import Chunk
from settings import settings
from storage.chunk_store import ChunkStore
from storage.postgres import engine as default_engine


class EmbedderError(RuntimeError):
    """Raised when the OpenRouter embeddings request fails."""


def _build_embedding_router(model: str) -> tuple[Router, str]:
    """Primary -> backup OpenRouter key chain, same shape as ChatRouterService.
    Returns the Router and the fallback_chain[0] model_name to call with."""
    wire_model = _openrouter_wire_model_id(f"openrouter/{model}")
    deployments = [
        LiteLLMDeployment(
            model_name="embedding-primary",
            litellm_params=LiteLLMModelParams(
                model=wire_model,
                api_key=settings.openrouter_api_key,
                api_base=settings.openrouter_base_url,
            ),
            model_info={"cooldown_time": 0},
        ),
    ]
    fallback_chain = ["embedding-primary"]
    if settings.openrouter_backup_api_key:
        deployments.append(
            LiteLLMDeployment(
                model_name="embedding-backup",
                litellm_params=LiteLLMModelParams(
                    model=wire_model,
                    api_key=settings.openrouter_backup_api_key,
                    api_base=settings.openrouter_base_url,
                ),
                model_info={"cooldown_time": 0},
            ),
        )
        fallback_chain.append("embedding-backup")

    config = ChatRouterConfig(deployments=deployments, fallback_chain=fallback_chain)
    fallback_tail = config.fallback_chain[1:]
    fallbacks = [{config.fallback_chain[0]: fallback_tail}] if fallback_tail else []
    router = Router(
        model_list=[d.model_dump() for d in config.deployments],
        fallbacks=fallbacks,
        num_retries=0,
    )
    return router, config.fallback_chain[0]


class Embedder(Embeddings):
    """Generates text embeddings via OpenRouter (through litellm), using Postgres
    (ChunkStore) as a read-only cache to skip repeat API calls. Does not persist
    embeddings itself — that's the ingest script's job (one Chunk row per
    occurrence, plus Qdrant sync).

    Implements langchain_core.embeddings.Embeddings so this same instance can be
    wrapped by ragas.embeddings.LangchainEmbeddingsWrapper for eval scoring
    (eval/ragas_adapters.py), without a second embeddings implementation."""

    def __init__(
        self,
        model: str | None = None,
        batch_size: int | None = None,
        chunk_store: ChunkStore | None = None,
    ):
        self.model = model or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self.chunk_store = chunk_store or ChunkStore(default_engine)
        self._router, self._router_model_name = _build_embedding_router(self.model)

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

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """langchain_core.embeddings.Embeddings interface method, for ragas/LangChain callers."""
        return self.embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """langchain_core.embeddings.Embeddings interface method, for ragas/LangChain callers."""
        return self.embed_one(text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # A 429 needs the router's primary->backup fallback, not a same-key retry —
        # retrying the exhausted key would just burn the retry budget for nothing.
        retry=retry_if_not_exception_type(RateLimitError),
        reraise=True,
    )
    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            resp = self._router.embedding(model=self._router_model_name, input=batch)
        except Exception as e:
            raise EmbedderError(f"OpenRouter embeddings request failed: {e}") from e

        data = resp.data
        if len(data) != len(batch):
            raise EmbedderError(f"Expected {len(batch)} embeddings, got {len(data)}")

        return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
