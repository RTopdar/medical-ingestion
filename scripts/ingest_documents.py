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

from logging_config import get_logger
from ingestion.chunker import ChunkerService
from ingestion.embedder import Embedder
from ingestion.loaders import LoaderFactory
from models.vectors import Chunk, IngestedDocument
from retrieval.bm25 import BM25Index
from storage.chunk_store import ChunkStore
from storage.postgres import engine, init_db
from vector_db import QdrantVectorStore

log = get_logger(__name__)


def ingest_json_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest JSON documents with rich metadata."""
    try:
        log.info("loading_json_documents", data_dir=data_dir)
        loader = LoaderFactory.json_loader(data_dir)
        docs = loader.load()
        log.info("loaded_json_documents", count=len(docs))

        for doc in docs[:1]:
            log.info(
                "sample_json_document",
                title=doc.metadata.get("title"),
                content_length=len(doc.page_content),
                metadata_keys=list(doc.metadata.keys()),
            )

        return docs
    except FileNotFoundError:
        log.warning("json_files_not_found", data_dir=data_dir)
        return []


def ingest_pdf_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest PDF documents (Docling extraction)."""
    try:
        log.info("loading_pdf_documents", data_dir=data_dir)
        loader = LoaderFactory.pdf_loader(data_dir)
        docs = loader.load()
        log.info("loaded_pdf_documents", count=len(docs))
        return docs
    except Exception as e:
        log.warning("pdf_load_error", data_dir=data_dir, error=str(e))
        return []


def ingest_csv_excel_documents(data_dir: str | Path = "dummy_docs") -> list[Document]:
    """Ingest CSV and Excel documents."""
    try:
        log.info("loading_csv_excel_documents", data_dir=data_dir)
        loader = LoaderFactory.excel_csv_loader(data_dir)
        docs = loader.load()
        log.info("loaded_csv_excel_documents", count=len(docs))
        return docs
    except Exception as e:
        log.warning("csv_excel_load_error", data_dir=data_dir, error=str(e))
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
        log.info("filtered_seen_documents", skipped=skipped)
    return new_documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Chunk documents for RAG."""
    log.info("chunking_documents", doc_count=len(documents))
    chunker = ChunkerService()
    with tqdm(total=len(documents), desc="Chunking", unit="doc") as pbar:
        chunks = chunker.chunk(documents)
        pbar.update(len(documents))
    log.info("chunked_documents", chunk_count=len(chunks))
    return chunks


def embed_and_store(chunks: list[Document]) -> None:
    """Embed chunks (Postgres-cached), persist one provenance row per chunk in Postgres,
    and sync one Qdrant point per unique content_hash."""
    log.info("embedding_chunks", chunk_count=len(chunks))
    chunk_store = ChunkStore(engine)
    embedder = Embedder(chunk_store=chunk_store)
    texts = [chunk.page_content for chunk in chunks]

    embeddings, content_hashes = embedder.embed_with_hashes(texts)
    log.info("embedded_chunks", count=len(embeddings), dimension=len(embeddings[0]))

    rows = [
        Chunk(
            content_hash=content_hash,
            text=chunk.page_content,
            model=embedder.model,
            embedding=embedding,
            metadata_=chunk.metadata,
            section_path=chunk.metadata.get("section_path"),
            page_number=chunk.metadata.get("page_number"),
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
        log.info("dropped_duplicate_rows", count=duplicates)
    rows = unique_rows

    log.info("storing_chunk_rows", row_count=len(rows))
    batch_size = 100
    with tqdm(total=len(rows), desc="Inserting", unit="row") as pbar:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            chunk_store.insert_chunks(batch)
            pbar.update(len(batch))
    log.info("inserted_chunk_rows", row_count=len(rows))

    qdrant_store = QdrantVectorStore(vector_size=len(embeddings[0]))
    new_points = chunk_store.sync_to_qdrant(rows, qdrant_store)
    log.info(
        "synced_qdrant",
        new_points=new_points,
        collection=qdrant_store.collection_name,
        cache_hits=len(rows) - new_points,
    )


def rebuild_bm25_index(chunk_store: ChunkStore) -> None:
    """Rebuild BM25 over the full chunk corpus in Postgres, not just this run's new
    chunks — bm25s has no incremental-add API, so this always runs on every invocation,
    even when filter_seen_documents finds nothing new to embed."""
    all_chunks = chunk_store.get_all_chunks()
    bm25_index = BM25Index()
    bm25_index.build(all_chunks)
    bm25_index.save()
    log.info("built_bm25_index", doc_count=len(bm25_index.corpus))


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
        log.error("invalid_filetypes", invalid=filetypes - valid, valid=valid)
        sys.exit(1)

    log.info("starting_ingestion_pipeline", filetypes=sorted(filetypes))

    all_documents = []

    if "json" in filetypes:
        all_documents.extend(ingest_json_documents())
    if "pdf" in filetypes:
        all_documents.extend(ingest_pdf_documents())
    if "csv" in filetypes or "xlsx" in filetypes:
        all_documents.extend(ingest_csv_excel_documents())

    if not all_documents:
        log.error("no_documents_ingested")
        sys.exit(1)

    log.info("documents_loaded", count=len(all_documents))

    init_db()
    chunk_store = ChunkStore(engine)
    all_documents = filter_seen_documents(all_documents, chunk_store)

    if not all_documents:
        log.info("all_documents_already_ingested")
        rebuild_bm25_index(chunk_store)
        sys.exit(0)

    chunks = chunk_documents(all_documents)

    avg_chunk_size = sum(len(c.page_content) for c in chunks) // len(chunks) if chunks else 0
    log.info(
        "ingestion_summary",
        doc_count=len(all_documents),
        chunk_count=len(chunks),
        avg_chunk_size=avg_chunk_size,
    )

    embed_and_store(chunks)
    rebuild_bm25_index(chunk_store)

    return all_documents, chunks


if __name__ == "__main__":
    main()
