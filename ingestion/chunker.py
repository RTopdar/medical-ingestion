import uuid
from typing import Optional

from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter

from settings import settings

from models.documents import Document, Chunk, Metadata


class ChunkerConfig(BaseModel):
    """Configuration for text chunking."""

    chunk_size: int = Field(
        default=settings.chunk_size,
        description="Target chunk size in characters (400-800 per spec)",
    )
    chunk_overlap: int = Field(
        default=settings.chunk_overlap,
        description="Overlap between chunks in characters (100-200 per spec)",
    )


class ChunkerService(BaseModel):
    """Convert Documents to Chunks using configurable strategy."""

    config: ChunkerConfig = Field(default_factory=ChunkerConfig)

    class Config:
        arbitrary_types_allowed = True

    def chunk(self, documents: list[Document]) -> list[Chunk]:
        """Split Documents into Chunks with metadata preservation."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            add_start_index=True,
        )

        chunks = []
        for doc in documents:
            # LangChain splitter for character-level splitting
            split_texts = splitter.split_text(doc.content)

            # Reconstruct with proper indices
            char_pos = 0
            for text in split_texts:
                # Find actual position in original content
                start_idx = doc.content.find(text, char_pos)
                if start_idx == -1:
                    start_idx = char_pos
                end_idx = start_idx + len(text)
                char_pos = end_idx

                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=doc.id,
                    content=text,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    metadata=Metadata(
                        source=doc.metadata.source,
                        source_type=doc.metadata.source_type,
                        tags=doc.metadata.tags + ["chunk"],
                        extra={
                            **doc.metadata.extra,
                            "parent_title": doc.title,
                        },
                    ),
                )
                chunks.append(chunk)

        return chunks
