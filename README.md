# Medical Ingestion

Learning project for vector data ingestion, parsing, embeddings, storage, and RAG pipelines.

## Goals

Build modular, reusable components that can be:

- **Called separately** — Each ingestion, embedding, storage, or RAG pipeline is a standalone callable module
- **Composed together** — Pipelines can be chained and mixed to build complex workflows
- **Tested independently** — Each component has its own test suite and can be validated in isolation

## Architecture

```text
ingestion/                  — data extraction & parsing (✓ complete)
  ├── loaders/              — PDFLoaderService, TextLoaderService, ExcelCSVLoaderService,
  │                           JSONLoaderService, SQLDataLoaderService, LoaderFactory
  ├── chunker.py            — ChunkerConfig, ChunkerService (Document -> Document[])
  ├── embedder.py           — Embedder (text -> vector via OpenRouter, w/ retry + DLQ)
  ├── clinicaltrials_fetcher.py — ClinicalTrials.gov API v2 ingestion
  └── loaders/individual-scripts/ — reference/demo loaders (not used by scripts/)

models/                     — Pydantic + SQLModel data contracts (✓ complete)
  ├── documents.py          — docstring pointer (langchain_core.documents.Document now used)
  ├── vectors.py            — Chunk, FailedEmbedding, IngestedDocument (SQLModel table=True)
  ├── rag.py                — RAGQuery, RAGResponse, RetrievedContext (planned wiring)
  └── clinical_trial.py     — ClinicalTrial, Eligibility (SQLModel table=True)

storage/                    — relational persistence & cache (✓ complete)
  ├── postgres.py           — SQLAlchemy engine, init_db() (chunk provenance/cache/dedup)
  ├── chunk_store.py        — ChunkStore (embedding cache-check, bulk insert, Qdrant sync, DLQ)
  └── sql.py                — SQLLoaderService (clinical trials SQLite, ORM queries)

vector_db/                  — similarity search abstraction (✓ complete: Qdrant)
  ├── base.py               — VectorStore interface (upsert_one, find_by_hash)
  └── qdrant.py             — QdrantVectorStore (local Docker, persistent volume)

infrastructure/             — containerized services (✓ complete)
  ├── docker-compose.qdrant.yml — Qdrant v1.19+ (HTTP 6333 + gRPC 6334)
  ├── docker-compose.postgres.yml — Postgres 16 (5432)
  ├── scripts/start_qdrant.sh    — idempotent Qdrant startup
  └── scripts/start_postgres.sh  — idempotent Postgres startup

logging_config.py           — structlog JSON configuration (✓ complete)

scripts/
  ├── ingest_documents.py   — end-to-end load → chunk → embed → store → Qdrant sync
  └── seed_clinical_trials_db.py — fetch + seed clinical trials

rag/                        — retrieval + generation (planned, not yet wired)
```

## Configuration

Settings loaded from environment (shell env > .env):

```bash
# Copy template
cp .env.example .env

# Edit with your keys, or set env vars:
export OPENROUTER_API_KEY=your_key
export POSTGRES_DSN="postgresql://postgres:postgres@localhost:5432/medical_ingestion"
export QDRANT_URL="http://localhost:6333"
export EMBEDDING_MODEL="openai/text-embedding-3-small"
export CHUNK_SIZE=1024
export CHUNK_OVERLAP=100
```

Key settings in [.env.example](.env.example):
- `OPENROUTER_API_KEY` — embedding API key
- `POSTGRES_DSN` — chunk cache/provenance/dedup store
- `QDRANT_URL` — similarity search backend
- `EMBEDDING_MODEL` — OpenRouter model slug
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — chunker config
- `CLINICAL_TRIALS_TABLE` / `ELIGIBILITY_TABLE` — SQLite table names (default: `clinical_trials` / `eligibility`)

## Usage

### Ingestion → Embedding → Storage → Qdrant (end-to-end pipeline, ✓ complete)

```bash
# Start services first
bash scripts/start_postgres.sh  # chunk cache/provenance at :5432
bash scripts/start_qdrant.sh    # vector search at :6333

# Ingest documents (load → chunk → embed → Postgres → Qdrant)
# See dummy_docs/ for sample PDFs, JSON, clinical trials data
uv run scripts/ingest_documents.py
```

### Loaders standalone

```python
from ingestion.loaders import LoaderFactory
from ingestion.chunker import ChunkerConfig, ChunkerService

# Load documents (PDF, text, Excel/CSV, JSON, or SQL)
loader = LoaderFactory.pdf_loader("docs/")
docs = loader.load()  # list[langchain_core.documents.Document]

# Chunk
config = ChunkerConfig(chunk_size=1024, chunk_overlap=100)
chunker = ChunkerService(config=config)
chunks = chunker.chunk(docs)
```

### Clinical trials (fetch + seed SQLite)

```bash
# Fetch diabetes + cancer trials, seed SQLite
uv run scripts/seed_clinical_trials_db.py

# Query via SQL loader
python -c "
from ingestion.loaders import LoaderFactory
from ingestion.clinicaltrials_fetcher import fetch_dummy_trials

loader = LoaderFactory.sql_loader()
docs = loader.load()
print(f'Loaded {len(docs)} trial documents')
"
```

### RAG query (planned — not yet wired)

Retrieval + generation still under design. Models defined in `models/rag.py`, no active endpoints yet.

## Requirements

### System

- Python 3.13+
- Docker + Docker Compose (Postgres 16 + Qdrant v1.19+)
- `uv` package manager

### Python Dependencies

Managed via `uv sync` from pyproject.toml. Key packages:

- `psycopg[binary]` — Postgres adapter + psql CLI
- `sqlalchemy`, `sqlmodel` — ORM (chunk cache/provenance, clinical trials)
- `qdrant-client` — Vector DB client (similarity search)
- `langchain-*` — Document loading, chunking, embeddings
- `docling`, `unstructured` — PDF/document parsing
- `structlog` — Structured JSON logging
- `tenacity` — Retry logic (embeddings API)

## Development

```bash
# Install dependencies
uv sync

# Activate venv (optional but recommended)
source .venv/bin/activate

# Start services
bash scripts/start_postgres.sh  # Postgres at :5432
bash scripts/start_qdrant.sh    # Qdrant at :6333 (HTTP) / :6334 (gRPC)

# Query Postgres via psql
psql -U postgres -d medical_ingestion -c "SELECT COUNT(*) FROM chunks;"

# Seed clinical trials (one-time)
uv run scripts/seed_clinical_trials_db.py

# Run full ingestion pipeline
uv run scripts/ingest_documents.py

# Run tests (when available)
uv run pytest

# View structured logs (ingest outputs JSON to stdout)
uv run scripts/ingest_documents.py | jq '.event'
```

## Learning Outcomes

- **Document parsing** — Docling (PDFs), Unstructured (mixed formats), JSON/SQL ingestion
- **Chunking strategies** — Recursive text splitting, metadata propagation, structure-aware refinement (future)
- **Vector embeddings** — OpenRouter API integration, retry logic, cost optimization (cache-check), DLQ for failures
- **Similarity search** — Qdrant local vector DB, point deduplication, metadata filtering
- **Relational storage** — SQLModel + Postgres/SQLite, ORM queries, per-occurrence provenance tracking
- **Observability** — Structured logging (structlog JSON), semantic events, operational monitoring
- **RAG architecture** — Modular retrieval + generation pipeline (planned: hybrid search, reranking, entity extraction)
- **Pipeline composition** — Standalone + chainable loaders, chunker, embedder, storage layers
