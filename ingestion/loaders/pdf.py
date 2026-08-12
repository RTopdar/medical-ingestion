from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader

from ingestion.loaders.base import LoaderConfig, clean_text


class PDFLoaderService(BaseModel):
    """Load PDFs via Docling and return LangChain Documents with structured metadata."""

    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    def load(self) -> list[Document]:
        """Load all PDFs from directory and return Documents."""
        pdf_files = sorted(self.config.source_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files in {self.config.source_dir}")

        documents = []
        for pdf_path in pdf_files:
            loader = DoclingLoader(file_path=str(pdf_path))
            langchain_docs = loader.load()

            for lc_doc in langchain_docs:
                content = lc_doc.page_content
                if self.config.clean_text:
                    content = clean_text(content)

                metadata = {
                    "source": str(pdf_path),
                    "source_type": "pdf",
                    "title": pdf_path.stem,
                    "tags": ["pdf", pdf_path.stem],
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
                            metadata["page_number"] = prov.get("page_no")
                            metadata["bbox"] = prov.get("bbox")
                            metadata["char_span"] = prov.get("charspan")
                        metadata["element_type"] = first_item.get("label", "text")
                        metadata["content_layer"] = first_item.get("content_layer")

                    if "headings" in dl_meta:
                        metadata["section"] = " > ".join(dl_meta["headings"])

                documents.append(Document(page_content=content, metadata=metadata))

        return documents
