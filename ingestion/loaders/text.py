from pydantic import BaseModel
from langchain_core.documents import Document

from ingestion.loaders.base import LoaderConfig


class TextLoaderService(BaseModel):
    """Load plain text files and return LangChain Documents."""

    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    def load(self) -> list[Document]:
        """Load all .txt files from directory and return raw Documents (no chunking)."""
        txt_files = sorted(self.config.source_dir.glob("**/*.txt"))
        if not txt_files:
            raise FileNotFoundError(f"No .txt files in {self.config.source_dir}")

        documents = []
        for txt_path in txt_files:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {
                "source": str(txt_path),
                "source_type": "txt",
                "title": txt_path.stem,
                "tags": ["text", txt_path.stem],
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents
