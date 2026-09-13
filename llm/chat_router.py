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

_OPENROUTER_PREFIX = "openrouter/"


def _openrouter_wire_model_id(chat_model: str) -> str:
    """Return a litellm model id that, after litellm strips the provider prefix,
    is sent to OpenRouter intact.

    litellm strips the leading 'openrouter/' from the model it sends on the wire.
    That is correct for real model ids (e.g. 'openrouter/meta-llama/x' -> 'meta-llama/x'),
    but OpenRouter's special root-level aliases ('openrouter/free', 'openrouter/auto')
    must be sent in full form — a bare 'free' 404s with "No endpoints available for
    openrouter/free". Double-prefix only those aliases so litellm sends the full id."""
    if chat_model.startswith(_OPENROUTER_PREFIX):
        remainder = chat_model[len(_OPENROUTER_PREFIX):]
        if "/" not in remainder:
            return _OPENROUTER_PREFIX + chat_model
    return chat_model


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
                    model=_openrouter_wire_model_id(settings.chat_model),
                    api_key=settings.openrouter_api_key,
                    api_base=settings.openrouter_base_url,
                ),
                # litellm cooldowns a deployment for 5s out of the box on a 404
                # (its "non-retryable" class). OpenRouter's "free" alias returns
                # that 404 transiently (no free endpoint for the key at that
                # instant), and a hard cooldown makes the primary *statically
                # unavailable* to the next request — a regression vs. the old
                # stateless direct call. cooldown_time=0 keeps the deployment
                # immediately available so failures are per-call, like before.
                model_info={"cooldown_time": 0},
            ),
        ]
        if settings.groq_api_key:
            deployments.append(
                LiteLLMDeployment(
                    model_name="groq-fallback",
                    litellm_params=LiteLLMModelParams(
                        model=settings.groq_chat_model,
                        api_key=settings.groq_api_key,
                        # Groq's default TPM for this model is very low (8k).
                        # Cap output tokens so a burst of fallback calls doesn't
                        # exhaust the minute budget after 1-2 requests.
                        max_tokens=1024,
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
