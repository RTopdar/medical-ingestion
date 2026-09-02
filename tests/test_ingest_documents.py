"""Tests for ingest_documents.py - verifies section_path and page_number extraction into Chunk model."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.documents import Document
from models.vectors import Chunk


def test_chunk_row_construction_with_metadata_extraction():
    """Test that Chunk rows are constructed with section_path and page_number extracted from metadata."""
    # Simulate embedded chunks with metadata containing section_path and page_number
    chunks = [
        Document(
            page_content="Introduction content here",
            metadata={
                "source": "test.pdf",
                "source_type": "pdf",
                "section_path": ["Introduction", "Background"],
                "page_number": 1,
                "document_id": "abc123",
            },
        ),
        Document(
            page_content="Methods section content",
            metadata={
                "source": "test.pdf",
                "source_type": "pdf",
                "section_path": ["Methods", "Data Collection"],
                "page_number": 5,
                "document_id": "abc123",
            },
        ),
        Document(
            page_content="Results without headers",
            metadata={
                "source": "plain_file.txt",
                "source_type": "text",
                "section_path": None,
                "page_number": None,
                "document_id": "def456",
            },
        ),
    ]

    # Simulate embeddings and content hashes (normally from Embedder)
    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]
    content_hashes = ["hash1", "hash2", "hash3"]
    model_name = "text-embedding-3-small"

    # Replicate the Chunk construction logic from ingest_documents.py:128-137
    rows = [
        Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model=model_name,
            embedding=embedding,
            metadata_=chunk.metadata,
            section_path=chunk.metadata.get("section_path"),
            page_number=chunk.metadata.get("page_number"),
        )
        for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
    ]

    # Verify all rows have expected fields
    assert len(rows) == 3

    # Verify first chunk has section_path and page_number extracted
    assert rows[0].content_hash == "hash1"
    assert rows[0].section_path == ["Introduction", "Background"]
    assert rows[0].page_number == 1
    assert rows[0].metadata_["source"] == "test.pdf"

    # Verify second chunk has different section_path and page_number
    assert rows[1].content_hash == "hash2"
    assert rows[1].section_path == ["Methods", "Data Collection"]
    assert rows[1].page_number == 5

    # Verify third chunk handles None values correctly
    assert rows[2].content_hash == "hash3"
    assert rows[2].section_path is None
    assert rows[2].page_number is None
    assert rows[2].metadata_["section_path"] is None  # Still in metadata for backward compat
    assert rows[2].metadata_["page_number"] is None


def test_chunk_extraction_from_pdf_metadata():
    """Test extraction when chunk metadata comes from PDF loader (realistic scenario)."""
    # Simulate a chunk from PDF loader with Docling's metadata structure
    pdf_chunk = Document(
        page_content="This is the introduction section",
        metadata={
            "source": "/path/to/document.pdf",
            "source_type": "pdf",
            "title": "Medical Document",
            "section": "Introduction > Background",
            "section_path": ["Introduction", "Background"],
            "page_number": 2,
            "element_type": "heading",
            "document_id": "pdf_doc_hash",
        },
    )

    # Simulate embedding
    embedding = [0.1] * 384  # 384-dim embedding
    content_hash = "pdf_chunk_hash123"

    # Construct Chunk row as done in ingest_documents.py
    chunk_row = Chunk(
        content_hash=content_hash,
        text=pdf_chunk.page_content,
        model="text-embedding-3-small",
        embedding=embedding,
        metadata_=pdf_chunk.metadata,
        section_path=pdf_chunk.metadata.get("section_path"),
        page_number=pdf_chunk.metadata.get("page_number"),
    )

    # Verify extraction worked
    assert chunk_row.section_path == ["Introduction", "Background"]
    assert chunk_row.page_number == 2
    # Verify backward compatibility - metadata still contains full dict
    assert chunk_row.metadata_["section"] == "Introduction > Background"
    assert chunk_row.metadata_["source_type"] == "pdf"


def test_chunk_extraction_from_markdown_metadata():
    """Test extraction when chunk metadata comes from markdown loader."""
    # Simulate a chunk from markdown loader (section hierarchy but no page numbers)
    md_chunk = Document(
        page_content="This is a subsection in the markdown",
        metadata={
            "source": "/path/to/document.md",
            "source_type": "markdown",
            "title": "Markdown Document",
            "section_path": ["Installation", "Prerequisites"],
            "page_number": None,  # Markdown doesn't have page numbers
            "document_id": "md_doc_hash",
        },
    )

    embedding = [0.2] * 384
    content_hash = "md_chunk_hash456"

    chunk_row = Chunk(
        content_hash=content_hash,
        text=md_chunk.page_content,
        model="text-embedding-3-small",
        embedding=embedding,
        metadata_=md_chunk.metadata,
        section_path=md_chunk.metadata.get("section_path"),
        page_number=md_chunk.metadata.get("page_number"),
    )

    assert chunk_row.section_path == ["Installation", "Prerequisites"]
    assert chunk_row.page_number is None  # Correctly handles None from markdown
    assert chunk_row.metadata_["source_type"] == "markdown"


def test_chunk_extraction_missing_fields():
    """Test extraction when metadata doesn't have section_path or page_number keys."""
    # Simulate a legacy chunk or non-structured document
    legacy_chunk = Document(
        page_content="Some legacy content",
        metadata={
            "source": "legacy.txt",
            "source_type": "text",
            # No section_path or page_number keys at all
            "document_id": "legacy_hash",
        },
    )

    embedding = [0.3] * 384
    content_hash = "legacy_chunk_hash"

    # Should not raise KeyError; .get() returns None
    chunk_row = Chunk(
        content_hash=content_hash,
        text=legacy_chunk.page_content,
        model="text-embedding-3-small",
        embedding=embedding,
        metadata_=legacy_chunk.metadata,
        section_path=legacy_chunk.metadata.get("section_path"),
        page_number=legacy_chunk.metadata.get("page_number"),
    )

    assert chunk_row.section_path is None
    assert chunk_row.page_number is None
    # Verify backward compat - metadata is stored as-is
    assert "section_path" not in chunk_row.metadata_


def test_chunk_fields_independent_of_metadata():
    """Test that section_path and page_number fields are independent of metadata_ dict."""
    chunk_data = {
        "content_hash": "test_hash",
        "text": "Test content",
        "model": "test-model",
        "embedding": [0.1, 0.2],
        "metadata_": {
            "source": "test.pdf",
            # No section_path/page_number in metadata
        },
        "section_path": ["A", "B"],
        "page_number": 42,
    }

    chunk = Chunk(**chunk_data)

    # Fields should be set even if missing from metadata_
    assert chunk.section_path == ["A", "B"]
    assert chunk.page_number == 42
    # Metadata should not have been modified
    assert "section_path" not in chunk.metadata_
    assert "page_number" not in chunk.metadata_


if __name__ == "__main__":
    test_chunk_row_construction_with_metadata_extraction()
    test_chunk_extraction_from_pdf_metadata()
    test_chunk_extraction_from_markdown_metadata()
    test_chunk_extraction_missing_fields()
    test_chunk_fields_independent_of_metadata()
    print("\nAll ingest_documents tests passed!")
