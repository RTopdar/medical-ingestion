"""Tests for llm/config.py pydantic router config models."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pydantic import ValidationError

from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams


class TestLiteLLMModelParams:
    def test_valid_params(self):
        p = LiteLLMModelParams(model="groq/llama-3.3-70b-versatile", api_key="gsk-test")
        assert p.model == "groq/llama-3.3-70b-versatile"
        assert p.temperature == 0.0
        assert p.timeout == 60

    def test_model_without_provider_prefix_rejected(self):
        with pytest.raises(ValidationError, match="provider-prefixed"):
            LiteLLMModelParams(model="llama-3.3-70b-versatile", api_key="gsk-test")

    def test_empty_api_key_rejected(self):
        with pytest.raises(ValidationError):
            LiteLLMModelParams(model="groq/llama-3.3-70b-versatile", api_key="")

    def test_temperature_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            LiteLLMModelParams(model="groq/llama-3.3-70b-versatile", api_key="k", temperature=3.0)

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            LiteLLMModelParams(model="groq/llama-3.3-70b-versatile", api_key="k", bogus_field=1)

    def test_non_positive_max_tokens_rejected(self):
        with pytest.raises(ValidationError):
            LiteLLMModelParams(model="groq/llama-3.3-70b-versatile", api_key="k", max_tokens=0)


class TestChatRouterConfig:
    def _deployment(self, name: str, model: str = "groq/llama-3.3-70b-versatile") -> LiteLLMDeployment:
        return LiteLLMDeployment(
            model_name=name,
            litellm_params=LiteLLMModelParams(model=model, api_key="k"),
        )

    def test_valid_config(self):
        cfg = ChatRouterConfig(
            deployments=[self._deployment("primary"), self._deployment("fallback")],
            fallback_chain=["primary", "fallback", "primary"],
        )
        assert cfg.fallback_chain == ["primary", "fallback", "primary"]

    def test_fallback_chain_referencing_unknown_deployment_rejected(self):
        with pytest.raises(ValidationError, match="unknown model_name"):
            ChatRouterConfig(
                deployments=[self._deployment("primary")],
                fallback_chain=["primary", "nonexistent"],
            )

    def test_single_deployment_chain_accepted(self):
        """A 1-element chain is valid — e.g. Groq unavailable, OpenRouter-only."""
        cfg = ChatRouterConfig(
            deployments=[self._deployment("primary")],
            fallback_chain=["primary"],
        )
        assert cfg.fallback_chain == ["primary"]

    def test_empty_fallback_chain_rejected(self):
        with pytest.raises(ValidationError):
            ChatRouterConfig(
                deployments=[self._deployment("primary")],
                fallback_chain=[],
            )

    def test_empty_deployments_rejected(self):
        with pytest.raises(ValidationError):
            ChatRouterConfig(deployments=[], fallback_chain=["primary", "fallback"])
