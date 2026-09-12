"""ChatRouterService — single reusable wrapper around litellm.Router for the
OpenRouter -> Groq -> OpenRouter chat fallback chain. Used by both
retrieval/search.py (answer generation) and eval/ragas_adapters.py (RAGAS
judge) so the chain is defined exactly once.

Groq is an optional fallback: when GROQ_API_KEY is unset, from_settings()
builds a 1-element chain (OpenRouter only) rather than failing to construct."""

import logging
from typing import Iterator

from litellm import Router

from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams
from settings import Settings

logger = logging.getLogger(__name__)


class ChatRouterService:
    """Owns one litellm Router built from a validated ChatRouterConfig."""

    def __init__(self, config: ChatRouterConfig):
        self.config = config
        fallback_tail = config.fallback_chain[1:]
        fallbacks = [{config.fallback_chain[0]: fallback_tail}] if fallback_tail else []
        self._router = Router(
            model_list=[d.model_dump() for d in config.deployments],
            fallbacks=fallbacks,
            num_retries=0,
        )

    def complete(self, messages: list[dict], **kwargs):
        return self._router.completion(
            model=self.config.fallback_chain[0], messages=messages, **kwargs
        )

    def stream(self, messages: list[dict], **kwargs) -> Iterator:
        return self._router.completion(
            model=self.config.fallback_chain[0], messages=messages, stream=True, **kwargs
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "ChatRouterService":
        """Standard OpenRouter -> Groq -> OpenRouter chain built from Settings.
        Groq is optional: if settings.groq_api_key is unset, degrades to an
        OpenRouter-only chain rather than failing to construct."""
        deployments = [
            LiteLLMDeployment(
                model_name="openrouter-primary",
                litellm_params=LiteLLMModelParams(
                    model=settings.chat_model,
                    api_key=settings.openrouter_api_key,
                    api_base=settings.openrouter_base_url,
                ),
            ),
        ]
        if settings.groq_api_key:
            deployments.append(
                LiteLLMDeployment(
                    model_name="groq-fallback",
                    litellm_params=LiteLLMModelParams(
                        model=settings.groq_chat_model,
                        api_key=settings.groq_api_key,
                    ),
                ),
            )
            fallback_chain = ["openrouter-primary", "groq-fallback", "openrouter-primary"]
        else:
            logger.warning(
                "GROQ_API_KEY not set — chat fallback chain degraded to OpenRouter-only"
            )
            fallback_chain = ["openrouter-primary"]

        config = ChatRouterConfig(deployments=deployments, fallback_chain=fallback_chain)
        return cls(config)
