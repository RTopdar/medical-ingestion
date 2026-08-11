from typing import Optional

from pydantic import BaseModel, Field

from models.documents import Chunk


class RetrievedContext(BaseModel):
    chunk: Chunk
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    rank: int = Field(..., description="Rank in retrieval results")


class RAGQuery(BaseModel):
    query: str = Field(..., description="User query text")
    top_k: int = Field(default=5, description="Number of retrieved contexts")
    filters: Optional[dict] = Field(default=None, description="Metadata filters")


class RAGResponse(BaseModel):
    query: str
    answer: str = Field(..., description="Generated answer from LLM")
    retrieved_contexts: list[RetrievedContext]
    model: str = Field(..., description="LLM model used")
    source_citations: list[str] = Field(default_factory=list)
