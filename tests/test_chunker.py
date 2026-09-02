"""Tests for ChunkerService, including markdown header section_path extraction."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.documents import Document
from ingestion.chunker import ChunkerService


class TestMarkdownHeadersToSectionPath:
    """Tests for markdown header splitting and section_path extraction."""

    def test_split_by_markdown_headers_single_level(self):
        """Test markdown splitting with single H1 header."""
        text = """# Introduction

This is introduction text."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        assert len(docs) == 1
        doc = docs[0]
        assert "introduction text" in doc.page_content.lower()
        assert doc.metadata["section"] == "Introduction"
        assert doc.metadata["section_path"] == ["Introduction"]

    def test_split_by_markdown_headers_two_levels(self):
        """Test markdown splitting with H1 and H2 headers."""
        text = """# Introduction

Intro text here.

## Background

Background details."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        assert len(docs) == 2

        # First split: only H1
        assert docs[0].metadata["section"] == "Introduction"
        assert docs[0].metadata["section_path"] == ["Introduction"]

        # Second split: H1 > H2
        assert docs[1].metadata["section"] == "Introduction > Background"
        assert docs[1].metadata["section_path"] == ["Introduction", "Background"]

    def test_split_by_markdown_headers_three_levels(self):
        """Test markdown splitting with H1, H2, and H3 headers (nested hierarchy)."""
        text = """# Introduction

Intro content.

## Background

Background content.

### Medical History

History details."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        assert len(docs) == 3

        # First: H1 only
        assert docs[0].metadata["section"] == "Introduction"
        assert docs[0].metadata["section_path"] == ["Introduction"]

        # Second: H1 > H2
        assert docs[1].metadata["section"] == "Introduction > Background"
        assert docs[1].metadata["section_path"] == ["Introduction", "Background"]

        # Third: H1 > H2 > H3
        assert docs[2].metadata["section"] == "Introduction > Background > Medical History"
        assert docs[2].metadata["section_path"] == ["Introduction", "Background", "Medical History"]

    def test_split_by_markdown_headers_section_path_is_list(self):
        """Test that section_path is always a list (or None if no headers)."""
        text = """# Main

Main content.

## Sub

Sub content."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        for doc in docs:
            section_path = doc.metadata.get("section_path")
            assert section_path is None or isinstance(
                section_path, list
            ), f"section_path should be list or None, got {type(section_path)}"

            if section_path:
                for item in section_path:
                    assert isinstance(
                        item, str
                    ), f"section_path items should be strings, got {type(item)}"

    def test_split_by_markdown_headers_non_nested_sibling_sections(self):
        """Test handling of sibling sections (H2 under same H1)."""
        text = """# Introduction

Intro text.

## Background

Background text.

## Methods

Methods text."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        assert len(docs) == 3

        # First: H1
        assert docs[0].metadata["section_path"] == ["Introduction"]

        # Second: H1 > H2 (first subsection)
        assert docs[1].metadata["section_path"] == ["Introduction", "Background"]

        # Third: H1 > H2 (sibling subsection, H1 stays same)
        assert docs[2].metadata["section_path"] == ["Introduction", "Methods"]

    def test_split_by_markdown_headers_level_reset(self):
        """Test that deeper levels are reset when a shallower level reappears."""
        text = """# Introduction

Intro.

## Background

Back.

### Details

Details.

# Methods

Methods.

## Study Design

Design."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        assert len(docs) == 5

        # Section 0: H1 only
        assert docs[0].metadata["section_path"] == ["Introduction"]

        # Section 1: H1 > H2
        assert docs[1].metadata["section_path"] == ["Introduction", "Background"]

        # Section 2: H1 > H2 > H3
        assert docs[2].metadata["section_path"] == ["Introduction", "Background", "Details"]

        # Section 3: New H1 (H2 and H3 reset)
        assert docs[3].metadata["section_path"] == ["Methods"]

        # Section 4: H1 > H2 (H3 still reset)
        assert docs[4].metadata["section_path"] == ["Methods", "Study Design"]

    def test_section_and_section_path_coexist(self):
        """Test that both section (string) and section_path (list) are set."""
        text = """# Main

Content.

## Sub

Content."""

        service = ChunkerService()
        docs = service._split_by_markdown_headers(text)

        doc = docs[1]  # The H1 > H2 one
        assert doc.metadata["section"] == "Main > Sub"  # flattened string
        assert doc.metadata["section_path"] == ["Main", "Sub"]  # structured list

    def test_chunker_with_markdown_preserves_section_path(self):
        """Test that ChunkerService.chunk() preserves section_path through full pipeline."""
        markdown_doc = Document(
            page_content="""# Overview

Overview text here.

## Details

Detailed information that will be chunked.""",
            metadata={
                "source": "test.md",
                "source_type": "markdown",
            },
        )

        service = ChunkerService()
        chunks = service.chunk([markdown_doc])

        # Should have multiple chunks due to chunking
        assert len(chunks) > 0

        # All chunks should have metadata from the document
        for chunk in chunks:
            assert chunk.metadata.get("source") == "test.md"
            assert chunk.metadata.get("source_type") == "markdown"

            # section_path should be preserved if set
            section_path = chunk.metadata.get("section_path")
            if section_path is not None:
                assert isinstance(section_path, list)
                for item in section_path:
                    assert isinstance(item, str)

    def test_no_markdown_headers_no_section_path(self):
        """Test that documents without markdown headers don't have section_path set."""
        plain_doc = Document(
            page_content="This is plain text without any markdown headers.",
            metadata={"source": "plain.txt", "source_type": "text"},
        )

        service = ChunkerService()
        chunks = service.chunk([plain_doc])

        assert len(chunks) > 0
        for chunk in chunks:
            # Plain text documents won't go through markdown splitting,
            # so section_path won't be set in metadata
            section_path = chunk.metadata.get("section_path")
            # It should either be None or not present
            assert section_path is None or section_path == []


if __name__ == "__main__":
    test_class = TestMarkdownHeadersToSectionPath()
    test_class.test_split_by_markdown_headers_single_level()
    test_class.test_split_by_markdown_headers_two_levels()
    test_class.test_split_by_markdown_headers_three_levels()
    test_class.test_split_by_markdown_headers_section_path_is_list()
    test_class.test_split_by_markdown_headers_non_nested_sibling_sections()
    test_class.test_split_by_markdown_headers_level_reset()
    test_class.test_section_and_section_path_coexist()
    test_class.test_chunker_with_markdown_preserves_section_path()
    test_class.test_no_markdown_headers_no_section_path()
    print("All tests passed!")
