from pathlib import Path
from typing import List

from langchain_docling.loader import DoclingLoader
from langchain_core.documents import Document


def load_pdf_documents(pdf_dir: str | Path = "dummy_docs") -> List[Document]:
    """Load all PDF files from directory using Docling for structure-aware parsing.

    Docling extracts page numbers, headings/section context, bounding boxes,
    and element types (text/table/figure), making it better for RAG than
    naive page-by-page text dumps.

    Args:
        pdf_dir: Directory containing PDF files

    Returns:
        List of LangChain Document objects with structured metadata
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
            doc.metadata["file"] = pdf_path.name
            doc.metadata["source_file"] = str(pdf_path)
            doc.metadata["format"] = "pdf"

            documents.append(doc)

    return documents


if __name__ == "__main__":
    print("=" * 80)
    print("PDF EXTRACTION")
    print("=" * 80)
    try:
        pdf_docs = load_pdf_documents()
        print(f"Loaded {len(pdf_docs)} elements from PDF files\n")

        for i, doc in enumerate(pdf_docs[:3]):
            print(f"{'='*80}")
            print(f"Element #{i+1}")
            print(f"{'='*80}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content length: {len(doc.page_content)} chars")
            print(f"\nContent:\n{doc.page_content[:500]}")
            if len(doc.page_content) > 500:
                print(f"... [{len(doc.page_content) - 500} more chars]\n")
            else:
                print()
    except FileNotFoundError as e:
        print(f"No PDF files to demonstrate: {e}\n")
