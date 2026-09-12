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
    fallback_chain: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def chain_references_known_deployments(self) -> "ChatRouterConfig":
        known = {d.model_name for d in self.deployments}
        unknown = [name for name in self.fallback_chain if name not in known]
        if unknown:
            raise ValueError(f"fallback_chain references unknown model_name(s): {unknown}")
        return self
