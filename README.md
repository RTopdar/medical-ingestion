# Medical Ingestion

Production-ready RAG pipeline for medical documents. Ingest PDFs/JSON/SQL → parse → chunk → embed (OpenRouter) → store (Postgres cache + Qdrant) → hybrid search (dense + BM25) → rerank (cross-encoder) → generate (LLM).

## Features

### Document Ingestion

- Multi-format loaders: PDF (Docling), JSON, Excel/CSV, SQL, API (ClinicalTrials.gov, PubMed Central)
- Metadata propagation (source, page, author) through all processing stages

### Embeddings & Storage

- OpenRouter API integration with retry logic (tenacity backoff)
- Postgres cache-checking (hash-based dedup) + provenance tracking + DLQ for failures
- Per-document dedup state (no re-embedding)

### Vector Search (Qdrant)

- Local Docker-based Qdrant v1.19+
- Persistent volumes for data survival
- Payload filtering + metadata in vectors

### Retrieval Pipeline

- **Dense retrieval** — Qdrant vector similarity
- **Sparse retrieval** — BM25 lexical index (rebuilt per ingest run)
- **Fusion** — Reciprocal rank fusion (RRF) over top-k results
- **Reranking** — Cross-encoder (OpenRouter `/rerank`) for final ranking
- **Generation** — Grounded LLM response (streaming)

### Architecture Documentation

- OKF v0.2 bundle structure (Open Knowledge Format) — standardized architecture docs
- One concept document per module/service/script
- Auto-sync docs with code changes (doc-sync subagent)
- Knowledge graph queryable via `/graphify` skill

### Code Quality

- Structured JSON logging (structlog) across all layers
- Modular, testable components (standalone + composable)
- Alembic migrations for Postgres schema versioning
- SQLModel ORM for type-safe database access

## Design Goals

Build modular, reusable components that can be:

- **Called separately** — Each ingestion, embedding, storage, or RAG pipeline is a standalone callable module
- **Composed together** — Pipelines can be chained and mixed to build complex workflows
- **Tested independently** — Each component has its own test suite and can be validated in isolation

## Quick Start

**Setup (one-time):**

```bash
# Install dependencies via uv
uv sync

# Create .env from template and add your OPENROUTER_API_KEY
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=sk-...
```

**Ingest documents:**

```bash
# Start Postgres + Qdrant (Docker)
bash scripts/start_postgres.sh
bash scripts/start_qdrant.sh

# Run ingestion pipeline (load → chunk → embed → Postgres → Qdrant)
uv run scripts/ingest_documents.py
```

**Retrieve & generate (interactive REPL):**

```bash
# Run the retrieval system: hybrid search (dense + BM25) → cross-encoder rerank → LLM
uv run main.py

# At the prompt, ask: "What are symptoms of diabetes?"
# Returns: reranked chunks + grounded LLM answer + citations
```

**Alternative demos:**

```bash
uv run scripts/similarity_search_demo.py    # Dense vector search only
uv run scripts/bm25_search_demo.py          # Sparse lexical search only
uv run scripts/hybrid_search_demo.py        # Hybrid fusion (no rerank)
```

See [File & Folder Structure](/doc/feature/file_structure.md) for where everything lives.

## Development Standards & Documentation

### Coding Guidelines

- **Modular design** — Standalone services, chainable pipelines, composable components
- **Type safety** — SQLModel ORM for database models, type hints on public APIs
- **Structured logging** — JSON output via structlog, semantic event names, operational context
- **Error handling** — Retry logic (tenacity) for external APIs, DLQ for failures
- **Black formatting** — Python 3.13 target (enforced in pre-commit)
- **Docstrings** — Minimal; code is self-documenting. Comments only for non-obvious WHY

### Documentation Standards (OKF v0.2)

Architecture docs live in `doc/feature/` — [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) standardized bundle:

