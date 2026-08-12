#!/usr/bin/env python3
"""Basic document ingestion pipeline - load from all sources."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.loaders import LoaderFactory
from ingestion.chunker import ChunkerConfig, ChunkerService
from models.documents import Document


def ingest_json_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest JSON documents with rich metadata."""
    print(f"Loading JSON documents from {data_dir}...")
    loader = LoaderFactory.json_loader(data_dir)
    docs = loader.load()
    print(f"  ✓ Loaded {len(docs)} documents from JSON")

    # Print metadata preview
    for doc in docs[:1]:
        print(f"\n  Sample document:")
        print(f"    ID: {doc.id}")
        print(f"    Title: {doc.title}")
        print(f"    Content length: {len(doc.content)} chars")
        print(f"    Metadata keys: {list(doc.metadata.extra.keys())}")
        if "nested_metadata" in doc.metadata.extra:
            nested = doc.metadata.extra["nested_metadata"]
            print(f"    Flattened metadata sample:")
            for k in list(nested.keys())[:5]:
                print(f"      - {k}: {str(nested[k])[:50]}...")

    return docs


def ingest_pdf_documents(data_dir: str | Path = "data/pdf") -> list[Document]:
    """Ingest PDF documents."""
    try:
        print(f"Loading PDF documents from {data_dir}...")
        loader = LoaderFactory.pdf_loader(data_dir)
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} documents from PDF")
        return docs
    except FileNotFoundError:
        print(f"  ⊘ No PDF files found in {data_dir}")
        return []


def ingest_csv_excel_documents(data_dir: str | Path = "data/csv") -> list[Document]:
    """Ingest CSV and Excel documents."""
    try:
        print(f"Loading CSV/Excel documents from {data_dir}...")
        loader = LoaderFactory.excel_csv_loader(data_dir)
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} documents from CSV/Excel")
        return docs
    except FileNotFoundError:
        print(f"  ⊘ No CSV/Excel files found in {data_dir}")
        return []


def chunk_documents(documents: list[Document]) -> list:
    """Chunk documents for RAG."""
    print(f"\nChunking {len(documents)} documents...")
    config = ChunkerConfig(chunk_size=512, chunk_overlap=100)
    chunker = ChunkerService(config=config)
    chunks = chunker.chunk(documents)
    print(f"  ✓ Created {len(chunks)} chunks")
    return chunks


def main():
    """Run full ingestion pipeline."""
    print("=" * 60)
    print("MEDICAL DOCUMENT INGESTION PIPELINE")
    print("=" * 60)

    all_documents = []

    # Ingest from different sources
    all_documents.extend(ingest_json_documents())
    all_documents.extend(ingest_pdf_documents())
    all_documents.extend(ingest_csv_excel_documents())

    if not all_documents:
        print("\n✗ No documents ingested!")
        return

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(all_documents)} documents loaded")
    print(f"{'=' * 60}")

    # Chunk documents
    chunks = chunk_documents(all_documents)

    # Print statistics
    print(f"\nIngestion Summary:")
    print(f"  Documents: {len(all_documents)}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Avg chunk size: {sum(len(c.content) for c in chunks) // len(chunks)} chars")

    return all_documents, chunks


if __name__ == "__main__":
    main()
