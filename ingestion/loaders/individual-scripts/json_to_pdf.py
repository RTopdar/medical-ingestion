"""Render pmc_documents.json entries to real PDF files for exercising the PDF ingestion path."""

import json
import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def safe_filename(title: str | None, index: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9 -]", "", title or "")[:60].strip().replace(" ", "_")
    return f"{index:03d}_{slug or 'untitled'}.pdf"


def doc_to_pdf(doc: dict, output_path: Path) -> None:
    styles = getSampleStyleSheet()
    pdf = SimpleDocTemplate(str(output_path), pagesize=LETTER)

    story = [
        Paragraph(doc.get("title") or "Untitled", styles["Title"]),
        Spacer(1, 12),
    ]

    authors = ", ".join(a["name"] for a in doc.get("authors", []) if a.get("name"))
    if authors:
        story.append(Paragraph(f"Authors: {authors}", styles["Normal"]))

    pub = doc.get("publication_info", {})
    if pub.get("journal"):
        story.append(
            Paragraph(
                f"Journal: {pub['journal']} ({pub.get('publication_date', 'n.d.')})",
                styles["Normal"],
            )
        )
    story.append(Spacer(1, 12))

    for paragraph in doc["content"].split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            story.append(Paragraph(paragraph, styles["Normal"]))
            story.append(Spacer(1, 8))

    pdf.build(story)


def convert_all(
    json_path: str | Path = "dummy_docs/pmc_documents.json", output_dir: str | Path = "data/pdf"
) -> list[str]:
    docs = json.loads(Path(json_path).read_text(encoding="utf-8"))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for i, doc in enumerate(docs, 1):
        out_path = out_dir / safe_filename(doc["title"], i)
        try:
            doc_to_pdf(doc, out_path)
            written.append(str(out_path))
            print(f"  [{i}/{len(docs)}] {out_path.name}")
        except Exception as e:
            print(f"  [{i}/{len(docs)}] FAILED: {e}")

    print(f"\nWrote {len(written)}/{len(docs)} PDFs to {out_dir}")
    return written


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "dummy_docs/pmc_documents.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/pdf"
    convert_all(json_path, output_dir)