- One concept document per module/service/script (concept = one `.md` file with YAML frontmatter + markdown body)
- Frontmatter metadata: `type`, `title`, `description`, optional `resource` (points to code), `tags`, `generated` (author/timestamp), `verified` (human/process sign-off)
- Provenance + trust as first-class: `sources` (materials derived from, with credibility signals), `generated` (who/when written), `verified` (who/when reviewed)
- Cross-links between concepts via standard markdown links
- Reserved files: `index.md` (directory listing), `log.md` (update history)
- No central schema registry, no required tooling — plain markdown + YAML, fully diffable in git

### Doc Sync Agent

After significant code changes (new modules, services, data models, scripts, migrations, architectural decisions), the `doc-sync` subagent automatically:

- Scans git diff for code changes
- Updates `IMPLEMENTATION_PLAN.md` narrative
- Creates/updates OKF concept docs in `doc/feature/`
- Updates bundle index + cross-links
- Ensures architecture docs stay in sync with code

**Result:** Docs don't rot. Humans read code + docs in parallel. No manual documentation churn.

Query the knowledge graph anytime with `/graphify query "<question>"` — it reflects current code + docs structure.

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

### Retrieval + Generation (interactive REPL)

```bash
# Must have ingested documents first (see above)
uv run main.py

# Prompt: "What are the symptoms of type 2 diabetes?"
# System:
#   1. Embed query (cache-checked)
#   2. Dense search (Qdrant) + sparse search (BM25)
#   3. Fuse via reciprocal rank fusion
#   4. Rerank with cross-encoder
#   5. Stream grounded LLM answer with citations
```

**SearchService orchestrates the full RAG pipeline** — see [Search Service](/doc/feature/search_service.md).

To integrate into your app: `from retrieval.search import SearchService` + `service.search(query)` returns chunks + LLM response.

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

## Documentation Index

**Architecture & Design:**

- **[System Overview](/doc/feature/architecture_overview.md)** — how ingestion, storage, retrieval, RAG layers interconnect
- **[File & Folder Structure](/doc/feature/file_structure.md)** — guide to directories, what runs where, bootstrap flow
- **[Full Architecture Bundle](/doc/feature/index.md)** — one doc per module/service/script (loaders, chunker, embedder, storage, search, etc.)

**Infrastructure & Setup:**

- **[Container Setup](/doc/feature/qdrant_infrastructure.md)** — Qdrant Docker compose, startup script, persistent volumes
- **[Postgres Storage](/doc/feature/postgres_storage.md)** — Postgres setup, init, chunk cache/provenance tables
- **[Alembic Migrations](/doc/feature/alembic_migrations.md)** — Schema versioning for Postgres tables

**How Things Work:**

- **[Loaders](/doc/feature/loaders.md)** — PDF/JSON/text/SQL/API ingestion
- **[Hybrid Search](/doc/feature/hybrid_search_retrieval.md)** — dense (Qdrant) + sparse (BM25), RRF fusion
- **[Cross-Encoder Reranker](/doc/feature/reranker.md)** — second-pass reorder via OpenRouter
- **[Search Service](/doc/feature/search_service.md)** — retrieval + grounded LLM answer

**Troubleshooting:**

- **[Known Incidents](/doc/bug/index.md)** — lookup prior bugs + fixes in this area before making changes

**Code Entry Points:**

- `ingestion/loaders/` — load documents from various formats
- `scripts/ingest_documents.py` — end-to-end ingestion pipeline
- `main.py` — interactive retrieval REPL
- `retrieval/search.py` — SearchService (for programmatic use)

## Learning Outcomes

- **Document parsing** — Docling (PDFs), Unstructured (mixed formats), JSON/SQL ingestion
- **Chunking strategies** — Recursive text splitting, metadata propagation, structure-aware refinement (future)
- **Vector embeddings** — OpenRouter API integration, retry logic, cost optimization (cache-check), DLQ for failures
- **Similarity search** — Qdrant local vector DB, point deduplication, metadata filtering
- **Relational storage** — SQLModel + Postgres/SQLite, ORM queries, per-occurrence provenance tracking
- **Observability** — Structured logging (structlog JSON), semantic events, operational monitoring
- **RAG architecture** — Modular retrieval + generation pipeline (hybrid search, reranking, cross-encoder rerank)
- **Pipeline composition** — Standalone + chainable loaders, chunker, embedder, storage layers
