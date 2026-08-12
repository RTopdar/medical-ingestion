import re
from pathlib import Path

from pydantic import BaseModel, Field


class LoaderConfig(BaseModel):
    """Configuration for document loaders."""
    source_dir: Path = Field(..., description="Directory containing source files")
    clean_text: bool = Field(default=True, description="Apply text cleaning")


def clean_text(text: str) -> str:
    """Clean extracted text from encoding issues, whitespace, and artifacts."""
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
