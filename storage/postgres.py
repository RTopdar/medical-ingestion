"""Postgres engine/session setup for Chunk/FailedEmbedding/IngestedDocument tables.

Mirrors storage/sql.py's SQLLoaderService pattern (SQLModel + Session + select),
just pointed at Postgres instead of sqlite.
"""

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from settings import settings

engine: Engine = create_engine(settings.postgres_dsn)


def init_db() -> None:
    """Create all SQLModel tables (Chunk, FailedEmbedding, IngestedDocument) if missing."""
    SQLModel.metadata.create_all(engine)
