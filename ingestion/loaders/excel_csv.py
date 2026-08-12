from pathlib import Path

from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader

from ingestion.loaders.base import LoaderConfig, clean_text


class ExcelCSVLoaderService(BaseModel):
    """Load Excel and CSV files using Unstructured for intelligent structure extraction."""

    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    def load(self) -> list[Document]:
        """Load all .csv and .xlsx files from directory and return Documents."""
        documents = []

        for csv_path in sorted(self.config.source_dir.glob("*.csv")):
            documents.extend(self._load(csv_path, source_type="csv"))

        for excel_path in sorted(self.config.source_dir.glob("*.xlsx")):
            documents.extend(self._load(excel_path, source_type="excel"))

        if not documents:
            raise FileNotFoundError(f"No CSV or Excel files in {self.config.source_dir}")

        return documents

    def _load(self, file_path: Path, source_type: str) -> list[Document]:
        """Load a single CSV/Excel file via Unstructured, preserving its native metadata."""
        loader = UnstructuredLoader(file_path=str(file_path))
        langchain_docs = loader.load()
        documents = []

        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            if self.config.clean_text:
                content = clean_text(content)

            metadata = dict(lc_doc.metadata)
            metadata["source"] = str(file_path)
            metadata["source_type"] = source_type
            metadata["title"] = file_path.stem
            metadata["tags"] = [source_type, file_path.stem]

            documents.append(Document(page_content=content, metadata=metadata))

        return documents
