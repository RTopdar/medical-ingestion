from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    source: str = Field(..., description="Document source (file path, URL, etc.)")
    source_type: str = Field(..., description="Type of source (pdf, txt, web, db)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict, description="Custom metadata")


class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Full document text")
    title: Optional[str] = None
    metadata: Metadata


class Chunk(BaseModel):
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text")
    start_idx: int = Field(..., description="Character index in original document")
    end_idx: int = Field(..., description="Character index in original document")
    metadata: Metadata = Field(default_factory=lambda: Metadata(source="", source_type=""))
