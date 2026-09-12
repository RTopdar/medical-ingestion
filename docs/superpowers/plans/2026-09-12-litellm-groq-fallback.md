# LiteLLM + Groq Chat Fallback, and pydantic-settings Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 3-step chat-completions fallback chain (OpenRouter → Groq → OpenRouter) behind a single reusable, pydantic-validated service class, and convert `settings.py` to `pydantic-settings` with zero call-site changes.

**Architecture:** Two new modules under `llm/`: `llm/config.py` (strict pydantic models describing a litellm `Router` model list and an ordered fallback chain) and `llm/chat_router.py` (`ChatRouterService`, a thin wrapper around `litellm.Router` built from a validated `ChatRouterConfig`, with a `from_settings()` factory). `retrieval/search.py` and `eval/ragas_adapters.py` both replace their direct `ChatOpenRouter(...)` construction with `ChatRouterService.from_settings(settings)`. `settings.py` becomes a `pydantic_settings.BaseSettings` subclass — same field names, same env var names, same dot-access API, so none of the 13 existing importers change.

**Tech Stack:** `litellm` (Router + provider routing), `pydantic` v2 (`strict=True`, `extra="forbid"` on new config models), `pydantic-settings` (`BaseSettings`), existing `langchain-core` message types, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-12-litellm-groq-fallback-design.md`

## Global Constraints

- Embeddings (`ingestion/embedder.py`) and reranking (`retrieval/reranker.py`) are NOT touched — Groq has no embeddings/rerank API, they stay on direct OpenRouter HTTP calls.
- Fallback order is fixed: OpenRouter primary → Groq → OpenRouter again (not Groq-only, not 2-step).
- All new list/param structures passed into `litellm.Router` must go through strict pydantic models first — no raw dicts constructed ad hoc.
- `settings.py` conversion must not require any change to the 13 files that do `from settings import settings` / `import settings` — verified by running the existing test suite after the conversion.
- `litellm` and `pydantic-settings` are already added via `uv add litellm pydantic-settings` and verified import-clean (see spec's "Dependency Check" section) — do not re-add.
- Env var names for existing settings fields are unchanged (`CHAT_MODEL`, `OPENROUTER_API_KEY`, etc.) — only two new vars are introduced: `GROQ_API_KEY`, `GROQ_CHAT_MODEL`.

---

### Task 1: Convert `settings.py` to pydantic-settings

**Files:**
- Modify: `settings.py` (full rewrite)
- Test: `tests/test_settings.py` (new)

**Interfaces:**
- Produces: `settings.Settings` (a `pydantic_settings.BaseSettings` subclass) and the module-level `settings` instance, with all fields from the current class preserved by name and default, plus two new fields: `groq_api_key: str = ""`, `groq_chat_model: str = "groq/llama-3.3-70b-versatile"`. `Settings.validate_required(self) -> None` replaces the old dead `classmethod validate`.

- [ ] **Step 1: Write the failing test**

```python
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
        s = Settings(_env_file=None)
        assert s.openrouter_api_key == ""
        assert s.chat_model == "openrouter/meta-llama/llama-2-7b-chat"
        assert s.groq_chat_model == "groq/llama-3.3-70b-versatile"
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_settings.py -v`
Expected: FAIL — `ImportError` or `AttributeError` (current `Settings` is a plain class, `_env_file` kwarg doesn't exist, `validate_required` doesn't exist).

- [ ] **Step 3: Write minimal implementation**

Replace the full contents of `settings.py`:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment (shell priority > .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Models
    chat_model: str = "openrouter/meta-llama/llama-2-7b-chat"
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_batch_size: int = Field(default=100, gt=0)
    reranker_model: str = "nvidia/llama-nemotron-rerank-vl-1b-v2:free"
    ragas_judge_model: str | None = None

    # Groq (chat fallback provider)
    groq_api_key: str = ""
    groq_chat_model: str = "groq/llama-3.3-70b-versatile"

    # Vector DB
    vector_db_type: str = "qdrant"
    vector_db_path: str = "./data/chroma"
    qdrant_url: str = "http://localhost:6333"
    bm25_index_path: str = "./data/bm25_index"

    # Ingestion
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=100, ge=0)
    input_data_path: str = "./data/input"

    # Storage
    sqlite_db_path: str = "./data/medical.db"
    clinical_trials_table: str = "clinical_trials"
    eligibility_table: str = "eligibility"
    postgres_dsn: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/medical_ingestion"
    )

    # Logging
    log_level: str = "INFO"

    def validate_required(self) -> None:
        """Validate required settings."""
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set. Set via env var or .env file.")

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  openrouter_api_key={'***' if self.openrouter_api_key else 'NOT SET'}\n"
            f"  chat_model={self.chat_model}\n"
            f"  embedding_model={self.embedding_model}\n"
            f"  embedding_batch_size={self.embedding_batch_size}\n"
            f"  reranker_model={self.reranker_model}\n"
            f"  vector_db_type={self.vector_db_type}\n"
            f"  chunk_size={self.chunk_size}\n"
            f")"
        )


settings = Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_settings.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Run full existing test suite to confirm zero call-site breakage**

Run: `source .venv/bin/activate && pytest tests/ -v`
Expected: PASS — all pre-existing tests still pass unchanged, confirming the 13 files importing `settings` need no edits.

- [ ] **Step 6: Commit**

```bash
git add settings.py tests/test_settings.py
git commit -m "$(cat <<'EOF'
Convert settings.py to pydantic-settings

