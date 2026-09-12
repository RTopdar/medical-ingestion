"""Tests for pydantic-settings-backed Settings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pydantic import ValidationError

from settings import Settings


class TestSettingsDefaults:
    def test_default_instance_has_expected_defaults(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("CHAT_MODEL", raising=False)
        monkeypatch.delenv("GROQ_CHAT_MODEL", raising=False)
        monkeypatch.delenv("EMBEDDING_BATCH_SIZE", raising=False)
        monkeypatch.delenv("CHUNK_SIZE", raising=False)
        s = Settings(_env_file=None)
        assert s.openrouter_api_key == ""
        assert s.chat_model == "openrouter/meta-llama/llama-2-7b-chat"
        assert s.groq_chat_model == "groq/openai/gpt-oss-120b"
        assert s.embedding_batch_size == 100
        assert s.chunk_size == 512

    def test_env_var_overrides_field(self, monkeypatch):
        monkeypatch.setenv("CHAT_MODEL", "openrouter/some/other-model")
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test-key")
        s = Settings(_env_file=None)
        assert s.chat_model == "openrouter/some/other-model"
        assert s.groq_api_key == "gsk-test-key"

    def test_embedding_batch_size_must_be_positive(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "0")
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_validate_required_raises_without_openrouter_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        s = Settings(_env_file=None, openrouter_api_key="")
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY not set"):
            s.validate_required()

    def test_repr_does_not_leak_api_key(self, monkeypatch):
        s = Settings(_env_file=None, openrouter_api_key="secret-value-123")
        assert "secret-value-123" not in repr(s)
        assert "***" in repr(s)

    def test_str_does_not_leak_api_key(self, monkeypatch):
        s = Settings(_env_file=None, openrouter_api_key="secret-value-123")
        assert "secret-value-123" not in str(s)
        assert "secret-value-123" not in f"{s}"
        assert "***" in str(s)
