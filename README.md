# Medical Ingestion

Learning project for vector data ingestion, parsing, RAG pipelines, and database connections.

## Goals

Build modular, reusable components that can be:

- **Called separately** — Each ingestion, parsing, RAG, or DB pipeline is a standalone callable module
- **Composed together** — Pipelines can be chained and mixed to build complex workflows
- **Tested independently** — Each component has its own test suite and can be validated in isolation

## Architecture

```text
ingestion/          — data extraction & parsing (implemented)
  ├── loaders/      — PDFLoaderService, TextLoaderService, ExcelCSVLoaderService,
  │                   JSONLoaderService, LoaderFactory
  ├── chunker.py    — ChunkerConfig, ChunkerService (Document -> Chunk)
  ├── pmc_fetcher.py, pmc_json_converter.py — PMC ingestion
  └── *_extraction.py — standalone reference scripts, superseded by loaders/

models/             — Pydantic data models (implemented)
  ├── documents.py  — Document, Metadata
  ├── rag.py        — RAGQuery, RAGResponse, RetrievedContext
  └── vectors.py    — EmbeddingRequest, EmbeddingResult, Vector

scripts/
  └── ingest_documents.py — wires loaders + chunker into one pipeline

embeddings/, vector_db/, rag/, storage/  — planned, not yet implemented
```

## Configuration

Settings are loaded from environment with **shell env priority over .env**:

```bash
# Copy template
cp .env.example .env

# Edit .env with your keys
# OR set env vars directly:
export OPENROUTER_API_KEY=your_key
export CHAT_MODEL=openrouter/model-name
```

See [.env.example](.env.example) for all available settings.

## Usage

### Implemented — loaders + chunker

```python
from ingestion.loaders import LoaderFactory
from ingestion.chunker import ChunkerConfig, ChunkerService

# Load documents (PDF, text, Excel/CSV, or JSON)
loader = LoaderFactory.pdf_loader("docs/")
docs = loader.load()

# Chunk for RAG
config = ChunkerConfig(chunk_size=512, chunk_overlap=100)
chunker = ChunkerService(config=config)
chunks = chunker.chunk(docs)
```

### Planned — embeddings, vector storage, RAG query (not yet implemented)

```python
from ingestion.pipeline import IngestionPipeline
from rag.pipeline import RAGPipeline

# Ingest and store
ingest = IngestionPipeline()
ingest.run(source="docs/", vector_db="chroma")

# Query with RAG
rag = RAGPipeline()
answer = rag.query("What does the paper say about X?")
```

## Requirements

### System

- Python 3.13+
- Docker + Docker Compose (for Postgres + pgAdmin + Qdrant)
- `uv` package manager (for Python deps)

### Python Dependencies

Managed via `uv sync` from pyproject.toml. Key packages:

- `psycopg[binary]` — Postgres adapter + psql CLI access
- `sqlalchemy`, `sqlmodel` — ORM for relational data
- `qdrant-client` — Vector DB client
- `langchain*` — Document loading, chunking, RAG
- `sentence-transformers` — Embeddings
- `structlog` — Structured logging

## Development

```bash
# Install dependencies
uv sync

# Start Postgres + pgAdmin
./scripts/start_postgres.sh
# Access pgAdmin at http://localhost:5050 (admin@example.com / admin)

# Query via psql CLI
psql -U postgres -d medical_ingestion -c "SELECT * FROM chunks LIMIT 5;"

# Run tests
uv run pytest

# Run a pipeline
uv run main.py
```

## Learning Outcomes

- Vector embeddings and similarity search
- Document parsing and chunking strategies
- RAG architecture and retrieval strategies
- Database integration (vector + relational)
- Pipeline composition and orchestration
