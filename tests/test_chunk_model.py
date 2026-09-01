"""Tests for Chunk model with section_path and page_number fields."""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.vectors import Chunk


def test_chunk_with_section_path_and_page_number():
    """Test creating a Chunk with both new fields set."""
    chunk = Chunk(
        content_hash="abc123def456",
        text="This is a test chunk",
        model="text-embedding-3-small",
        embedding=[0.1, 0.2, 0.3],
        section_path=["Introduction", "Background", "Medical History"],
        page_number=5,
        metadata_={"source": "test_pdf.pdf", "patient_mrn": "12345"},
    )

    assert chunk.content_hash == "abc123def456"
    assert chunk.text == "This is a test chunk"
    assert chunk.model == "text-embedding-3-small"
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.section_path == ["Introduction", "Background", "Medical History"]
    assert chunk.page_number == 5
    assert chunk.metadata_ == {"source": "test_pdf.pdf", "patient_mrn": "12345"}
    assert chunk.id is None  # Not yet persisted
    assert isinstance(chunk.created_at, datetime)


def test_chunk_with_null_section_path_and_page_number():
    """Test creating a Chunk with both new fields as None (nullable)."""
    chunk = Chunk(
        content_hash="xyz789",
        text="Another test chunk",
        model="text-embedding-3-large",
        embedding=[0.4, 0.5, 0.6],
        section_path=None,
        page_number=None,
        metadata_={"source": "another_source"},
    )

    assert chunk.content_hash == "xyz789"
    assert chunk.text == "Another test chunk"
    assert chunk.model == "text-embedding-3-large"
    assert chunk.section_path is None
    assert chunk.page_number is None
    assert chunk.metadata_ == {"source": "another_source"}
    assert isinstance(chunk.created_at, datetime)


def test_chunk_default_null_section_path_and_page_number():
    """Test creating a Chunk without specifying new fields defaults to None."""
    chunk = Chunk(
        content_hash="default789",
        text="Default test chunk",
        model="text-embedding-3-small",
        embedding=[0.7, 0.8, 0.9],
    )

    assert chunk.section_path is None
    assert chunk.page_number is None
    assert chunk.metadata_ == {}  # default_factory creates empty dict


def test_chunk_model_dict_representation():
    """Test that Chunk serializes correctly including new fields."""
    chunk = Chunk(
        content_hash="dict_test123",
        text="Dict test chunk",
        model="text-embedding-3-small",
        embedding=[0.1, 0.2],
        section_path=["Section A", "Subsection B"],
        page_number=10,
        metadata_={"custom_key": "custom_value"},
    )

    # Convert to dict to verify all fields are present
    chunk_dict = chunk.model_dump()

    assert "section_path" in chunk_dict
    assert "page_number" in chunk_dict
    assert chunk_dict["section_path"] == ["Section A", "Subsection B"]
    assert chunk_dict["page_number"] == 10


if __name__ == "__main__":
    test_chunk_with_section_path_and_page_number()
    test_chunk_with_null_section_path_and_page_number()
    test_chunk_default_null_section_path_and_page_number()
    test_chunk_model_dict_representation()
    print("All tests passed!")
