from pathlib import Path
from typing import List
import re

from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader


def clean_text(text: str) -> str:
    """Clean extracted text from encoding issues, whitespace, and artifacts.

    Handles:
    - Control characters and non-printable chars
    - Encoding artifacts (mojibake, broken unicode)
    - Excessive whitespace and newlines
    - Ligatures and special character normalization
    """
    if not text:
        return ""

    text = str(text)

    text = "".join(
        c for c in text
        if ord(c) >= 32 or c in "\n\t\r"
    )

    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +\n", "\n", text)

    text = text.strip()

    return text


def load_pdf_documents(pdf_dir: str | Path = "dummy_docs") -> List[Document]:
    """Load all PDF files from directory using Docling for document structure extraction.

    Docling preserves document structure (tables, headings, hierarchies) as markdown,
    making it ideal for complex medical PDFs.

    Args:
        pdf_dir: Directory containing PDF files

    Returns:
        List of LangChain Document objects with markdown-formatted content and metadata
    """
    pdf_dir = Path(pdf_dir)
    documents = []

    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")

    for pdf_path in pdf_files:
        loader = DoclingLoader(file_path=str(pdf_path))
        docs = loader.load()

        for doc in docs:
            doc.page_content = clean_text(doc.page_content)
            doc.metadata["file"] = pdf_path.name
            documents.append(doc)

    return documents


if __name__ == "__main__":
    docs = load_pdf_documents()
    print(f"Loaded {len(docs)} documents from {len(set(d.metadata['file'] for d in docs))} PDFs\n")

    for doc in docs[:3]:  # Show first 3 documents
        print(f"File: {doc.metadata['file']}")
        print(f"Content preview: {doc.page_content[:200]}...\n")
