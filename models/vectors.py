from typing import Optional

from pydantic import BaseModel, Field


class Vector(BaseModel):
    chunk_id: str = Field(..., description="Associated chunk ID")
    embedding: list[float] = Field(..., description="Vector embedding values")
    model: str = Field(..., description="Embedding model used")
    dimension: int = Field(..., description="Vector dimension")


class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed")
    model: Optional[str] = None


class EmbeddingResult(BaseModel):
    text: str
    embedding: list[float]
    model: str
    dimension: int
