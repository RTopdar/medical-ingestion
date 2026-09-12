# LiteLLM + Groq Chat Fallback, and Settings → pydantic-settings

Date: 2026-09-12
Status: Approved, pending implementation plan

## Problem

`eval/ragas_runner.py` runs against a single upstream (OpenRouter) with no
retry/fallback beyond ragas's own `RunConfig` (timeout/retries on the *same*
provider). Under concurrent judge calls, OpenRouter rate-limits and times out,
producing partial/failed eval runs (see prior fix: lowered `max_workers`,
raised `timeout`/`max_retries` in `RunConfig`, raised judge `max_tokens`).

Separately, `settings.py` is a plain class reading `os.getenv` with no
validation — a typo'd or missing env var surfaces as a runtime `AttributeError`
or silent wrong-type value deep in a call stack instead of a clear error at
startup.

## Goals

1. Add a second chat-completions provider (Groq) as an automatic fallback for
   all LLM **chat** calls (answer generation, RAGAS judge), without touching
   embeddings or reranking (Groq has no such endpoints — those stay on direct
   OpenRouter HTTP calls, unchanged).
2. Fallback order is a fixed 3-step chain: **OpenRouter → Groq → OpenRouter**
   (retry primary once more after Groq also fails, rather than giving up after
   two providers).
3. Convert `settings.py` to `pydantic-settings` for typed, validated
   configuration — zero call-site changes across the 13 files that import
   `settings`.
4. Any new list/param structures (the router's model list, per-model
   parameters) are strict pydantic models — no raw dicts passed to litellm's
   `Router` without validation first.

## Non-Goals

- Embeddings (`ingestion/embedder.py`) and reranking (`retrieval/reranker.py`)
  are not touched — Groq has no embeddings or rerank API.
- No change to the RAGAS `RunConfig` tuning already in place
  (`eval/ragas_runner.py`) — this is additive (a more resilient LLM
  underneath), not a replacement for it.
- No change to vector DB, ingestion pipeline, or chunking.

## Dependency Check (done)

Ran `uv add pydantic-settings litellm` against the live `.venv`:

- Resolves cleanly, 9 packages added/changed.
- `openai` transitively downgraded 3.3.0 → 2.54.0 (litellm's pin). No file in
  the repo imports `openai` directly (grep confirmed) — only pulled in
  transitively via `langchain-openai`/ragas — so this is safe.
- `litellm.Router` and `pydantic_settings` import cleanly and coexist with the
  existing `ragas` + `langchain_openrouter` stack, including the vertexai
  import-order workaround already documented in `eval/ragas_adapters.py`
  (that workaround must still run before `import ragas`, unrelated to
  litellm).

## Design

### 1. `settings.py` → `pydantic-settings`

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    chat_model: str = "openrouter/meta-llama/llama-2-7b-chat"
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_batch_size: int = Field(default=100, gt=0)
    reranker_model: str = "nvidia/llama-nemotron-rerank-vl-1b-v2:free"
    ragas_judge_model: str | None = None

    groq_api_key: str = ""
    groq_chat_model: str = "groq/llama-3.3-70b-versatile"

    vector_db_type: str = "qdrant"
    vector_db_path: str = "./data/chroma"
    qdrant_url: str = "http://localhost:6333"
    bm25_index_path: str = "./data/bm25_index"

    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=100, ge=0)
    input_data_path: str = "./data/input"

    sqlite_db_path: str = "./data/medical.db"
    clinical_trials_table: str = "clinical_trials"
    eligibility_table: str = "eligibility"
    postgres_dsn: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/medical_ingestion"
    )

    log_level: str = "INFO"

    def validate_required(self) -> None:
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set. Set via env var or .env file.")


