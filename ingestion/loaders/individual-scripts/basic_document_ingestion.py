from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)
from pathlib import Path
import glob


def load_text_file(file_path: str) -> list[Document]:
    """
    Load plain text file and return Document object.
    Ref: https://docs.langchain.com/oss/python/integrations/document_loaders/index

    Args:
        file_path (str): Path to text file to load

    Returns:
        list[Document]: List containing single Document with file content
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return [Document(page_content=content, metadata={"source": file_path})]


def ingest_single_file(
    file_path: str, chunk_size: int = 1000, chunk_overlap: int = 300
) -> list[Document]:
    """
    Ingest a single text file and return chunked Document objects.

    Args:
        file_path (str): The path to the file to be ingested.
        chunk_size (int): The size of each chunk in characters. Default is 1000.
        chunk_overlap (int): The number of characters to overlap between chunks. Default is 0.

    Returns:
        list[Document]: A list of Document objects containing chunked text.
    """
    documents = load_text_file(file_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs


def ingest_from_directory(
    directory_path: str, chunk_size: int = 1000, chunk_overlap: int = 3
) -> list[Document]:
    """
    Load all text files from a directory and return chunked Document objects.

    Args:
        directory_path (str): Path to directory containing text files.
        chunk_size (int): Size of each chunk in characters. Default is 1000.
        chunk_overlap (int): Overlap between chunks in characters. Default is 3.

    Returns:
        list[Document]: List of chunked Document objects from all files in directory.
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    file_paths = sorted(dir_path.glob("**/*.txt"))
    print(f"Found {len(file_paths)} .txt files in {dir_path}")
    if not file_paths:
        raise FileNotFoundError(f"No .txt files found in {dir_path}")

    all_docs = []
    for file_path in file_paths:
        if file_path.is_file():
            docs = ingest_single_file(
                str(file_path), chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            all_docs.extend(docs)

    return all_docs


def load_single_dummy_pubmed() -> list[Document]:
    """
    Load dummy PubMed data from dummy_docs/pubmed directory using TextLoader.

    Returns:
        list[Document]: List of Document objects from PubMed data.
    """
    dummy_file_path = "dummy_docs/pubmed/full_paper_diabetes.txt"
    return ingest_single_file(dummy_file_path)


if __name__ == "__main__":
    # Load all papers from directory
    dir_path = Path("dummy_docs/pubmed")
    file_paths = sorted(dir_path.glob("*.txt"))

    print("Files loaded:")
    for f in file_paths:
        print(f"  - {f.name}")

    docs = ingest_from_directory("dummy_docs/pubmed")
    print(f"\nTotal: {len(docs)} chunked documents from {len(file_paths)} files")
    print(f"\nFirst 3 documents:")
    for i, doc in enumerate(docs[:3]):
        print(f"\n--- Document {i+1} ---")
        print(f"Source: {doc.metadata['source'].split('/')[-1]}")
        print(f"Content: {doc.page_content[:150]}...")
