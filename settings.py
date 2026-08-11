import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuration loaded from environment (shell priority > .env)."""

    # OpenRouter
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Models
    chat_model: str = os.getenv("CHAT_MODEL", "openrouter/meta-llama/llama-2-7b-chat")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Vector DB
    vector_db_type: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/chroma")

    # Ingestion
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1024"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    input_data_path: str = os.getenv("INPUT_DATA_PATH", "./data/input")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required settings."""
        if not cls.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set. Set via env var or .env file.")

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  openrouter_api_key={'***' if self.openrouter_api_key else 'NOT SET'}\n"
            f"  chat_model={self.chat_model}\n"
            f"  embedding_model={self.embedding_model}\n"
            f"  vector_db_type={self.vector_db_type}\n"
            f"  chunk_size={self.chunk_size}\n"
            f")"
        )


settings = Settings()
