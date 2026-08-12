import json
from pathlib import Path

from pydantic import BaseModel
from langchain_core.documents import Document

from ingestion.loaders.base import LoaderConfig, clean_text


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
                content = clean_text(content)

            title = item.get("title") or item.get("id") or item.get("name", "Untitled")
            doc_id = item.get("id", "")

            flat_metadata = self._flatten_metadata(item)

            metadata = {
                "source": str(json_path),
                "source_type": "json",
                "title": title,
                "id": doc_id,
                "document_type": item.get("document_type", "json"),
                "raw_json_keys": list(item.keys()),
                "nested_metadata": flat_metadata,
            }

            if "patient_info" in item:
                metadata["patient_mrn"] = item["patient_info"].get("mrn")
                metadata["patient_name"] = item["patient_info"].get("name")
                metadata["patient_age"] = item["patient_info"].get("age")

            if "clinical_data" in item:
                metadata["diagnoses"] = [
                    d.get("description") for d in item["clinical_data"].get("diagnoses", [])
                ]
                metadata["medications"] = [
                    m.get("name") for m in item["clinical_data"].get("medications", [])
                ]

            if "provider" in item:
                metadata["provider_name"] = item["provider"].get("name")
                metadata["provider_specialty"] = item["provider"].get("specialty")

            if "surgical_data" in item:
                metadata["procedure"] = item["surgical_data"].get("procedure")
                metadata["surgeon"] = item["surgical_data"].get("surgical_team", {}).get("surgeon")

            if "publication_info" in item:
                pub = item["publication_info"]
                metadata["journal"] = pub.get("journal")
                metadata["publication_date"] = pub.get("publication_date")
                metadata["volume"] = pub.get("volume")
                metadata["issue"] = pub.get("issue")

            if "authors" in item:
                metadata["authors"] = [a.get("name") for a in item["authors"]]
                metadata["author_affiliations"] = [
                    a.get("affiliation") for a in item["authors"] if a.get("affiliation")
                ]

            if "article_metadata" in item:
                metadata["keywords"] = item["article_metadata"].get("keywords", [])

            if "research_data" in item:
                metadata["study_type"] = item["research_data"].get("study_type")
                metadata["sample_size"] = item["research_data"].get("sample_size")

            if "source" in item and isinstance(item["source"], dict):
                metadata["external_source_type"] = item["source"].get("type")
                metadata["external_source_url"] = item["source"].get("url")

            tags = item.get("tags", [])
            if not tags:
                tags = [item.get("document_type", "json"), json_path.stem]
            metadata["tags"] = tags

            documents.append(Document(page_content=content, metadata=metadata))

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
                items.extend(JSONLoaderService._flatten_metadata(v, new_key, sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    items.append((new_key, json.dumps(v)))
                else:
                    items.append((new_key, ", ".join(str(i) for i in v)))
            else:
                items.append((new_key, v))

        return dict(items)
