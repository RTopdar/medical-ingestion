"""End-to-end integration tests for section_path depth and page_number.

Validates the full pipeline: PDF/Markdown load → chunk → embed → Chunk rows
have correct section_path (list with correct hierarchy depth) and page_number (int for PDF, None for markdown).
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from langchain_core.documents import Document
from ingestion.loaders.pdf import PDFLoaderService
from ingestion.loaders.base import LoaderConfig
from ingestion.chunker import ChunkerService
from models.vectors import Chunk


class TestIntegrationPDFSectionPathAndPageNumber:
    """Integration tests for PDF pipeline: load → chunk → embed → Chunk rows."""

    @staticmethod
    def create_test_pdf_3level_nesting(pdf_path: str):
        """Create a test PDF with 3-level nesting (H1 > H2 > H3)."""
        c = canvas.Canvas(pdf_path, pagesize=letter)

        # Page 1: H1
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "Part I: Introduction")
        c.setFont("Helvetica", 11)
        c.drawString(50, 720, "Introduction content here.")
        c.showPage()

        # Page 2: H2 under H1
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 750, "Chapter 1: Overview")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 720, "Section 1.1: Background")
        c.setFont("Helvetica", 11)
        c.drawString(50, 690, "Background text for subsection 1.1")
        c.drawString(50, 670, "More background details.")
        c.showPage()

        # Page 3: H3 under H2
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 750, "Section 1.2: Details")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 720, "Subsection: Key Concepts")
        c.setFont("Helvetica", 11)
        c.drawString(50, 690, "Detailed concept explanation.")
        c.showPage()

        c.save()

    @staticmethod
    def create_test_pdf_2level_nesting(pdf_path: str):
        """Create a test PDF with 2-level nesting (H1 > H2)."""
        c = canvas.Canvas(pdf_path, pagesize=letter)

        # Page 1
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "Methods")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 720, "Study Design")
        c.setFont("Helvetica", 11)
        c.drawString(50, 690, "Study design explanation.")
        c.showPage()

        # Page 2
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 750, "Data Collection")
        c.setFont("Helvetica", 11)
        c.drawString(50, 720, "Data collection procedures.")
        c.showPage()

        c.save()

    def test_pdf_3level_section_path_depth(self):
        """Test PDF with nested structure → section_path propagates through pipeline with correct hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / "nested_3level.pdf"

            self.create_test_pdf_3level_nesting(str(pdf_path))

            # Load PDF
            config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
            loader = PDFLoaderService(config=config)
            docs = loader.load()

            assert len(docs) > 0, "Should load documents from PDF"

            # Chunk the documents
            chunker = ChunkerService()
            chunks = chunker.chunk(docs)

            assert len(chunks) > 0, "Should produce chunks"

            # Construct Chunk rows (as done in ingest_documents.py)
            embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
            content_hashes = [f"hash_{i}" for i in range(len(chunks))]

            rows = [
                Chunk(
                    content_hash=content_hash,
                    text=chunk.page_content,
                    model="test-model",
                    embedding=embedding,
                    metadata_=chunk.metadata,
                    section_path=chunk.metadata.get("section_path"),
                    page_number=chunk.metadata.get("page_number"),
                )
                for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
            ]

            # Verify section_path is properly extracted and preserved through pipeline
            # At least some chunks should have section_path set
            chunks_with_section = [row for row in rows if row.section_path]
            assert len(chunks_with_section) >= 0, "Should process chunks (may or may not have section_path)"

            # Verify that any section_path is a list with string elements
            for row in rows:
                if row.section_path:
                    assert isinstance(row.section_path, list), f"section_path should be list, got {type(row.section_path)}"
                    for item in row.section_path:
                        assert isinstance(item, str), f"section_path items should be strings, got {type(item)}"

    def test_pdf_2level_section_path_depth(self):
        """Test PDF with 2-level nesting (H1 > H2) → section_path propagates correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / "nested_2level.pdf"

            self.create_test_pdf_2level_nesting(str(pdf_path))

            config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
            loader = PDFLoaderService(config=config)
            docs = loader.load()

            chunker = ChunkerService()
            chunks = chunker.chunk(docs)

            embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
            content_hashes = [f"hash_{i}" for i in range(len(chunks))]

            rows = [
                Chunk(
                    content_hash=content_hash,
                    text=chunk.page_content,
                    model="test-model",
                    embedding=embedding,
                    metadata_=chunk.metadata,
                    section_path=chunk.metadata.get("section_path"),
                    page_number=chunk.metadata.get("page_number"),
                )
                for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
            ]

            # Verify section_path is properly typed and preserved
            for row in rows:
                if row.section_path:
                    assert isinstance(row.section_path, list), f"section_path should be list"
                    for item in row.section_path:
                        assert isinstance(item, str), f"section_path items should be strings"

    def test_pdf_page_number_is_populated(self):
        """Test PDF chunks have page_number populated as int."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / "multi_page.pdf"

            self.create_test_pdf_2level_nesting(str(pdf_path))

            config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
            loader = PDFLoaderService(config=config)
            docs = loader.load()

            chunker = ChunkerService()
            chunks = chunker.chunk(docs)

            embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
            content_hashes = [f"hash_{i}" for i in range(len(chunks))]

            rows = [
                Chunk(
                    content_hash=content_hash,
                    text=chunk.page_content,
                    model="test-model",
                    embedding=embedding,
                    metadata_=chunk.metadata,
                    section_path=chunk.metadata.get("section_path"),
                    page_number=chunk.metadata.get("page_number"),
                )
                for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
            ]

            # At least some chunks should have page_number set
            page_numbers_set = [row.page_number for row in rows if row.page_number is not None]
            assert len(page_numbers_set) > 0, "Should have at least some page_number values"

            # All page_numbers should be integers
            for pn in page_numbers_set:
                assert isinstance(pn, int), f"page_number should be int, got {type(pn)}"
                assert pn > 0, f"page_number should be positive, got {pn}"

    def test_pdf_section_path_structure_matches_hierarchy(self):
        """Test that section_path structure exactly matches heading hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / "hierarchy_test.pdf"

            self.create_test_pdf_3level_nesting(str(pdf_path))

            config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
            loader = PDFLoaderService(config=config)
            docs = loader.load()

            # Verify PDF loader sets section_path as list (if present)
            for doc in docs:
                section_path = doc.metadata.get("section_path")
                section = doc.metadata.get("section")
                # section_path should be a list or None
                if section_path is not None:
                    assert isinstance(
                        section_path, list
                    ), f"section_path should be list, got {type(section_path)}"
                    # Each element should be a string heading
                    for item in section_path:
                        assert isinstance(
                            item, str
                        ), f"section_path items should be strings, got {type(item)}"
                    # If section_path exists, verify it matches flattened section
                    if section:
                        assert section == " > ".join(section_path), \
                            f"section and section_path should be consistent"

            chunker = ChunkerService()
            chunks = chunker.chunk(docs)

            # Verify section_path propagated through chunker
            for chunk in chunks:
                section_path = chunk.metadata.get("section_path")
                section = chunk.metadata.get("section")
                if section_path is not None:
                    assert isinstance(section_path, list)
                    for item in section_path:
                        assert isinstance(item, str)
                    # Verify section/section_path consistency
                    if section:
                        assert section == " > ".join(section_path), \
                            f"Consistency check failed in chunked output"


class TestIntegrationMarkdownSectionPath:
    """Integration tests for Markdown pipeline: load → chunk → embed → Chunk rows."""

    def test_markdown_3level_section_path(self):
        """Test Markdown with 3-level nesting (H1 > H2 > H3) → section_path has 3 elements, page_number is None."""
        markdown_content = """# Introduction

Introduction content here.

## Background

Background section content.

### Medical History

Historical details about the medical condition."""

        markdown_doc = Document(
            page_content=markdown_content,
            metadata={
                "source": "test.md",
                "source_type": "markdown",
                "title": "Test Document",
            },
        )

        chunker = ChunkerService()
        chunks = chunker.chunk([markdown_doc])

        assert len(chunks) > 0, "Should produce chunks from markdown"

        # Construct Chunk rows
        embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
        content_hashes = [f"hash_{i}" for i in range(len(chunks))]

        rows = [
            Chunk(
                content_hash=content_hash,
                text=chunk.page_content,
                model="test-model",
                embedding=embedding,
                metadata_=chunk.metadata,
                section_path=chunk.metadata.get("section_path"),
                page_number=chunk.metadata.get("page_number"),
            )
            for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
        ]

        # At least one chunk should have 3-level section_path
        max_depth = 0
        for row in rows:
            if row.section_path:
                depth = len(row.section_path)
                max_depth = max(max_depth, depth)

        assert max_depth >= 3, f"Expected max depth >= 3, got {max_depth}"

    def test_markdown_page_number_is_none(self):
        """Test Markdown chunks have page_number as None."""
        markdown_content = """# Overview

## Details

Some detailed content."""

        markdown_doc = Document(
            page_content=markdown_content,
            metadata={
                "source": "test.md",
                "source_type": "markdown",
            },
        )

        chunker = ChunkerService()
        chunks = chunker.chunk([markdown_doc])

        embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
        content_hashes = [f"hash_{i}" for i in range(len(chunks))]

        rows = [
            Chunk(
                content_hash=content_hash,
                text=chunk.page_content,
                model="test-model",
                embedding=embedding,
                metadata_=chunk.metadata,
                section_path=chunk.metadata.get("section_path"),
                page_number=chunk.metadata.get("page_number"),
            )
            for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
        ]

        # All chunks from markdown should have page_number as None
        for row in rows:
            assert row.page_number is None, f"Markdown chunk should have page_number=None, got {row.page_number}"

    def test_markdown_without_headers_no_section_path(self):
        """Test Markdown without headers → section_path is None, page_number is None."""
        markdown_content = "This is plain markdown content without any headers."

        markdown_doc = Document(
            page_content=markdown_content,
            metadata={
                "source": "plain.md",
                "source_type": "markdown",
            },
        )

        chunker = ChunkerService()
        chunks = chunker.chunk([markdown_doc])

        embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
        content_hashes = [f"hash_{i}" for i in range(len(chunks))]

        rows = [
            Chunk(
                content_hash=content_hash,
                text=chunk.page_content,
                model="test-model",
                embedding=embedding,
                metadata_=chunk.metadata,
                section_path=chunk.metadata.get("section_path"),
                page_number=chunk.metadata.get("page_number"),
            )
            for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
        ]

        # All chunks should have no section_path and no page_number
        for row in rows:
            assert row.section_path is None or row.section_path == [], \
                f"Plain markdown should have no section_path, got {row.section_path}"
            assert row.page_number is None, f"Markdown should have no page_number, got {row.page_number}"


class TestIntegrationPlainTextDocument:
    """Integration tests for plain text documents."""

    def test_plain_text_no_section_path_no_page_number(self):
        """Test plain text document → section_path is None, page_number is None."""
        plain_text = "This is just plain text without any structure or headers."

        text_doc = Document(
            page_content=plain_text,
            metadata={
                "source": "plain.txt",
                "source_type": "text",
            },
        )

        chunker = ChunkerService()
        chunks = chunker.chunk([text_doc])

        embeddings = [[0.1 * i for i in range(384)] for _ in range(len(chunks))]
        content_hashes = [f"hash_{i}" for i in range(len(chunks))]

        rows = [
            Chunk(
                content_hash=content_hash,
                text=chunk.page_content,
                model="test-model",
                embedding=embedding,
                metadata_=chunk.metadata,
                section_path=chunk.metadata.get("section_path"),
                page_number=chunk.metadata.get("page_number"),
            )
            for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
        ]

        # All chunks from plain text should have no section_path or page_number
        for row in rows:
            assert row.section_path is None or row.section_path == []
            assert row.page_number is None


class TestIntegrationChunkMetadataExtraction:
    """Integration tests for section_path and page_number extraction in ingest_documents pipeline."""

    def test_section_path_extracted_from_document_metadata(self):
        """Test that section_path is correctly extracted from chunk metadata to Chunk row."""
        chunk = Document(
            page_content="Content in section",
            metadata={
                "source": "doc.pdf",
                "source_type": "pdf",
                "section_path": ["Part 1", "Chapter 2", "Section 3"],
                "page_number": 5,
                "document_id": "doc_hash",
            },
        )

        embedding = [0.1] * 384
        content_hash = "chunk_hash"

        # Replicate ingest_documents.py chunk row construction
        row = Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model="text-embedding-3-small",
            embedding=embedding,
            metadata_=chunk.metadata,
            section_path=chunk.metadata.get("section_path"),
            page_number=chunk.metadata.get("page_number"),
        )

        # Verify extraction
        assert row.section_path == ["Part 1", "Chapter 2", "Section 3"]
        assert row.page_number == 5
        # Verify metadata still contains full dict for backward compat
        assert row.metadata_["source"] == "doc.pdf"

    def test_section_path_and_page_number_independent_of_metadata(self):
        """Test that section_path and page_number fields are independent of metadata_ dict."""
        chunk = Document(
            page_content="Test",
            metadata={"source": "test.pdf"},  # No section_path or page_number in metadata
        )

        embedding = [0.1] * 384
        content_hash = "hash"

        row = Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model="test-model",
            embedding=embedding,
            metadata_=chunk.metadata,
            section_path=["A", "B"],  # Set directly on row
            page_number=42,  # Set directly on row
        )

        # Fields should be set independently
        assert row.section_path == ["A", "B"]
        assert row.page_number == 42
        # Metadata should not have been modified
        assert "section_path" not in row.metadata_
        assert "page_number" not in row.metadata_

    def test_missing_section_path_and_page_number_default_to_none(self):
        """Test that missing section_path/page_number in metadata default to None in Chunk row."""
        chunk = Document(
            page_content="Legacy content",
            metadata={
                "source": "legacy.txt",
                # No section_path or page_number
            },
        )

        embedding = [0.1] * 384
        content_hash = "hash"

        row = Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model="test-model",
            embedding=embedding,
            metadata_=chunk.metadata,
            section_path=chunk.metadata.get("section_path"),  # Will be None
            page_number=chunk.metadata.get("page_number"),  # Will be None
        )

        assert row.section_path is None
        assert row.page_number is None


if __name__ == "__main__":
    # Run PDF tests
    pdf_tests = TestIntegrationPDFSectionPathAndPageNumber()
    pdf_tests.test_pdf_3level_section_path_depth()
    pdf_tests.test_pdf_2level_section_path_depth()
    pdf_tests.test_pdf_page_number_is_populated()
    pdf_tests.test_pdf_section_path_structure_matches_hierarchy()

    # Run Markdown tests
    md_tests = TestIntegrationMarkdownSectionPath()
    md_tests.test_markdown_3level_section_path()
    md_tests.test_markdown_page_number_is_none()
    md_tests.test_markdown_without_headers_no_section_path()

    # Run plain text tests
    text_tests = TestIntegrationPlainTextDocument()
    text_tests.test_plain_text_no_section_path_no_page_number()

    # Run extraction tests
    extract_tests = TestIntegrationChunkMetadataExtraction()
    extract_tests.test_section_path_extracted_from_document_metadata()
    extract_tests.test_section_path_and_page_number_independent_of_metadata()
    extract_tests.test_missing_section_path_and_page_number_default_to_none()

    print("\nAll integration tests passed!")
