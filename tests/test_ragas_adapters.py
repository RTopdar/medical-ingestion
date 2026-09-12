"""Tests for eval/ragas_adapters.py::build_ragas_llm using ChatRouterService."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch

import eval.ragas_adapters as ragas_adapters

# `ragas.llms.LangchainLLMWrapper` is a `DeprecationHelper` proxy instance, not
# a class, so `isinstance(x, ragas.llms.LangchainLLMWrapper)` can never succeed
# (see ragas/llms/__init__.py). Import the real class it wraps instead.
from ragas.llms.base import LangchainLLMWrapper


class TestBuildRagasLLM:
    def test_returns_langchain_llm_wrapper(self):
        llm = ragas_adapters.build_ragas_llm()
        assert isinstance(llm, LangchainLLMWrapper)

    def test_uses_chat_router_service_from_settings(self):
        with patch("eval.ragas_adapters.ChatRouterService.from_settings") as mock_from_settings:
            mock_from_settings.return_value.config.fallback_chain = ["openrouter-primary", "groq-fallback", "openrouter-primary"]
            ragas_adapters.build_ragas_llm()
            mock_from_settings.assert_called_once()

    def test_model_override_is_applied_to_openrouter_leg(self):
        llm = ragas_adapters.build_ragas_llm(model="some/override-model")
        primary_deployment = llm.langchain_llm.router.model_list[0]
        assert primary_deployment["litellm_params"]["model"] == "openrouter/some/override-model"

    def test_bare_ragas_judge_model_setting_is_prefixed(self):
        with patch.object(
            ragas_adapters.settings, "ragas_judge_model", "bare/judge-model"
        ):
            llm = ragas_adapters.build_ragas_llm()
        primary_deployment = llm.langchain_llm.router.model_list[0]
        assert primary_deployment["litellm_params"]["model"] == "openrouter/bare/judge-model"
