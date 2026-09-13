"""Cross-encoder reranker — OpenRouter /rerank endpoint, scores query+document pairs
jointly (unlike RRF's rank-only fusion in retrieval/hybrid.py), so it runs as a second
pass over the fused shortlist rather than replacing it.

litellm.rerank() has no OpenRouter provider (its custom_llm_provider literal omits
"openrouter" as of the installed version), so this stays on raw requests — with a
manual primary -> backup OpenRouter key fallback on 429, mirroring llm/chat_router.py.
"""

import requests

from settings import settings

OPENROUTER_RERANK_URL = "https://openrouter.ai/api/v1/rerank"


class Reranker:
    """Wraps OpenRouter's rerank endpoint for a set of already-fused candidates."""

    def __init__(self, model: str | None = None, timeout: int = 30):
        self.model = model or settings.reranker_model
        self.timeout = timeout
        self.session = requests.Session()

    def _post(self, api_key: str, payload: dict) -> requests.Response:
        return self.session.post(
            OPENROUTER_RERANK_URL,
            json=payload,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    def rerank(self, query: str, candidates: list[dict], top_n: int | None = None) -> list[dict]:
        """Rerank fused candidates (each carrying a `text` key) by relevance to `query`.

        Returns candidates in relevance order, each with a `relevance_score` key added.
        """
        if not candidates:
            return []

        documents = [c["text"] or "" for c in candidates]
        payload = {"model": self.model, "query": query, "documents": documents}
        if top_n is not None:
            payload["top_n"] = top_n

        resp = self._post(settings.openrouter_api_key, payload)
        if resp.status_code == 429 and settings.openrouter_backup_api_key:
            resp = self._post(settings.openrouter_backup_api_key, payload)
        if not resp.ok:
            raise RuntimeError(f"Rerank failed ({resp.status_code}): {resp.text}")

        results = resp.json().get("results", [])
        return [{**candidates[r["index"]], "relevance_score": r["relevance_score"]} for r in results]
