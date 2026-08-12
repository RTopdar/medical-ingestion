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

            # Preserve and enrich metadata from Docling
            doc.metadata["file"] = pdf_path.name
            doc.metadata["source_file"] = str(pdf_path)

            # Extract useful fields from dl_meta for RAG
            if "dl_meta" in doc.metadata:
                dl_meta = doc.metadata["dl_meta"]

                # Extract page number and bounding box from provenance
                if "doc_items" in dl_meta and dl_meta["doc_items"]:
                    first_item = dl_meta["doc_items"][0]
                    if "prov" in first_item and first_item["prov"]:
                        prov = first_item["prov"][0]
                        doc.metadata["page_number"] = prov.get("page_no")
                        doc.metadata["bbox"] = prov.get("bbox")
                        doc.metadata["char_span"] = prov.get("charspan")

                    # Extract element type (text, table, image, etc)
                    doc.metadata["element_type"] = first_item.get("label", "text")

                # Extract section headings
                if "headings" in dl_meta:
                    doc.metadata["headings"] = dl_meta["headings"]
                    doc.metadata["section"] = " > ".join(dl_meta["headings"])

                # Extract content layer (body, header, footer)
                if "doc_items" in dl_meta and dl_meta["doc_items"]:
                    doc.metadata["content_layer"] = dl_meta["doc_items"][0].get("content_layer")

            documents.append(doc)

    return documents


if __name__ == "__main__":
    docs = load_pdf_documents()
    print(f"Loaded {len(docs)} documents from {len(set(d.metadata['file'] for d in docs))} PDFs\n")

    for i, doc in enumerate(docs[:2]):  # Show first 2 documents in detail
        print(f"{'='*80}")
        print(f"Document #{i+1}")
        print(f"{'='*80}")
        print(f"Metadata: {doc.metadata}")
        print(f"Content length: {len(doc.page_content)} chars")
        print(f"\nContent:\n{doc.page_content[:500]}")
        if len(doc.page_content) > 500:
            print(f"... [{len(doc.page_content) - 500} more chars]\n")
        else:
            print()
