"""BM25 sparse lexical index over chunks — companion to Qdrant's dense index.

Rebuilt from scratch each ingestion run (see scripts/ingest_documents.py), over the full
deduped chunk corpus (one entry per unique content_hash, matching what Qdrant holds) —
bm25s has no incremental-add API, so a fresh corpus means a fresh index every time.
"""

from pathlib import Path

import bm25s

from models.vectors import Chunk
from settings import settings


class BM25Index:
    """Wraps bm25s.BM25 with a corpus of {content_hash, text, metadata} aligned to
    each indexed document, so search results carry back the same identity Qdrant uses."""

    def __init__(self, index_dir: str | Path | None = None):
        self.index_dir = Path(index_dir or settings.bm25_index_path)
        self.retriever = bm25s.BM25()
        self.corpus: list[dict] = []

    def build(self, chunks: list[Chunk]) -> None:
        """Index one entry per unique content_hash (first occurrence wins), mirroring
        how ChunkStore.sync_to_qdrant dedupes before writing to Qdrant."""
        seen: set[str] = set()
        unique_chunks = []
        for chunk in chunks:
            if chunk.content_hash in seen:
                continue
            seen.add(chunk.content_hash)
            unique_chunks.append(chunk)

        self.corpus = [
            {"content_hash": c.content_hash, "text": c.text, "metadata": c.metadata_}
            for c in unique_chunks
        ]
        tokens = bm25s.tokenize([c.text for c in unique_chunks], stopwords="en")
        self.retriever.index(tokens)

    def save(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.retriever.save(str(self.index_dir), corpus=self.corpus)

    def load(self) -> None:
        self.retriever = bm25s.BM25.load(str(self.index_dir), load_corpus=True)
        self.corpus = self.retriever.corpus

    def search(self, query: str, top_k: int = 5) -> list[tuple[dict, float]]:
        """Returns (corpus_entry, score) pairs, highest score first."""
        query_tokens = bm25s.tokenize(query, stopwords="en")
        results, scores = self.retriever.retrieve(query_tokens, corpus=self.corpus, k=top_k)
        return list(zip(results[0], scores[0]))
