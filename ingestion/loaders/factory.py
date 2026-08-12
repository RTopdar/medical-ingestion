from pathlib import Path

from ingestion.loaders.base import LoaderConfig
from ingestion.loaders.pdf import PDFLoaderService
from ingestion.loaders.text import TextLoaderService
from ingestion.loaders.excel_csv import ExcelCSVLoaderService
from ingestion.loaders.json_loader import JSONLoaderService
from ingestion.loaders.sql_loader import SQLDataLoaderService


class LoaderFactory:
    """Factory for creating loaders based on source type."""

    @staticmethod
    def pdf_loader(source_dir: str | Path, clean_text: bool = True) -> PDFLoaderService:
        """Create PDF loader."""
        config = LoaderConfig(source_dir=Path(source_dir), clean_text=clean_text)
        return PDFLoaderService(config=config)

    @staticmethod
    def text_loader(source_dir: str | Path) -> TextLoaderService:
        """Create text loader."""
        config = LoaderConfig(source_dir=Path(source_dir))
        return TextLoaderService(config=config)

    @staticmethod
    def excel_csv_loader(source_dir: str | Path) -> ExcelCSVLoaderService:
        """Create Excel/CSV loader."""
        config = LoaderConfig(source_dir=Path(source_dir))
        return ExcelCSVLoaderService(config=config)

    @staticmethod
    def json_loader(source_dir: str | Path, clean_text: bool = True) -> JSONLoaderService:
        """Create JSON loader."""
        config = LoaderConfig(source_dir=Path(source_dir), clean_text=clean_text)
        return JSONLoaderService(config=config)

    @staticmethod
    def sql_loader(db_path: str | Path) -> SQLDataLoaderService:
        """Create SQL loader for clinical trial records."""
        return SQLDataLoaderService(db_path=Path(db_path))
