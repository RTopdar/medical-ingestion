import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
    """Convert Documents to chunked Documents using RecursiveCharacterTextSplitter."""

    config: ChunkerConfig = Field(default_factory=ChunkerConfig)

    class Config:
        arbitrary_types_allowed = True

    def chunk(self, documents: list[Document]) -> list[Document]:
        """Split Documents into smaller Documents, metadata propagated by LangChain."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            add_start_index=True,
        )
        return splitter.split_documents(documents)


def _load_all_documents() -> list[Document]:
    """Load Documents from every loader source, skipping sources with no data."""
    from ingestion.loaders import LoaderFactory

    documents = []

    try:
        documents += LoaderFactory.json_loader("dummy_docs").load()
    except FileNotFoundError as e:
        print(f"  ⊘ JSON: {e}")

    try:
        documents += LoaderFactory.pdf_loader("dummy_docs").load()
    except FileNotFoundError as e:
        print(f"  ⊘ PDF: {e}")

    try:
        documents += LoaderFactory.excel_csv_loader("dummy_docs").load()
    except FileNotFoundError as e:
        print(f"  ⊘ Excel/CSV: {e}")

    try:
        documents += LoaderFactory.text_loader("dummy_docs").load()
    except FileNotFoundError as e:
        print(f"  ⊘ Text: {e}")

    try:
        documents += LoaderFactory.sql_loader(settings.sqlite_db_path).load()
    except Exception as e:
        print(f"  ⊘ SQL: {e}")

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
