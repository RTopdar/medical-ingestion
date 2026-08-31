"""Hybrid retriever — reciprocal rank fusion over Qdrant dense search + BM25 sparse search.

Both stores key results by content_hash (Qdrant payload, BM25 corpus entry), so fusion
needs no id-mapping: storage/chunk_store.py dedupes to the same unique-content_hash set
before writing to either store.
"""

from retrieval.bm25 import BM25Index
from vector_db.qdrant import QdrantVectorStore


class HybridRetriever:
    """Fuses dense + sparse rankings by reciprocal rank, not raw score — cosine similarity
    and BM25 score live on unrelated scales, so combining by rank avoids score calibration."""

    def __init__(self, qdrant_store: QdrantVectorStore, bm25_index: BM25Index, rrf_k: int = 60):
        self.qdrant_store = qdrant_store
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k

    def search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        fetch_k: int = 20,
    ) -> list[dict]:
        dense_hits = self.qdrant_store.search(query_vector=query_embedding, limit=fetch_k)
        sparse_hits = self.bm25_index.search(query, top_k=fetch_k)

        scores: dict[str, float] = {}
        entries: dict[str, dict] = {}

        for rank, hit in enumerate(dense_hits):
            content_hash = hit.payload["content_hash"]
            scores[content_hash] = scores.get(content_hash, 0.0) + 1 / (self.rrf_k + rank + 1)
            entries.setdefault(
                content_hash, {"text": hit.payload.get("text"), "metadata": hit.payload}
            )

        for rank, (entry, _score) in enumerate(sparse_hits):
            content_hash = entry["content_hash"]
            scores[content_hash] = scores.get(content_hash, 0.0) + 1 / (self.rrf_k + rank + 1)
            entries.setdefault(
                content_hash, {"text": entry["text"], "metadata": entry["metadata"]}
            )

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return [{"content_hash": h, "score": s, **entries[h]} for h, s in ranked]