Adds typed validation for existing config plus new Groq fallback fields
(groq_api_key, groq_chat_model), with no call-site changes across the repo.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `llm/config.py` — strict pydantic router config models

**Files:**
- Create: `llm/__init__.py`
- Create: `llm/config.py`
- Test: `tests/test_llm_config.py`

**Interfaces:**
- Consumes: nothing (pure pydantic models, no dependency on Task 1 beyond type hints).
- Produces: `LiteLLMModelParams`, `LiteLLMDeployment`, `ChatRouterConfig` — all importable from `llm.config`, all with `model_config = ConfigDict(strict=True, extra="forbid")`.

- [ ] **Step 1: Write the failing test**

```python
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

    def test_fallback_chain_too_short_rejected(self):
        with pytest.raises(ValidationError):
            ChatRouterConfig(
                deployments=[self._deployment("primary")],
                fallback_chain=["primary"],
            )

    def test_empty_deployments_rejected(self):
        with pytest.raises(ValidationError):
            ChatRouterConfig(deployments=[], fallback_chain=["primary", "fallback"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_llm_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'llm'`

- [ ] **Step 3: Write minimal implementation**

`llm/__init__.py`:
```python
```
(empty — marks `llm/` as a package)

`llm/config.py`:
```python
"""Strict pydantic models describing a litellm Router configuration: the
model list (deployments) and the ordered fallback chain across them.
No raw dicts are handed to litellm.Router without passing through these
models first (see llm/chat_router.py::ChatRouterService)."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LiteLLMModelParams(BaseModel):
    """Per-deployment parameters passed to litellm as `litellm_params`."""

    model_config = ConfigDict(strict=True, extra="forbid")

    model: str
    api_key: str = Field(min_length=1)
    api_base: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    timeout: int = Field(default=60, gt=0)

    @field_validator("model")
    @classmethod
    def must_have_provider_prefix(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError(
                f"model must be provider-prefixed (e.g. 'groq/llama-3.3-70b'), got {v!r}"
            )
        return v


class LiteLLMDeployment(BaseModel):
    """One named entry in litellm Router's model_list."""

    model_config = ConfigDict(strict=True, extra="forbid")

    model_name: str = Field(min_length=1)
    litellm_params: LiteLLMModelParams


class ChatRouterConfig(BaseModel):
    """Ordered fallback chain over named deployments. fallback_chain[0] is the
    primary; each subsequent entry is tried after the previous one fails."""

    model_config = ConfigDict(strict=True, extra="forbid")

    deployments: list[LiteLLMDeployment] = Field(min_length=1)
    fallback_chain: list[str] = Field(min_length=2)

    @model_validator(mode="after")
    def chain_references_known_deployments(self) -> "ChatRouterConfig":
        known = {d.model_name for d in self.deployments}
        unknown = [name for name in self.fallback_chain if name not in known]
        if unknown:
            raise ValueError(f"fallback_chain references unknown model_name(s): {unknown}")
        return self
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_llm_config.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add llm/__init__.py llm/config.py tests/test_llm_config.py
git commit -m "$(cat <<'EOF'
Add strict pydantic config models for litellm Router

LiteLLMModelParams/LiteLLMDeployment/ChatRouterConfig validate the model
list and fallback chain before they reach litellm.Router.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `llm/chat_router.py` — `ChatRouterService`

**Files:**
- Create: `llm/chat_router.py`
- Test: `tests/test_chat_router.py`

**Interfaces:**
- Consumes: `llm.config.ChatRouterConfig`, `llm.config.LiteLLMDeployment`, `llm.config.LiteLLMModelParams` (Task 2); `settings.Settings` (Task 1, for the `from_settings` factory — takes a `Settings` instance, not the module-level singleton, so tests can pass a fake one).
- Produces: `ChatRouterService` with:
  - `__init__(self, config: ChatRouterConfig)`
  - `.complete(self, messages: list[dict], **kwargs) -> litellm.ModelResponse` (non-streaming)
  - `.stream(self, messages: list[dict], **kwargs) -> Iterator[...]` (streaming, `stream=True`)
  - `classmethod .from_settings(cls, settings: Settings) -> "ChatRouterService"` — builds the standard OpenRouter → Groq → OpenRouter chain

- [ ] **Step 1: Write the failing test**

```python
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
        openrouter_base_url="https://openrouter.ai/api/v1",
        chat_model="meta-llama/llama-3-70b",
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
    def test_from_settings_builds_openrouter_groq_openrouter_chain(self):
        service = ChatRouterService.from_settings(_fake_settings())
        assert service.config.fallback_chain == [
            "openrouter-primary",
            "groq-fallback",
            "openrouter-primary",
        ]
        names = [d.model_name for d in service.config.deployments]
        assert names == ["openrouter-primary", "groq-fallback"]
        primary = service.config.deployments[0].litellm_params
        assert primary.model == "openrouter/meta-llama/llama-3-70b"
        assert primary.api_key == "or-key"
        fallback = service.config.deployments[1].litellm_params
        assert fallback.model == "groq/llama-3.3-70b-versatile"
        assert fallback.api_key == "gsk-key"


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_chat_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'llm.chat_router'`

- [ ] **Step 3: Write minimal implementation**

`llm/chat_router.py`:
```python
"""ChatRouterService — single reusable wrapper around litellm.Router for the
OpenRouter -> Groq -> OpenRouter chat fallback chain. Used by both
retrieval/search.py (answer generation) and eval/ragas_adapters.py (RAGAS
judge) so the chain is defined exactly once."""

