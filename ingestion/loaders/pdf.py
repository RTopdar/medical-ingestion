from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader
from docling.document_converter import DocumentConverter

from ingestion.loaders.base import LoaderConfig, clean_text


class PDFLoaderService(BaseModel):
    """Load PDFs via Docling and return LangChain Documents with structured metadata."""

    config: LoaderConfig

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def _extract_section_path_from_document(docling_doc) -> dict[str, list[str] | None]:
        """Extract hierarchical section path with heading levels from Docling document.

        Returns a dict with keys:
        - 'section_path': list of heading texts in hierarchical order [H1, H2, H3, ...] or None
        - 'section_text': flattened section string for display (e.g., "H1 > H2 > H3")
        """
        section_path = []

        # Track headings by level
        headings_by_level = {}

        def traverse_body(body_item):
            """Recursively traverse document body to collect headings with levels."""
            if not hasattr(body_item, 'children'):
                return

            for child in body_item.children:
                # Dereference if it's a reference
                if hasattr(child, 'get_ref'):
                    child = child.get_ref()

                # Check if this is a heading
                if hasattr(child, 'label') and child.label and 'heading' in child.label.lower():
                    if hasattr(child, 'level'):
                        level = child.level
                        if hasattr(child, 'text'):
                            text = child.text.strip()
                            # Update headings_by_level: keep this level and remove deeper levels
                            headings_by_level[level] = text
                            # Remove all deeper levels
                            levels_to_remove = [l for l in headings_by_level if l > level]
                            for l in levels_to_remove:
                                del headings_by_level[l]

                # Recurse into children
                traverse_body(child)

        # Try to extract from Docling document object
        if hasattr(docling_doc, 'body'):
            traverse_body(docling_doc.body)

        # Build section_path from collected headings
        if headings_by_level:
            sorted_levels = sorted(headings_by_level.keys())
            section_path = [headings_by_level[level] for level in sorted_levels]

        return {
            'section_path': section_path if section_path else None,
            'section_text': ' > '.join(section_path) if section_path else None
        }

    def load(self) -> list[Document]:
        """Load all PDFs from directory and return Documents."""
        pdf_files = sorted(self.config.source_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files in {self.config.source_dir}")

        documents = []
        for pdf_path in pdf_files:
            # Use raw Docling converter to get full document structure with heading levels
            raw_docling_doc = None
            try:
                converter = DocumentConverter()
                doc_result = converter.convert(str(pdf_path))
                raw_docling_doc = doc_result.document
            except Exception:
                # Fall back to LangChain loader if raw conversion fails
                pass

            # Extract section path from raw Docling document if available
            section_path_data = {}
            if raw_docling_doc:
                section_path_data = self._extract_section_path_from_document(raw_docling_doc)

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
                    "section_path": None,
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
                        # Use extracted section_path if available, otherwise fall back to flattened headings
                        if section_path_data.get('section_path'):
                            metadata["section_path"] = section_path_data['section_path']
                            metadata["section"] = section_path_data['section_text']
                        else:
                            # Fallback: treat headings list as ordered path
                            metadata["section"] = " > ".join(dl_meta["headings"])
                            metadata["section_path"] = dl_meta["headings"] if dl_meta["headings"] else None

                documents.append(Document(page_content=content, metadata=metadata))

        return documents
