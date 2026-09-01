"""Search service — embed query, fuse dense+sparse via RRF, rerank with a cross-encoder,
then ground an LLM answer in the top chunks. This is the production search path;
scripts/*_demo.py are throwaway exploration scripts, not this module's caller.
"""

import re
import requests
from langchain_core.messages import HumanMessage
from langchain_openrouter import ChatOpenRouter

from retrieval.bm25 import BM25Index
from retrieval.hybrid import HybridRetriever
from retrieval.reranker import Reranker
from settings import settings
from vector_db.qdrant import QdrantVectorStore


def embed_query(text: str) -> list[float]:
    """Embed text via OpenRouter API."""
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
    )
    resp = session.post(
        f"{settings.openrouter_base_url}/embeddings",
        json={"model": settings.embedding_model, "input": [text]},
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"Embedding failed ({resp.status_code}): {resp.text}")
    data = resp.json().get("data", [])
    if not data:
        raise RuntimeError("No embedding returned")
    return data[0]["embedding"]


class SearchService:
    """Owns the full retrieval stack: BM25 + Qdrant + RRF fusion + cross-encoder rerank."""

    def __init__(self):
        self.bm25_index = BM25Index()
        self.bm25_index.load()
        self.retriever = HybridRetriever(QdrantVectorStore(), self.bm25_index)
        self.reranker = Reranker()
        self.last_results: list[dict] = []

    def search(self, query: str, top_k: int = 5, fetch_k: int = 20) -> list[dict]:
        """Fuse dense+sparse candidates, then rerank the fused shortlist for final order."""
        query_embedding = embed_query(query)
        fused = self.retriever.search(query, query_embedding, top_k=fetch_k, fetch_k=fetch_k)
        reranked = self.reranker.rerank(query, fused, top_n=top_k)
        self.last_results = self._enrich_with_citations(reranked)
        return self.last_results

    def _enrich_with_citations(self, results: list[dict]) -> list[dict]:
        """Layer 1: Add citation metadata to each result for downstream layers."""
        for i, result in enumerate(results):
            metadata = result.get("metadata", {})
            source = metadata.get("source", "Unknown")
            doc_id = metadata.get("document_id", "N/A")
            result["citation_index"] = i + 1
            result["citation"] = {"source": source, "document_id": doc_id, "rank": i}
        return results

    @staticmethod
    def extract_citations_from_answer(answer_text: str, num_results: int) -> list[int]:
        """Layer 5: Parse inline citations [1], [2], etc. from LLM answer.

        Returns list of citation indices found in answer (1-indexed, filtered to valid range).
        """
        pattern = r"\[(\d+)\]"
        matches = re.findall(pattern, answer_text)
        citations = [int(m) for m in matches if 1 <= int(m) <= num_results]
        return citations

    def answer(self, query: str, chunks: list[str], citations: list[dict] | None = None):
        """Stream an LLM answer grounded in the given chunks with citation markers.

        Layer 2: If citations provided, append source marker to each chunk text.
        Layer 4: Prompt instructs LLM to cite inline using chunk numbers.
        """
        context_parts = []
        for i, chunk in enumerate(chunks):
            marker = ""
            if citations and i < len(citations):
                source = citations[i].get("source", "Unknown")
                marker = f" [Source: {source}]"
            context_parts.append(f"[{i + 1}] {chunk}{marker}")

        context_str = "\n\n".join(context_parts)
        prompt = f"""You are a medical expert. Answer the following question based ONLY on the provided medical documents.

Question: {query}

Context from medical documents:
{context_str}

IMPORTANT: When citing information, include the source number in brackets like [1], [2], etc.
Provide a clear, concise answer based on the documents. If the answer is not in the documents, say so."""

        llm = ChatOpenRouter(model=settings.chat_model, temperature=0.7, streaming=True)
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            if chunk.content:
                yield chunk.content