settings = Settings()
```

Env var names are unchanged (pydantic-settings uppercases the field name by
default: `chat_model` → `CHAT_MODEL`), so **no `.env` rewrite needed** for
existing vars — only the two new Groq vars are added.

`Settings.validate()` was a classmethod with no callers anywhere in the repo
(confirmed via grep) and was already buggy (referenced `cls.openrouter_api_key`
on the class, not an instance). Replaced with an instance method
`validate_required()`; since nothing calls it today this is a like-for-like
dead-code carry-forward, not a behavior change.

`__repr__` stays as an explicit override (unchanged) since pydantic's default
repr would leak `openrouter_api_key` in plain text.

### 2. `llm/config.py` — strict pydantic models for router configuration

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LiteLLMModelParams(BaseModel):
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

### 3. `llm/chat_router.py` — the reusable service class

```python
from langchain_core.language_models.chat_models import BaseChatModel
from litellm import Router

from llm.config import ChatRouterConfig, LiteLLMDeployment, LiteLLMModelParams
from settings import Settings


class ChatRouterService:
    """Owns one litellm Router built from a validated ChatRouterConfig.
    Single source of truth for the OpenRouter -> Groq -> OpenRouter fallback
    chain, reused by retrieval/search.py and eval/ragas_adapters.py so the
    chain is defined exactly once."""

    def __init__(self, config: ChatRouterConfig):
        self.config = config
        self._router = Router(
            model_list=[d.model_dump() for d in config.deployments],
            fallbacks=[{config.fallback_chain[0]: config.fallback_chain[1:]}],
            num_retries=0,  # the fallback_chain IS the retry policy; no extra per-node retries
        )

    def stream(self, messages: list[dict], **kwargs):
        return self._router.completion(model=self.config.fallback_chain[0], messages=messages, stream=True, **kwargs)

    def complete(self, messages: list[dict], **kwargs):
        return self._router.completion(model=self.config.fallback_chain[0], messages=messages, **kwargs)

    @classmethod
    def from_settings(cls, settings: Settings) -> "ChatRouterService":
        """Standard OpenRouter -> Groq -> OpenRouter chain from Settings."""
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

Exact LangChain adapter shape (raw `litellm.Router.completion` vs. wrapping in
a `BaseChatModel` subclass so `search.py`'s `HumanMessage`/`.stream()` call
sites don't change) is an implementation-plan-level decision, not a design
one — both are mechanical. Preference is to keep `search.py`/`ragas_adapters.py`
call sites as close to their current shape as possible (minimize diff).

### 4. Call site changes

**`retrieval/search.py::answer()`**: replace
```python
llm = ChatOpenRouter(model=settings.chat_model, temperature=0.7, streaming=True)
for chunk in llm.stream([HumanMessage(content=prompt)]):
```
with the `ChatRouterService.from_settings(settings)` singleton (built once in
`SearchService.__init__`, not per-call) and its `.stream(...)` method.

**`eval/ragas_adapters.py::build_ragas_llm()`**: replace the direct
`ChatOpenRouter(...)` construction with `ChatRouterService.from_settings(settings)`,
still wrapped in `LangchainLLMWrapper` for ragas.

### 5. New/changed files

- `llm/config.py` (new) — pydantic models
- `llm/chat_router.py` (new) — `ChatRouterService`
- `settings.py` (rewrite) — pydantic-settings
- `retrieval/search.py` (edit) — use `ChatRouterService`
- `eval/ragas_adapters.py` (edit) — use `ChatRouterService`
- `.env.example` (edit) — add `GROQ_API_KEY`, `GROQ_CHAT_MODEL`
- `pyproject.toml` — `litellm`, `pydantic-settings` (already added and verified)

### Testing

- Unit: `llm/config.py` validators (missing provider prefix rejected,
  unknown fallback_chain name rejected, out-of-range temperature rejected).
- Unit: `ChatRouterService.from_settings` builds without error given a fake
  `Settings`.
- Integration/smoke: `retrieval/search.py::answer()` still streams a real
  answer (manual smoke test, since it needs live API keys).
- Regression: rerun `eval/ragas_runner.py --limit 5` end-to-end to confirm the
  new router doesn't break judge scoring and fallback engages correctly if
  OpenRouter is throttled.
- `settings.py`: import `from settings import settings` in a fresh process and
  confirm all 13 existing importers still get attribute access unchanged (no
  code change needed in those files, verified by running existing test suite).
