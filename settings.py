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
    groq_chat_model: str = "groq/openai/gpt-oss-120b"

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
