import uuid
from pathlib import Path

from pydantic import BaseModel
from langchain_unstructured import UnstructuredLoader

from models.documents import Document, Metadata
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
            documents.extend(self._load_csv(csv_path))

        for excel_path in sorted(self.config.source_dir.glob("*.xlsx")):
            documents.extend(self._load_excel(excel_path))

        if not documents:
            raise FileNotFoundError(
                f"No CSV or Excel files in {self.config.source_dir}"
            )

        return documents

    def _load_csv(self, csv_path: Path) -> list[Document]:
        """Load single CSV file using Unstructured."""
        loader = UnstructuredLoader(file_path=str(csv_path))
        langchain_docs = loader.load()
        documents = []

        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            if self.config.clean_text:
                content = clean_text(content)

            extra = {
                "element_type": lc_doc.metadata.get("category", "text"),
            }

            metadata = Metadata(
                source=str(csv_path),
                source_type="csv",
                tags=["csv", csv_path.stem],
                extra=extra,
            )

            doc = Document(
                id=str(uuid.uuid4()),
                content=content,
                title=csv_path.stem,
                metadata=metadata,
            )
            documents.append(doc)

        return documents

    def _load_excel(self, excel_path: Path) -> list[Document]:
        """Load Excel file using Unstructured (handles multiple sheets)."""
        loader = UnstructuredLoader(file_path=str(excel_path))
        langchain_docs = loader.load()
        documents = []

        for lc_doc in langchain_docs:
            content = lc_doc.page_content
            if self.config.clean_text:
                content = clean_text(content)

            extra = {
                "element_type": lc_doc.metadata.get("category", "text"),
            }

            metadata = Metadata(
                source=str(excel_path),
                source_type="excel",
                tags=["excel", excel_path.stem],
                extra=extra,
            )

            doc = Document(
                id=str(uuid.uuid4()),
                content=content,
                title=excel_path.stem,
                metadata=metadata,
            )
            documents.append(doc)

        return documents
