from pathlib import Path
from typing import List
import uuid

from langchain_unstructured import UnstructuredLoader
from langchain_core.documents import Document


def load_csv_documents(csv_dir: str | Path = "dummy_docs") -> List[Document]:
    """Load all CSV files from directory using Unstructured for intelligent parsing.

    Unstructured extracts structure (headers, tables, relationships) from tabular data,
    making it better for RAG than naive row-by-row splitting.

    Args:
        csv_dir: Directory containing CSV files

    Returns:
        List of LangChain Document objects with structured metadata
    """
    csv_dir = Path(csv_dir)
    documents = []

    if not csv_dir.exists():
        raise FileNotFoundError(f"CSV directory not found: {csv_dir}")

    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {csv_dir}")

    for csv_path in csv_files:
        loader = UnstructuredLoader(file_path=str(csv_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata["file"] = csv_path.name
            doc.metadata["source_file"] = str(csv_path)
            doc.metadata["format"] = "csv"

            documents.append(doc)

    return documents


def load_excel_documents(excel_dir: str | Path = "dummy_docs") -> List[Document]:
    """Load all Excel files from directory using Unstructured for intelligent parsing.

    Unstructured handles multiple sheets, preserves table structure and headers,
    and extracts semantic relationships.

    Args:
        excel_dir: Directory containing Excel (.xlsx) files

    Returns:
        List of LangChain Document objects with structured metadata
    """
    excel_dir = Path(excel_dir)
    documents = []

    if not excel_dir.exists():
        raise FileNotFoundError(f"Excel directory not found: {excel_dir}")

    excel_files = sorted(excel_dir.glob("*.xlsx"))
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {excel_dir}")

    for excel_path in excel_files:
        loader = UnstructuredLoader(file_path=str(excel_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata["file"] = excel_path.name
            doc.metadata["source_file"] = str(excel_path)
            doc.metadata["format"] = "excel"

            documents.append(doc)

    return documents


if __name__ == "__main__":
    print("=" * 80)
    print("CSV EXTRACTION")
    print("=" * 80)
    try:
        csv_docs = load_csv_documents()
        print(f"Loaded {len(csv_docs)} elements from CSV files\n")

        for i, doc in enumerate(csv_docs[:3]):
            print(f"{'='*80}")
            print(f"Element #{i+1} (type: {doc.metadata.get('category', 'unknown')})")
            print(f"{'='*80}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content length: {len(doc.page_content)} chars")
            print(f"\nContent:\n{doc.page_content[:500]}")
            if len(doc.page_content) > 500:
                print(f"... [{len(doc.page_content) - 500} more chars]\n")
            else:
                print()
    except FileNotFoundError as e:
        print(f"No CSV files to demonstrate: {e}\n")

    print("\n" + "=" * 80)
    print("EXCEL EXTRACTION")
    print("=" * 80)
    try:
        excel_docs = load_excel_documents()
        print(f"Loaded {len(excel_docs)} elements from Excel files\n")

        for i, doc in enumerate(excel_docs[:3]):
            print(f"{'='*80}")
            print(f"Element #{i+1} (type: {doc.metadata.get('category', 'unknown')})")
            print(f"{'='*80}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content length: {len(doc.page_content)} chars")
            print(f"\nContent:\n{doc.page_content[:500]}")
            if len(doc.page_content) > 500:
                print(f"... [{len(doc.page_content) - 500} more chars]\n")
            else:
                print()
    except FileNotFoundError as e:
        print(f"No Excel files to demonstrate: {e}\n")
