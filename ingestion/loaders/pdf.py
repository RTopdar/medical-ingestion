import uuid

from pydantic import BaseModel
from langchain_docling.loader import DoclingLoader

from models.documents import Document, Metadata
from ingestion.loaders.base import LoaderConfig, clean_text


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
                content = lc_doc.page_content
                if self.config.clean_text:
                    content = clean_text(content)

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
