from pydantic import BaseModel
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

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
        """Load all PDFs from directory and return Documents.

        Uses a single Docling `DocumentConverter().convert()` pass per file, then
        chunks that same parsed document directly with `HybridChunker` (the same
        chunker `DoclingLoader` uses internally). This avoids parsing each PDF
        twice. The full hierarchical section path (ancestor chain across heading
        levels, e.g. Part > Chapter > Section) is derived once per document from
        the parsed structure and applied to every chunk from that document —
        `HybridChunker`'s own per-chunk `headings` metadata only carries the
        immediate heading, not the full ancestor chain, so it cannot replace this
        traversal.
        """
        pdf_files = sorted(self.config.source_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files in {self.config.source_dir}")

        chunker = HybridChunker()
        documents = []
        for pdf_path in pdf_files:
            converter = DocumentConverter()
            doc_result = converter.convert(str(pdf_path))
            docling_doc = doc_result.document

            section_path_data = self._extract_section_path_from_document(docling_doc)

            for chunk in chunker.chunk(docling_doc):
                content = chunker.contextualize(chunk=chunk)
                if self.config.clean_text:
                    content = clean_text(content)

                metadata = {
                    "source": str(pdf_path),
                    "source_type": "pdf",
                    "title": pdf_path.stem,
                    "tags": ["pdf", pdf_path.stem],
                    "page_number": None,
                    "element_type": "text",
                    "section": section_path_data.get('section_text'),
                    "section_path": section_path_data.get('section_path'),
                    "bbox": None,
                    "char_span": None,
                    "content_layer": None,
                }

                chunk_meta = chunk.meta.export_json_dict()
                doc_items = chunk_meta.get("doc_items") or []
                if doc_items:
                    first_item = doc_items[0]
                    prov = (first_item.get("prov") or [None])[0]
                    if prov:
                        metadata["page_number"] = prov.get("page_no")
                        metadata["bbox"] = prov.get("bbox")
                        metadata["char_span"] = prov.get("charspan")
                    metadata["element_type"] = first_item.get("label", "text")
                    metadata["content_layer"] = first_item.get("content_layer")

                documents.append(Document(page_content=content, metadata=metadata))

        return documents
