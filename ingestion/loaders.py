import uuid
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from langchain_docling.loader import DoclingLoader
from langchain_unstructured import UnstructuredLoader

from models.documents import Document, Metadata


class LoaderConfig(BaseModel):
    """Configuration for document loaders."""
    source_dir: Path = Field(..., description="Directory containing source files")
    clean_text: bool = Field(default=True, description="Apply text cleaning")


class PDFLoaderService(BaseModel):
    """Load PDFs via Docling and convert to Pydantic Documents."""
    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    def load(self) -> list[Document]:
        """Load all PDFs from directory and return raw Documents"""
        pdf_files = sorted(self.config.source_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files in {self.config.source_dir}")

        documents = []
        for pdf_path in pdf_files:
            loader = DoclingLoader(file_path=str(pdf_path))
            langchain_docs = loader.load()

            for lc_doc in langchain_docs:
                # Clean text if enabled
                content = lc_doc.page_content
                if self.config.clean_text:
                    content = self._clean_text(content)

                # Extract PDF-specific metadata from Docling
                extra = {
                    "page_number": None,
                    "element_type": "text",
                    "section": None,
                    "bbox": None,
                    "char_span": None,
                    "content_layer": None,
                }

                if "dl_meta" in lc_doc.metadata:
                    dl_meta = lc_doc.metadata["dl_meta"]
                    if "doc_items" in dl_meta and dl_meta["doc_items"]:
                        first_item = dl_meta["doc_items"][0]
                        if "prov" in first_item and first_item["prov"]:
                            prov = first_item["prov"][0]
                            extra["page_number"] = prov.get("page_no")
                            extra["bbox"] = prov.get("bbox")
                            extra["char_span"] = prov.get("charspan")
                        extra["element_type"] = first_item.get("label", "text")
                        extra["content_layer"] = first_item.get("content_layer")

                    if "headings" in dl_meta:
                        extra["section"] = " > ".join(dl_meta["headings"])

                metadata = Metadata(
                    source=str(pdf_path),
                    source_type="pdf",
                    tags=["pdf", pdf_path.stem],
                    extra=extra,
                )

                doc = Document(
                    id=str(uuid.uuid4()),
                    content=content,
                    title=pdf_path.stem,
                    metadata=metadata,
                )
                documents.append(doc)

        return documents

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text from encoding issues, whitespace, and artifacts."""
        import re

        if not text:
            return ""

        text = str(text)
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        text = text.strip()

        return text


class TextLoaderService(BaseModel):
    """Load plain text files and convert to Pydantic Documents."""
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

            metadata = Metadata(
                source=str(txt_path),
                source_type="txt",
                tags=["text", txt_path.stem],
                extra={},
            )

            doc = Document(
                id=str(uuid.uuid4()),
                content=content,
                title=txt_path.stem,
                metadata=metadata,
            )
            documents.append(doc)

        return documents

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
                content = self._clean_text(content)

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
                content = self._clean_text(content)

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

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text from encoding issues, whitespace, and artifacts."""
        import re

        if not text:
            return ""

        text = str(text)
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        text = text.strip()

        return text


class JSONLoaderService(BaseModel):
    """Load JSON files with complex nested metadata extraction."""
    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    def load(self) -> list[Document]:
        """Load all .json files and extract max metadata."""
        json_files = sorted(self.config.source_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON files in {self.config.source_dir}")

        documents = []
        for json_path in json_files:
            documents.extend(self._load_json(json_path))

        return documents

    def _load_json(self, json_path: Path) -> list[Document]:
        """Load single JSON file with nested metadata preservation."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        items = data if isinstance(data, list) else [data]

        for item in items:
            # Extract content field (support multiple common field names)
            content = (
                item.get("content")
                or item.get("text")
                or item.get("body")
                or item.get("description")
                or ""
            )

            if not content:
                continue

            if self.config.clean_text:
                content = self._clean_text(content)

            # Extract title/id
            title = item.get("title") or item.get("id") or item.get("name", "Untitled")
            doc_id = item.get("id", str(uuid.uuid4()))

            # Flatten nested metadata while preserving structure
            flat_metadata = self._flatten_metadata(item)

            # Build extra metadata with rich nested info
            extra = {
                "document_type": item.get("document_type", "json"),
                "raw_json_keys": list(item.keys()),
                "nested_metadata": flat_metadata,
            }

            # Extract common fields
            if "patient_info" in item:
                extra["patient_mrn"] = item["patient_info"].get("mrn")
                extra["patient_name"] = item["patient_info"].get("name")
                extra["patient_age"] = item["patient_info"].get("age")

            if "clinical_data" in item:
                extra["diagnoses"] = [
                    d.get("description") for d in item["clinical_data"].get("diagnoses", [])
                ]
                extra["medications"] = [
                    m.get("name") for m in item["clinical_data"].get("medications", [])
                ]

            if "provider" in item:
                extra["provider_name"] = item["provider"].get("name")
                extra["provider_specialty"] = item["provider"].get("specialty")

            if "surgical_data" in item:
                extra["procedure"] = item["surgical_data"].get("procedure")
                extra["surgeon"] = item["surgical_data"].get("surgical_team", {}).get("surgeon")

            if "publication_info" in item:
                pub = item["publication_info"]
                extra["journal"] = pub.get("journal")
                extra["publication_date"] = pub.get("publication_date")
                extra["volume"] = pub.get("volume")
                extra["issue"] = pub.get("issue")

            if "authors" in item:
                extra["authors"] = [a.get("name") for a in item["authors"]]
                extra["author_affiliations"] = [
                    a.get("affiliation") for a in item["authors"] if a.get("affiliation")
                ]

            if "article_metadata" in item:
                extra["keywords"] = item["article_metadata"].get("keywords", [])

            if "research_data" in item:
                extra["study_type"] = item["research_data"].get("study_type")
                extra["sample_size"] = item["research_data"].get("sample_size")

            if "source" in item and isinstance(item["source"], dict):
                extra["external_source_type"] = item["source"].get("type")
                extra["external_source_url"] = item["source"].get("url")

            # Tags from document or auto-generate
            tags = item.get("tags", [])
            if not tags:
                tags = [item.get("document_type", "json"), json_path.stem]

            metadata = Metadata(
                source=str(json_path),
                source_type="json",
                tags=tags,
                extra=extra,
            )

            doc = Document(
                id=doc_id,
                content=content,
                title=title,
                metadata=metadata,
            )
            documents.append(doc)

        return documents

    @staticmethod
    def _flatten_metadata(obj: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flatten nested JSON to dot notation for queryable metadata."""
        items = []
        for k, v in obj.items():
            if k in ["content", "text", "body"]:
                continue

            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(
                    JSONLoaderService._flatten_metadata(v, new_key, sep).items()
                )
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    items.append((new_key, json.dumps(v)))
                else:
                    items.append((new_key, ", ".join(str(i) for i in v)))
            else:
                items.append((new_key, v))

        return dict(items)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text from encoding issues, whitespace, and artifacts."""
        import re

        if not text:
            return ""

        text = str(text)
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t\r")
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        text = text.strip()

        return text


class LoaderFactory:
    """Factory for creating loaders based on source type."""

    @staticmethod
    def pdf_loader(source_dir: str | Path, clean_text: bool = True) -> PDFLoaderService:
        """Create PDF loader."""
        config = LoaderConfig(source_dir=Path(source_dir), clean_text=clean_text)
        return PDFLoaderService(config=config)

    @staticmethod
    def text_loader(source_dir: str | Path) -> TextLoaderService:
        """Create text loader."""
        config = LoaderConfig(source_dir=Path(source_dir))
        return TextLoaderService(config=config)

    @staticmethod
    def excel_csv_loader(source_dir: str | Path) -> ExcelCSVLoaderService:
        """Create Excel/CSV loader."""
        config = LoaderConfig(source_dir=Path(source_dir))
        return ExcelCSVLoaderService(config=config)

    @staticmethod
    def json_loader(source_dir: str | Path, clean_text: bool = True) -> JSONLoaderService:
        """Create JSON loader."""
        config = LoaderConfig(source_dir=Path(source_dir), clean_text=clean_text)
        return JSONLoaderService(config=config)
