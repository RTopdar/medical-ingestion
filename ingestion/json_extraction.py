import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document


def load_json_documents(json_dir: str | Path = "dummy_docs") -> List[Document]:
    """Load all JSON files from directory, treating each top-level object
    (or each item in a top-level list) as one Document.

    Args:
        json_dir: Directory containing JSON files

    Returns:
        List of LangChain Document objects with raw JSON fields as metadata
    """
    json_dir = Path(json_dir)
    documents = []

    if not json_dir.exists():
        raise FileNotFoundError(f"JSON directory not found: {json_dir}")

    json_files = sorted(json_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")

    for json_path in json_files:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data if isinstance(data, list) else [data]

        for item in items:
            content = (
                item.get("content")
                or item.get("text")
                or item.get("body")
                or item.get("description")
                or ""
            )

            metadata = dict(item)
            metadata.pop("content", None)
            metadata["file"] = json_path.name
            metadata["source_file"] = str(json_path)
            metadata["format"] = "json"

            documents.append(Document(page_content=content, metadata=metadata))

    return documents


if __name__ == "__main__":
    print("=" * 80)
    print("JSON EXTRACTION")
    print("=" * 80)
    try:
        json_docs = load_json_documents()
        print(f"Loaded {len(json_docs)} elements from JSON files\n")

        for i, doc in enumerate(json_docs[:3]):
            print(f"{'='*80}")
            print(f"Element #{i+1}")
            print(f"{'='*80}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content length: {len(doc.page_content)} chars")
            print(f"\nContent:\n{doc.page_content[:500]}")
            if len(doc.page_content) > 500:
                print(f"... [{len(doc.page_content) - 500} more chars]\n")
            else:
                print()
    except FileNotFoundError as e:
        print(f"No JSON files to demonstrate: {e}\n")
