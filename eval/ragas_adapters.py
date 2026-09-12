"""Wires RAGAS's judge LLM and embeddings onto this repo's existing OpenRouter
stack — no new API provider or credential, just LangChain-shaped wrappers
ragas expects around ChatRouterService (chat, via ChatLiteLLMRouter) and
Embedder (embeddings).
"""

import sys
import types

# --- Upstream ragas bug workaround -----------------------------------------
# ragas>=0.3.x unconditionally imports langchain_community.chat_models.vertexai
# at package import time (ragas/llms/base.py), purely to add ChatVertexAI/VertexAI
# to an internal list of "known LangChain LLM classes that support the legacy
# .generate() batch API". That submodule only exists if the optional
# langchain-google-vertexai package is installed, which langchain_community does
# not declare as a real dependency — so `import ragas` crashes with
# ModuleNotFoundError on a clean install, even though nothing in this repo uses
# (or will ever call) VertexAI. Confirmed on ragas 0.3.9 through 0.4.3.
# Stub the submodule before importing ragas so its import succeeds; the stub
# class is never instantiated since ChatOpenRouter is used exclusively here.
# Remove this block once upstream ragas fixes the unconditional import.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _vertexai_stub = types.ModuleType("langchain_community.chat_models.vertexai")

    class _StubChatVertexAI:
        """Placeholder — never instantiated. See workaround comment above."""

    _vertexai_stub.ChatVertexAI = _StubChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _vertexai_stub
# -----------------------------------------------------------------------------

from langchain_litellm import ChatLiteLLMRouter
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper

from ingestion.embedder import Embedder
from llm.chat_router import ChatRouterService
from settings import settings


def build_ragas_llm(model: str | None = None) -> LangchainLLMWrapper:
    """Wrap ChatRouterService (OpenRouter->Groq->OpenRouter fallback) as the
    RAGAS judge LLM. `model` overrides the OpenRouter leg only — defaults to
    settings.ragas_judge_model, falling back to settings.chat_model."""
    openrouter_model = model and f"openrouter/{model}"
    override_settings = settings.model_copy(
        update={"chat_model": openrouter_model or settings.ragas_judge_model or settings.chat_model}
    )
    service = ChatRouterService.from_settings(override_settings)
    chat = ChatLiteLLMRouter(router=service._router, model=service.config.fallback_chain[0])
    return LangchainLLMWrapper(chat)


def build_ragas_embeddings() -> LangchainEmbeddingsWrapper:
    """Wrap the same Embedder used by ingestion (Postgres-cached OpenRouter embeddings)
    as the RAGAS judge embeddings — one embeddings implementation, no duplication."""
    return LangchainEmbeddingsWrapper(Embedder())