from typing import Iterator

from litellm import Router

from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams
from settings import Settings


class ChatRouterService:
    """Owns one litellm Router built from a validated ChatRouterConfig."""

    def __init__(self, config: ChatRouterConfig):
        self.config = config
        self._router = Router(
            model_list=[d.model_dump() for d in config.deployments],
            fallbacks=[{config.fallback_chain[0]: config.fallback_chain[1:]}],
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
        """Standard OpenRouter -> Groq -> OpenRouter chain built from Settings."""
        config = ChatRouterConfig(
            deployments=[
                LiteLLMDeployment(
                    model_name="openrouter-primary",
                    litellm_params=LiteLLMModelParams(
                        model=f"openrouter/{settings.chat_model}",
                        api_key=settings.openrouter_api_key,
                        api_base=settings.openrouter_base_url,
                    ),
                ),
                LiteLLMDeployment(
                    model_name="groq-fallback",
                    litellm_params=LiteLLMModelParams(
                        model=settings.groq_chat_model,
                        api_key=settings.groq_api_key,
                    ),
                ),
            ],
            fallback_chain=["openrouter-primary", "groq-fallback", "openrouter-primary"],
        )
        return cls(config)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_chat_router.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add llm/chat_router.py tests/test_chat_router.py
git commit -m "$(cat <<'EOF'
Add ChatRouterService wrapping litellm Router with OpenRouter->Groq->OpenRouter fallback

Single reusable service class for both answer generation and RAGAS judge
call sites, built from validated ChatRouterConfig.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Wire `ChatRouterService` into `retrieval/search.py`

**Files:**
- Modify: `retrieval/search.py:1-16` (imports), `retrieval/search.py:40-56` (`SearchService.__init__`), `retrieval/search.py:79-107` (`answer()`)
- Test: `tests/test_search_answer.py` (new)

**Interfaces:**
- Consumes: `llm.chat_router.ChatRouterService` (Task 3), `.stream(messages: list[dict]) -> Iterator`.
- Produces: `SearchService.answer()` keeps its exact current signature and streaming-string-generator behavior — no change visible to `eval/ragas_runner.py::collect_live_records`, which does `"".join(self.search_service.answer(...))`.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for SearchService.answer() using ChatRouterService instead of ChatOpenRouter directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

from retrieval.search import SearchService


class _FakeStreamChunk:
    def __init__(self, content: str):
        self.choices = [MagicMock(delta=MagicMock(content=content))]


class TestSearchServiceAnswer:
    def test_answer_streams_text_from_chat_router_service(self):
        service = SearchService.__new__(SearchService)  # bypass __init__ (needs live BM25/Qdrant)
        fake_router = MagicMock()
        fake_router.stream.return_value = iter(
            [_FakeStreamChunk("Hello "), _FakeStreamChunk("world")]
        )
        service.chat_router = fake_router

        chunks = list(service.answer("What is X?", ["some context chunk"], citations=[{"source": "doc1"}]))

        assert "".join(chunks) == "Hello world"
        fake_router.stream.assert_called_once()
        call_args = fake_router.stream.call_args
        messages = call_args.args[0] if call_args.args else call_args.kwargs["messages"]
        assert messages[0]["role"] == "user"
        assert "What is X?" in messages[0]["content"]
        assert "some context chunk" in messages[0]["content"]
        assert "[Source: doc1]" in messages[0]["content"]

    def test_answer_skips_empty_content_chunks(self):
        service = SearchService.__new__(SearchService)
        fake_router = MagicMock()
        fake_router.stream.return_value = iter(
            [_FakeStreamChunk(""), _FakeStreamChunk("only this")]
        )
        service.chat_router = fake_router

        chunks = list(service.answer("Q", ["ctx"]))

        assert chunks == ["only this"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_search_answer.py -v`
Expected: FAIL — `AttributeError: 'SearchService' object has no attribute 'chat_router'`

- [ ] **Step 3: Write minimal implementation**

Edit `retrieval/search.py` — replace the import block:

```python
import re
import requests

from llm.chat_router import ChatRouterService
from retrieval.bm25 import BM25Index
from retrieval.hybrid import HybridRetriever
from retrieval.reranker import Reranker
from settings import settings
from vector_db.qdrant import QdrantVectorStore
```

(drop `from langchain_core.messages import HumanMessage` and `from langchain_openrouter import ChatOpenRouter` — no longer used)

In `SearchService.__init__`, add the router as an instance attribute:

```python
    def __init__(self):
        self.bm25_index = BM25Index()
        self.bm25_index.load()
        self.retriever = HybridRetriever(QdrantVectorStore(), self.bm25_index)
        self.reranker = Reranker()
        self.chat_router = ChatRouterService.from_settings(settings)
        self.last_results: list[dict] = []
```

Replace the tail of `answer()`:

```python
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

        for chunk in self.chat_router.stream([{"role": "user", "content": prompt}], temperature=0.7):
            content = chunk.choices[0].delta.content
            if content:
                yield content
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_search_answer.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `source .venv/bin/activate && pytest tests/ -v`
Expected: PASS — all tests pass (this task doesn't touch `SearchService.search()` or citation extraction logic).

- [ ] **Step 6: Commit**

```bash
git add retrieval/search.py tests/test_search_answer.py
git commit -m "$(cat <<'EOF'
Route SearchService.answer() through ChatRouterService

Replaces direct ChatOpenRouter construction with the shared
OpenRouter->Groq->OpenRouter fallback chain. Streaming behavior and
public answer() signature are unchanged.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Wire `ChatRouterService` into `eval/ragas_adapters.py`

**Files:**
- Modify: `eval/ragas_adapters.py:31-47` (imports and `build_ragas_llm`)
- Test: `tests/test_ragas_adapters.py` (new)

**Interfaces:**
- Consumes: `llm.chat_router.ChatRouterService` (Task 3).
- Produces: `build_ragas_llm(model: str | None = None) -> LangchainLLMWrapper` — same signature and return type as before; ragas continues to receive a `LangchainLLMWrapper`, now wrapping a LangChain-compatible adapter over `ChatRouterService` instead of `ChatOpenRouter` directly.

Note: `LangchainLLMWrapper` expects a LangChain `BaseChatModel`. `litellm` ships `langchain_litellm.ChatLiteLLMRouter` (a `BaseChatModel` subclass that wraps a `litellm.Router` instance) for exactly this. This task uses that adapter rather than hand-rolling a `BaseChatModel` subclass.

- [ ] **Step 1: `langchain-litellm` dependency — already verified**

`langchain-litellm` was installed and its `ChatLiteLLMRouter` shape confirmed live during plan finalization:

```
$ python -c "from langchain_litellm import ChatLiteLLMRouter; import inspect; print(inspect.signature(ChatLiteLLMRouter.__init__))"
(self, *, router: Any, **kwargs: Any) -> None
```

Confirmed pydantic fields include `router` and `model` (NOT `litellm_router`/`model_name` as originally guessed). Confirmed working construction:

```python
from litellm import Router
from langchain_litellm import ChatLiteLLMRouter

model_list = [{"model_name": "primary", "litellm_params": {"model": "groq/llama-3.3-70b-versatile", "api_key": "fake-key"}}]
router = Router(model_list=model_list, fallbacks=[{"primary": ["primary"]}], num_retries=0)
chat = ChatLiteLLMRouter(router=router, model="primary")
assert chat.model == "primary"  # constructs cleanly
```

`langchain-core` was bumped 1.5.4 → 1.6.3 as a transitive dependency of `langchain-litellm` — already applied via `uv add langchain-litellm`, no further action needed here. Use `router=` and `model=` (not `litellm_params=`/`model_name=`) in Step 4 below.

- [ ] **Step 2: Write the failing test**

```python
"""Tests for eval/ragas_adapters.py::build_ragas_llm using ChatRouterService."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch

import eval.ragas_adapters as ragas_adapters
from ragas.llms import LangchainLLMWrapper


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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_ragas_adapters.py -v`
Expected: FAIL — `build_ragas_llm` still constructs `ChatOpenRouter` directly, `ChatRouterService` not imported in `eval/ragas_adapters.py`.

- [ ] **Step 4: Write minimal implementation**

Edit `eval/ragas_adapters.py` — replace the `build_ragas_llm` function and its imports:

```python
from langchain_litellm import ChatLiteLLMRouter  # confirmed available in Step 1
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper

from ingestion.embedder import Embedder
from llm.chat_router import ChatRouterService
from settings import settings


def build_ragas_llm(model: str | None = None) -> LangchainLLMWrapper:
    """Wrap ChatRouterService (OpenRouter->Groq->OpenRouter fallback) as the
    RAGAS judge LLM. `model` overrides the OpenRouter leg's model only —
    defaults to settings.ragas_judge_model, falling back to settings.chat_model."""
    override_settings = settings.model_copy(
        update={"chat_model": model or settings.ragas_judge_model or settings.chat_model}
    )
    service = ChatRouterService.from_settings(override_settings)
    chat = ChatLiteLLMRouter(router=service._router, model=service.config.fallback_chain[0])
    return LangchainLLMWrapper(chat)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_ragas_adapters.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/ -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add eval/ragas_adapters.py tests/test_ragas_adapters.py pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
Route RAGAS judge LLM through ChatRouterService

build_ragas_llm now wraps the same OpenRouter->Groq->OpenRouter fallback
chain used by answer generation, via ChatLiteLLMRouter, instead of
constructing ChatOpenRouter directly.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: `.env.example`, smoke test, cleanup, doc-sync, and push

**Files:**
- Modify: `.env.example`
- Delete: `docs/superpowers/specs/2026-09-12-litellm-groq-fallback-design.md`, `docs/superpowers/plans/2026-09-12-litellm-groq-fallback.md` (per explicit user instruction: remove the working design docs once implementation is done)
- No new test — this task is glue + verification + docs + git.

- [ ] **Step 1: Set `GROQ_CHAT_MODEL` in `.env.example`**

`.env.example` already has a `# Groq Config` block with `GROQ_API_KEY` (a real key for local dev use only — do not touch or overwrite that line) and a placeholder `GROQ_CHAT_MODEL=your-backup-model`. Read the current tail first:

Run: `tail -6 .env.example`

Replace only the placeholder value, leaving `GROQ_API_KEY` untouched:
```
GROQ_CHAT_MODEL=groq/llama-3.3-70b-versatile
```

Also confirm `settings.py`'s `groq_chat_model` field default (Task 1) matches this exact string — it already does per Task 1's implementation.

- [ ] **Step 2: Manual smoke test of live answer generation**

Run: `source .venv/bin/activate && python -c "
from retrieval.search import SearchService
s = SearchService()
results = s.search('what is hypertension', top_k=3, fetch_k=10)
print(''.join(s.answer('what is hypertension', [r['text'] for r in results])))
"`
Expected: prints a real streamed answer with `[N]` citations, no exception. Confirms the OpenRouter leg works end-to-end through the new router.

- [ ] **Step 3: Smoke test the RAGAS judge path**

Run: `source .venv/bin/activate && python -m eval.ragas_runner --limit 3`
Expected: completes without `TimeoutError`/`LLMDidNotFinishException` stack traces killing the run; prints the overall mean scores table.

- [ ] **Step 4: Remove the working design docs**

```bash
git rm docs/superpowers/specs/2026-09-12-litellm-groq-fallback-design.md
git rm docs/superpowers/plans/2026-09-12-litellm-groq-fallback.md
```

- [ ] **Step 5: Commit `.env.example` and doc removal together**

```bash
git add .env.example
git commit -m "$(cat <<'EOF'
Document Groq fallback env vars, remove working design docs

GROQ_API_KEY/GROQ_CHAT_MODEL documented in .env.example. Spec and plan
docs for this feature are removed now that implementation is complete
and the doc-sync agent has updated the permanent architecture docs.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Run the doc-sync agent**

Dispatch the `doc-sync` agent (per CLAUDE.md Rule #4) to update `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, and the `doc/feature/` OKF bundle to reflect: the new `llm/` module (`ChatRouterService`, `ChatRouterConfig`), the OpenRouter→Groq→OpenRouter fallback chain now used by `retrieval/search.py` and `eval/ragas_adapters.py`, and the `settings.py` pydantic-settings conversion.

- [ ] **Step 7: Push**

```bash
git push
```

## Self-Review Notes

- **Spec coverage:** All 5 goals covered — (1) Groq fallback via `ChatRouterService` (Tasks 3-5), (2) 3-step OpenRouter→Groq→OpenRouter order (Task 2's `fallback_chain`, Task 3's `from_settings`), (3) `settings.py` → pydantic-settings (Task 1), (4) strict pydantic validation on router config (Task 2), (5) embeddings/reranker untouched (no task modifies `ingestion/embedder.py` or `retrieval/reranker.py`).
- **Known risk flagged, not hidden:** Task 5's exact `ChatLiteLLMRouter` constructor kwargs are unconfirmed against the installed `litellm`/`langchain_litellm` version — Task 5 Step 1 requires checking the real signature before writing code, rather than the plan asserting a signature it hasn't verified. If `langchain_litellm` turns out not to exist or differs materially, the implementer should fall back to a minimal custom `BaseChatModel` subclass around `ChatRouterService.complete()`/`.stream()` — same interface, no other task changes.
- **Type consistency:** `ChatRouterService.stream()`/`.complete()` signatures (Task 3) match their usage in Task 4 (`retrieval/search.py`) and Task 5 (via `ChatLiteLLMRouter` wrapping `service._router` directly, not `service.stream`/`service.complete` — noted since ragas needs a LangChain `BaseChatModel`, not raw litellm calls).
- **User's explicit follow-up instruction** ("remove the extra design docs... then doc-sync... then commit and push") is captured as Task 6, the final task.
