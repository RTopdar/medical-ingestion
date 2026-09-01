import re
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from settings import settings


class ChunkerConfig(BaseModel):
    """Configuration for text chunking."""

    chunk_size: int = Field(
        default=settings.chunk_size,
        description="Target chunk size in characters (400-800 per spec)",
    )
    chunk_overlap: int = Field(
        default=settings.chunk_overlap,
        description="Overlap between chunks in characters (100-200 per spec)",
    )


class ChunkerService(BaseModel):
    """Convert Documents to chunked Documents using RecursiveCharacterTextSplitter,
    with optional markdown header pre-pass and section-context injection."""

    config: ChunkerConfig = Field(default_factory=ChunkerConfig)

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def _has_markdown_headers(text: str) -> bool:
        """Check if text contains markdown-style headers (#, ##, ###)."""
        return bool(re.search(r"^#{1,6}\s", text, re.MULTILINE))

    @staticmethod
    def _split_by_markdown_headers(text: str) -> list[Document]:
        """Split text by markdown headers, return Documents with section metadata."""
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        )
        md_splits = splitter.split_text(text)
        docs = []
        for split in md_splits:
            section = " > ".join(split.metadata.values()) if split.metadata else None
            docs.append(Document(page_content=split.page_content, metadata={"section": section}))
        return docs

    def _inject_section_context(self, chunks: list[Document]) -> list[Document]:
        """Prepend section to page_content if section metadata exists and is non-null."""
        for chunk in chunks:
            section = chunk.metadata.get("section")
            if section:
                chunk.page_content = f"[Section: {section}]\n{chunk.page_content}"
        return chunks

    def chunk(self, documents: list[Document]) -> list[Document]:
        """Split Documents into smaller Documents, metadata propagated by LangChain.

        Process: for each doc, check for markdown headers. If found, pre-split by headers
        (preserving section hierarchy in metadata), then chunk each section. Otherwise,
        chunk directly. Finally, inject section context into page_content for embedding.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            add_start_index=True,
        )

        all_chunks = []
        for doc in documents:
            if self._has_markdown_headers(doc.page_content):
                md_docs = self._split_by_markdown_headers(doc.page_content)
                for md_doc in md_docs:
                    merged_metadata = {**doc.metadata, **md_doc.metadata}
                    md_doc.metadata = merged_metadata
                chunks = splitter.split_documents(md_docs)
            else:
                chunks = splitter.split_documents([doc])
            all_chunks.extend(chunks)

        return self._inject_section_context(all_chunks)


def _load_all_documents() -> list[Document]:
    """Load Documents from every loader source, skipping sources with no data."""
    from ingestion.loaders import LoaderFactory

    documents = []
    sources = [
        ("JSON", lambda: LoaderFactory.json_loader("dummy_docs").load(), FileNotFoundError),
        ("PDF", lambda: LoaderFactory.pdf_loader("dummy_docs").load(), FileNotFoundError),
        (
            "Excel/CSV",
            lambda: LoaderFactory.excel_csv_loader("dummy_docs").load(),
            FileNotFoundError,
        ),
        ("Text", lambda: LoaderFactory.text_loader("dummy_docs").load(), FileNotFoundError),
        # SQL raises DB-layer errors beyond a missing file, so it needs a broader catch.
        ("SQL", lambda: LoaderFactory.sql_loader(settings.sqlite_db_path).load(), Exception),
    ]

    for name, load, expected_error in sources:
        try:
            documents += load()
        except expected_error as e:
            print(f"  SKIPPED {name}: {e}")

    return documents


def main():
    """Chunk Documents from every loader source and print one sample chunk per source type."""
    documents = _load_all_documents()
    print(f"\nLoaded {len(documents)} documents from all sources")

    chunks = ChunkerService().chunk(documents)
    print(f"Created {len(chunks)} chunks total (showing one sample per source_type)\n")

    seen_source_types = set()
    for chunk in chunks:
        source_type = chunk.metadata.get("source_type")
        if source_type in seen_source_types:
            continue
        seen_source_types.add(source_type)

        print("=" * 70)
        print(f"SAMPLE CHUNK  (source_type={source_type})")
        print("=" * 70)
        print(f"content ({len(chunk.page_content)} chars):")
        print("  " + chunk.page_content.replace("\n", "\n  "))
        print(f"\nmetadata ({len(chunk.metadata)} keys):")
        key_width = max((len(k) for k in chunk.metadata), default=0)
        for k, v in chunk.metadata.items():
            print(f"  {k.ljust(key_width)} : {v!r}")
        print()


if __name__ == "__main__":
    main()
