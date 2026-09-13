"""Tests for ChatRouterService."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import pytest

from llm.chat_router import ChatRouterService
from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams
from settings import Settings


def _fake_settings() -> Settings:
    return Settings(
        _env_file=None,
        openrouter_api_key="or-key",
        openrouter_backup_api_key="",
        openrouter_base_url="https://openrouter.ai/api/v1",
        chat_model="openrouter/meta-llama/llama-3-70b",
        groq_api_key="gsk-key",
        groq_chat_model="groq/llama-3.3-70b-versatile",
    )


class TestChatRouterServiceConstruction:
    def test_builds_router_with_correct_model_list_length(self):
        config = ChatRouterConfig(
            deployments=[
                LiteLLMDeployment(
                    model_name="primary",
                    litellm_params=LiteLLMModelParams(model="openrouter/x", api_key="k1"),
                ),
                LiteLLMDeployment(
                    model_name="fallback",
                    litellm_params=LiteLLMModelParams(model="groq/y", api_key="k2"),
                ),
            ],
            fallback_chain=["primary", "fallback", "primary"],
        )
        service = ChatRouterService(config)
        assert len(service._router.model_list) == 2

    def test_fallbacks_configured_from_chain(self):
        config = ChatRouterConfig(
            deployments=[
                LiteLLMDeployment(
                    model_name="primary",
                    litellm_params=LiteLLMModelParams(model="openrouter/x", api_key="k1"),
                ),
                LiteLLMDeployment(
                    model_name="fallback",
                    litellm_params=LiteLLMModelParams(model="groq/y", api_key="k2"),
                ),
            ],
            fallback_chain=["primary", "fallback", "primary"],
        )
        service = ChatRouterService(config)
        assert service._router.fallbacks == [{"primary": ["fallback", "primary"]}]


class TestChatRouterServiceFromSettings:
    def test_from_settings_builds_openrouter_groq_chain(self):
        service = ChatRouterService.from_settings(_fake_settings())
        assert service.config.fallback_chain == [
            "openrouter-primary",
            "groq-fallback",
        ]
        names = [d.model_name for d in service.config.deployments]
        assert names == ["openrouter-primary", "groq-fallback"]
        primary = service.config.deployments[0].litellm_params
        assert primary.model == "openrouter/meta-llama/llama-3-70b"  # matches settings.chat_model verbatim, no added prefix
        assert primary.api_key == "or-key"
        fallback = service.config.deployments[1].litellm_params
        assert fallback.model == "groq/llama-3.3-70b-versatile"
        assert fallback.api_key == "gsk-key"

    def test_from_settings_degrades_to_openrouter_only_without_groq_key(self):
        settings = _fake_settings()
        settings = settings.model_copy(update={"groq_api_key": ""})
        service = ChatRouterService.from_settings(settings)
        assert service.config.fallback_chain == ["openrouter-primary"]
        names = [d.model_name for d in service.config.deployments]
        assert names == ["openrouter-primary"]

    def test_from_settings_appends_openrouter_backup_when_key_set(self):
        settings = _fake_settings()
        settings = settings.model_copy(update={"openrouter_backup_api_key": "or-backup-key"})
        service = ChatRouterService.from_settings(settings)
        assert service.config.fallback_chain == [
            "openrouter-primary",
            "groq-fallback",
            "openrouter-backup",
        ]
        names = [d.model_name for d in service.config.deployments]
        assert names == ["openrouter-primary", "groq-fallback", "openrouter-backup"]
        backup = service.config.deployments[2].litellm_params
        assert backup.api_key == "or-backup-key"
        assert backup.model == "openrouter/meta-llama/llama-3-70b"


class TestChatRouterServiceCompletion:
    def test_complete_calls_router_completion_with_primary_model_name(self):
        service = ChatRouterService.from_settings(_fake_settings())
        with patch.object(service._router, "completion", return_value="ok") as mock_completion:
            result = service.complete([{"role": "user", "content": "hi"}])
        assert result == "ok"
        mock_completion.assert_called_once_with(
            model="openrouter-primary",
            messages=[{"role": "user", "content": "hi"}],
        )

    def test_stream_passes_stream_true(self):
        service = ChatRouterService.from_settings(_fake_settings())
        with patch.object(service._router, "completion", return_value=iter(["a", "b"])) as mock_completion:
            list(service.stream([{"role": "user", "content": "hi"}]))
        mock_completion.assert_called_once_with(
            model="openrouter-primary",
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )
