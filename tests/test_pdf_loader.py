"""Tests for PDF loader with section_path extraction."""
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from ingestion.loaders.pdf import PDFLoaderService
from ingestion.loaders.base import LoaderConfig


def create_test_pdf_with_headings(pdf_path: str):
    """Create a test PDF with nested heading hierarchy (H1 > H2 > H3)."""
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Page 1: H1
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, 750, "Part I: Introduction")
    c.showPage()

    # Page 2: H2 under H1
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 720, "Chapter 1: Overview")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 690, "Section 1.1: Background")
    c.setFont("Helvetica", 11)
    c.drawString(50, 660, "Body text under subsection 1.1")
    c.drawString(50, 640, "More body text here.")
    c.showPage()

    # Page 3: Another H3 under same H2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 720, "Section 1.2: Related Work")
    c.setFont("Helvetica", 11)
    c.drawString(50, 690, "More body text under section 1.2")
    c.showPage()

    # Page 4: New H2
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 720, "Chapter 2: Methodology")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 690, "Section 2.1: Data Collection")
    c.setFont("Helvetica", 11)
    c.drawString(50, 660, "Body text for data collection.")
    c.save()


def test_pdf_loader_extracts_section_metadata():
    """Test that PDF loader extracts section metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "test_document.pdf"

        # Create test PDF
        create_test_pdf_with_headings(str(pdf_path))

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Verify documents were loaded
        assert len(docs) > 0, "Should load at least one document"

        # Verify metadata fields exist
        for doc in docs:
            assert "section" in doc.metadata, "Should have section field"
            assert "section_path" in doc.metadata, "Should have section_path field"
            assert "page_number" in doc.metadata, "Should have page_number field"
            assert "source" in doc.metadata, "Should have source field"
            assert "element_type" in doc.metadata, "Should have element_type field"

        print(f"Loaded {len(docs)} documents from test PDF")
        print(f"First doc metadata keys: {list(docs[0].metadata.keys())}")


def test_pdf_loader_section_path_is_list():
    """Test that section_path is a list or None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "test_document.pdf"

        # Create test PDF
        create_test_pdf_with_headings(str(pdf_path))

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Check section_path type
        for doc in docs:
            section_path = doc.metadata.get("section_path")
            if section_path is not None:
                assert isinstance(
                    section_path, list
                ), f"section_path should be list, got {type(section_path)}"
                # Each element should be a string
                for item in section_path:
                    assert isinstance(item, str), f"section_path items should be strings, got {type(item)}"


def test_pdf_loader_preserves_section_string():
    """Test that flattened section string is still populated for backward compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "test_document.pdf"

        # Create test PDF
        create_test_pdf_with_headings(str(pdf_path))

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Check that section string exists
        for doc in docs:
            section = doc.metadata.get("section")
            if section is not None:
                assert isinstance(section, str), "section should be string"
                # If there's a section_path, section should be the flattened version
                if doc.metadata.get("section_path"):
                    section_path = doc.metadata["section_path"]
                    # Section should be " > " joined headings
                    expected_section = " > ".join(section_path)
                    assert section == expected_section, f"section mismatch: '{section}' != '{expected_section}'"


def test_pdf_loader_handles_empty_pdf():
    """Test that loader handles PDFs without headings gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "plain_document.pdf"

        # Create a simple PDF without headings
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(50, 750, "Just plain text without any headings.")
        c.save()

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Should still load successfully
        assert len(docs) > 0, "Should load document even without headings"

        # section_path should be None or empty for documents without headings
        for doc in docs:
            section_path = doc.metadata.get("section_path")
            section = doc.metadata.get("section")
            # Either both are None, or section_path is empty list
            if section_path is None:
                assert section is None or section == "", "Inconsistent section state"


def test_pdf_loader_page_number_extraction():
    """Test that page numbers are extracted correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "test_document.pdf"

        # Create test PDF with multiple pages
        create_test_pdf_with_headings(str(pdf_path))

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Check that page numbers are extracted
        page_numbers = [doc.metadata.get("page_number") for doc in docs]
        assert len(page_numbers) > 0, "Should have page numbers"
        # At least some should be numbers
        numeric_pages = [p for p in page_numbers if p is not None]
        assert len(numeric_pages) > 0, "Should have at least some numeric page numbers"


def test_pdf_loader_source_metadata():
    """Test that source metadata is correctly set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pdf_path = tmpdir_path / "my_document.pdf"

        # Create test PDF
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(50, 750, "Test content")
        c.save()

        # Load using PDFLoaderService
        config = LoaderConfig(source_dir=tmpdir_path, clean_text=False)
        loader = PDFLoaderService(config=config)
        docs = loader.load()

        # Check source metadata
        for doc in docs:
            assert "source" in doc.metadata
            assert "source_type" in doc.metadata
            assert doc.metadata["source_type"] == "pdf"
            assert str(pdf_path) in doc.metadata["source"]
            assert doc.metadata["title"] == "my_document"


if __name__ == "__main__":
    test_pdf_loader_extracts_section_metadata()
    test_pdf_loader_section_path_is_list()
    test_pdf_loader_preserves_section_string()
    test_pdf_loader_handles_empty_pdf()
    test_pdf_loader_page_number_extraction()
    test_pdf_loader_source_metadata()
    print("\nAll PDF loader tests passed!")
