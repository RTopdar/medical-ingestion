#!/usr/bin/env python3
"""Document ingestion pipeline - load, chunk, embed, and push to Qdrant.

Usage:
  python scripts/ingest_documents.py               # All filetypes from dummy_docs
  python scripts/ingest_documents.py --filetype=pdf
  python scripts/ingest_documents.py --filetype=json,csv
  python scripts/ingest_documents.py --help
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.getLogger("qdrant_client").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from langchain_core.documents import Document
from tqdm import tqdm

from ingestion.chunker import ChunkerConfig, ChunkerService
from ingestion.embedder import Embedder
from ingestion.loaders import LoaderFactory
from models.vectors import Chunk, IngestedDocument
from storage.chunk_store import ChunkStore
from storage.postgres import engine, init_db
from vector_db import QdrantVectorStore


def ingest_json_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest JSON documents with rich metadata."""
    try:
        print(f"Loading JSON documents from {data_dir}...")
        loader = LoaderFactory.json_loader(data_dir)
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} documents from JSON")

        for doc in docs[:1]:
            print(f"\n  Sample document:")
            print(f"    Title: {doc.metadata.get('title')}")
            print(f"    Content length: {len(doc.page_content)} chars")
            print(f"    Metadata keys: {list(doc.metadata.keys())}")

        return docs
    except FileNotFoundError:
        print(f"  ⊘ No JSON files found in {data_dir}")
        return []


def ingest_pdf_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest PDF documents (Docling extraction)."""
    try:
        print(f"Loading PDF documents from {data_dir}...")
        loader = LoaderFactory.pdf_loader(data_dir)
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} documents from PDF")
        return docs
    except (FileNotFoundError, Exception) as e:
        print(f"  ⊘ No PDF files found or error: {e}")
        return []


def ingest_csv_excel_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest CSV and Excel documents."""
    try:
        print(f"Loading CSV/Excel documents from {data_dir}...")
        loader = LoaderFactory.excel_csv_loader(data_dir)
        docs = loader.load()
        print(f"  ✓ Loaded {len(docs)} documents from CSV/Excel")
        return docs
    except (FileNotFoundError, Exception):
        print(f"  ⊘ No CSV/Excel files found in {data_dir}")
        return []


def filter_seen_documents(documents: list[Document], store: ChunkStore) -> list[Document]:
    """Drop documents whose full content has already been ingested (exact re-upload),
    so they skip chunking, embedding, and storage entirely. Surviving documents get
    their content_hash threaded into metadata['document_id'] for chunk provenance."""
    new_documents = []
    skipped = 0
    for doc in documents:
        content_hash = IngestedDocument.make_content_hash(doc.page_content)
        if store.document_seen(content_hash):
            skipped += 1
            continue
        store.mark_document_seen(content_hash, doc.metadata.get("source", "unknown"))
        doc.metadata["document_id"] = content_hash
        new_documents.append(doc)

    if skipped:
        print(f"  ⊘ Skipped {skipped} already-ingested document(s)")
    return new_documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Chunk documents for RAG."""
    print(f"\nChunking {len(documents)} documents...")
    config = ChunkerConfig(chunk_size=512, chunk_overlap=100)
    chunker = ChunkerService(config=config)
    with tqdm(total=len(documents), desc="Chunking", unit="doc") as pbar:
        chunks = chunker.chunk(documents)
        pbar.update(len(documents))
    print(f"  ✓ Created {len(chunks)} chunks")
    return chunks


def embed_and_store(chunks: list[Document]) -> None:
    """Embed chunks (Postgres-cached), persist one provenance row per chunk in Postgres,
    and sync one Qdrant point per unique content_hash."""
    print(f"\nEmbedding {len(chunks)} chunks...")
    chunk_store = ChunkStore(engine)
    embedder = Embedder(chunk_store=chunk_store)
    texts = [chunk.page_content for chunk in chunks]

    embeddings, content_hashes = embedder.embed_with_hashes(texts)
    print(f"  ✓ Embedded {len(embeddings)} chunks (dim={len(embeddings[0])})")

    rows = [
        Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model=embedder.model,
            embedding=embedding,
            metadata_=chunk.metadata,
        )
        for chunk, embedding, content_hash in zip(chunks, embeddings, content_hashes)
    ]

    seen: set[tuple[str, str]] = set()
    unique_rows = []
    duplicates = 0
    for row in rows:
        key = (row.content_hash, json.dumps(row.metadata_, sort_keys=True, default=str))
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique_rows.append(row)
    if duplicates:
        print(f"  ⊘ Dropped {duplicates} duplicate chunk row(s) (same content_hash + metadata within this run)")
    rows = unique_rows

    print(f"\nStoring {len(rows)} chunk rows in Postgres...")
    batch_size = 100
    with tqdm(total=len(rows), desc="Inserting", unit="row") as pbar:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            chunk_store.insert_chunks(batch)
            pbar.update(len(batch))
    print(f"  ✓ Inserted {len(rows)} rows into 'chunks'")

    qdrant_store = QdrantVectorStore(vector_size=len(embeddings[0]))
    new_points = chunk_store.sync_to_qdrant(rows, qdrant_store)
    print(f"  ✓ Synced Qdrant: {new_points} new point(s) into '{qdrant_store.collection_name}' "
          f"({len(rows) - new_points} content-hash cache hits)")


def main():
    """Run full ingestion pipeline with optional filetype filtering."""
    parser = argparse.ArgumentParser(
        description="Ingest medical documents: load → chunk → embed → Qdrant push",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ingest_documents.py               # All filetypes from dummy_docs
  python scripts/ingest_documents.py --filetype=pdf
  python scripts/ingest_documents.py --filetype=pdf,json
  python scripts/ingest_documents.py --filetype=csv,xlsx
        """,
    )
    parser.add_argument(
        "--filetype",
        default="json,pdf,csv",
        help="Comma-separated list of filetypes to ingest (json, pdf, csv, xlsx). Default: all",
    )
    args = parser.parse_args()

    filetypes = {ft.strip().lower() for ft in args.filetype.split(",")}
    valid = {"json", "pdf", "csv", "xlsx"}
    if not filetypes <= valid:
        print(f"✗ Invalid filetype(s): {filetypes - valid}. Valid: {valid}")
        sys.exit(1)

    print("=" * 60)
    print("MEDICAL DOCUMENT INGESTION PIPELINE")
    print(f"Filetypes: {', '.join(sorted(filetypes))}")
    print("=" * 60)

    all_documents = []

    if "json" in filetypes:
        all_documents.extend(ingest_json_documents())
    if "pdf" in filetypes:
        all_documents.extend(ingest_pdf_documents())
    if "csv" in filetypes or "xlsx" in filetypes:
        all_documents.extend(ingest_csv_excel_documents())

    if not all_documents:
        print("\n✗ No documents ingested!")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(all_documents)} documents loaded")
    print(f"{'=' * 60}")

    init_db()
    chunk_store = ChunkStore(engine)
    all_documents = filter_seen_documents(all_documents, chunk_store)

    if not all_documents:
        print("\n✗ All documents already ingested, nothing new to process!")
        sys.exit(0)

    chunks = chunk_documents(all_documents)

    print(f"\nIngestion Summary:")
    print(f"  Documents: {len(all_documents)}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")

    embed_and_store(chunks)

    return all_documents, chunks


if __name__ == "__main__":
    main()
