---
name: file_structure
type: Concept
title: File and Folder Structure
description: Guide to every top-level directory — what lives where, what runs, what stores
status: stable
---

# File and Folder Structure

```
medical-ingestion/
├── ingestion/                      # Load, parse, chunk, embed documents
│   ├── loaders/
│   │   ├── __init__.py             # LoaderFactory (get_pdf_loader, get_text_loader, etc)
│   │   ├── base.py                 # LoaderService protocol
│   │   ├── pdf.py                  # PDFLoaderService (via Docling)
│   │   ├── text.py                 # TextLoaderService
│   │   ├── excel_csv.py            # ExcelCSVLoaderService
│   │   ├── json.py                 # JSONLoaderService
│   │   ├── sql.py                  # SQLDataLoaderService (clinical trials from SQLite)
│   │   └── individual-scripts/     # Standalone reference implementations (not used by ingestion)
│   │       ├── pdf_extraction.py   # Docling-only reference
│   │       ├── json_extraction.py  # LangChain reference
│   │       ├── excel_csv_extraction.py
│   │       ├── basic_document_ingestion.py
│   │       ├── pmc_fetcher.py      # PubMed Central raw fetch
│   │       └── pmc_json_converter.py  # PMC raw → structured JSON
│   ├── chunker.py                  # ChunkerService (Document → Document[])
│   ├── embedder.py                 # Embedder (Document → embedding vector via OpenRouter)
│   └── clinicaltrials_fetcher.py   # ClinicalTrials.gov v2 API fetch
│
├── models/                         # Pydantic + SQLModel data contracts
│   ├── __init__.py
│   ├── documents.py                # Stub (Document moved to langchain_core)
│   ├── vectors.py                  # Chunk, FailedEmbedding, IngestedDocument (SQLModel tables)
│   ├── rag.py                      # RAGQuery, RAGResponse (for RAG pipeline)
│   └── clinical_trial.py           # ClinicalTrial, Eligibility (SQLModel tables)
│
├── storage/                        # Relational persistence & cache
│   ├── __init__.py
│   ├── postgres.py                 # SQLAlchemy engine, init_db(), Postgres setup
│   ├── chunk_store.py              # ChunkStore (embedding cache, provenance, dedup, DLQ)
│   ├── sql.py                      # SQLLoaderService (SQLite loader for clinical trials)
│   └── docker-compose.postgres.yml # (moved to root)
│
├── vector_db/                      # Similarity search abstraction
│   ├── __init__.py
│   ├── base.py                     # VectorStore protocol (upsert_one, find_by_hash, etc)
│   └── qdrant.py                   # QdrantVectorStore (local Docker client)
│
├── retrieval/                      # Search & RAG pipeline (production)
│   ├── __init__.py
│   ├── bm25.py                     # BM25 sparse index (lexical search)
│   ├── hybrid.py                   # Hybrid search (dense Qdrant + sparse BM25, RRF fusion)
│   ├── reranker.py                 # Cross-encoder reranker (OpenRouter /rerank)
│   └── search.py                   # SearchService (embed → hybrid → rerank → LLM)
│
├── scripts/                        # Entry-point scripts
│   ├── ingest_documents.py         # Full pipeline: load → chunk → embed → Postgres → Qdrant
│   ├── seed_clinical_trials_db.py  # Fetch ClinicalTrials.gov, seed SQLite
│   ├── similarity_search_demo.py   # Interactive: embed query → Qdrant search → display
│   ├── bm25_search_demo.py         # Throwaway: BM25-only search (no dense, no rerank)
│   └── hybrid_search_demo.py       # Throwaway: hybrid search demo (no rerank)
│
├── infrastructure/                 # Container & service startup (mostly moved to root)
│   ├── scripts/
│   │   ├── start_qdrant.sh         # Idempotent Qdrant startup (docker run)
│   │   └── start_postgres.sh       # Idempotent Postgres startup (docker run)
│   └── [docker-compose files moved to root]
│
├── migrations/                     # Alembic schema migrations
│   ├── versions/                   # Auto-generated revision files
│   └── env.py                      # Alembic config (wired to models/vectors.py metadata)
│
├── doc/                            # Documentation (OKF v0.2)
│   ├── index.md                    # Index of indexes (points to feature/ and bug/)
│   ├── feature/                    # Architecture bundle (one concept doc per module)
│   │   ├── index.md                # Architecture bundle index (start: architecture_overview.md)
│   │   ├── architecture_overview.md # High-level system design
│   │   ├── file_structure.md       # This file — folder guide
│   │   ├── loaders.md
│   │   ├── chunker.md
│   │   ├── embedder.md
│   │   ├── chunk_store.md
│   │   ├── postgres_storage.md
│   │   ├── qdrant_infrastructure.md
│   │   ├── bm25_index.md
│   │   ├── hybrid_search_retrieval.md
│   │   ├── reranker.md
│   │   ├── search_service.md
│   │   ├── ingest_documents_script.md
│   │   ├── [other concept docs...]
│   │   └── alembic_migrations.md
│   └── bug/                        # Incident index (one doc per bug, whether fixed or active)
│       ├── index.md
│       └── incidents/
│
├── dummy_docs/                     # Sample input data for testing
│   ├── *.pdf
│   ├── *.txt
│   └── *.json
│
├── volumes/                        # Docker persistent storage (gitignored)
│   ├── qdrant/                     # Qdrant vector DB data
│   └── postgres/                   # Postgres data
│
├── .claude/                        # Claude Code config
│   ├── agents/                     # Agent specs
│   │   ├── incident-handler.md
│   │   └── doc-sync.md
│   ├── settings.json               # Claude Code settings
│   ├── plugins/                    # Local plugins (caveman mode, etc)
│   └── projects/
│       └── -home-rounak-Desktop-Projects-medical-ingestion/
│           └── memory/             # Persistent memory (memories.md index + discrete memory files)
│
├── main.py                         # Interactive retrieval + generation REPL (SearchService)
├── logging_config.py               # Structured JSON logging (structlog)
├── settings.py                     # Environment config loading (pydantic BaseSettings)
├── pyproject.toml                  # Python dependencies + metadata
├── uv.lock                         # Locked dependency versions
├── .env.example                    # Template for .env (copy to .env and add OPENROUTER_API_KEY)
├── .env                            # Local secrets (gitignored)
├── .gitignore                      # Ignore patterns
├── README.md                       # This project's overview, quickstart, config
├── CLAUDE.md                       # Project-specific Claude Code rules
├── AGENTS.md                       # Agent specs + behavioral guidelines
├── IMPLEMENTATION_PLAN.md          # Narrative architecture + open decisions
├── docker-compose.qdrant.yml       # Qdrant service (HTTP 6333 + gRPC 6334)
├── docker-compose.postgres.yml     # Postgres service (5432)
├── alembic.ini                     # Alembic config file
└── .caveman.json                   # Caveman mode config (full level)
```

## Directory Purposes at a Glance

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| **ingestion/** | Load, parse, chunk, embed documents | loaders/, chunker.py, embedder.py |
| **models/** | Data types (Pydantic + SQLModel) | vectors.py, clinical_trial.py, rag.py |
| **storage/** | Postgres cache, provenance, DLQ | postgres.py, chunk_store.py |
| **vector_db/** | Similarity search wrapper | qdrant.py (QdrantVectorStore) |
| **retrieval/** | Search + RAG (production pipeline) | bm25.py, hybrid.py, reranker.py, search.py |
| **scripts/** | CLI entry points | ingest_documents.py, main.py, *_demo.py |
| **migrations/** | Database schema versions | versions/, env.py |
| **doc/feature/** | Architecture bundle (one doc per module) | index.md, architecture_overview.md |
| **doc/bug/** | Incident tracking (bugs fixed or active) | index.md, incidents/ |
| **volumes/** | Docker persistent storage (gitignored) | qdrant/, postgres/ |
| **.claude/** | Claude Code config + memory | agents/, settings.json, projects/*/memory/ |

## Bootstrap / Initialization Flow

1. **venv setup** — `uv sync` → `.venv/`
2. **Config** — `.env` (copy from `.env.example`, add `OPENROUTER_API_KEY`)
3. **Services** — `bash scripts/start_qdrant.sh` + `bash scripts/start_postgres.sh` (Docker)
4. **Ingest** — `uv run scripts/ingest_documents.py` (load → chunk → embed → cache → Qdrant)
5. **Search** — `uv run main.py` (interactive REPL, hybrid retrieval + LLM)

## Ingestion Data Flow

```
dummy_docs/ (PDFs, JSON, text)
  ↓
loaders/ (extract documents as langchain_core.documents.Document)
  ↓
chunker.py (split, propagate metadata)
  ↓
embedder.py (OpenRouter API, cache-checked)
  ↓
storage/postgres.py (Postgres: provenance, cache, dedup, DLQ)
  ↓
retrieval/bm25.py (rebuild sparse index)
  ↓
vector_db/qdrant.py (upsert dense vectors + metadata)
```

## Retrieval Data Flow

```
main.py (user query)
  ↓
embedder.py (embed query, cache-checked)
  ↓
retrieval/hybrid.py (dense Qdrant + sparse BM25, RRF fusion)
  ↓
retrieval/reranker.py (cross-encoder rerank shortlist)
  ↓
retrieval/search.py (grounded LLM answer)
  ↓
display results + stream response
```

## Key Files (Quick Reference)

- **Entry points:** `main.py` (REPL), `scripts/ingest_documents.py` (pipeline)
- **Config:** `settings.py` (loads `.env`), `pyproject.toml` (dependencies)
- **Logging:** `logging_config.py` (structlog JSON)
- **Services:** `docker-compose.qdrant.yml`, `docker-compose.postgres.yml`
- **Startup scripts:** `scripts/start_qdrant.sh`, `scripts/start_postgres.sh`
- **Migrations:** `alembic.ini`, `migrations/versions/`
- **Architecture docs:** `doc/feature/index.md`, `IMPLEMENTATION_PLAN.md`

---

## Next: Deep Dive

- **Loading docs?** Start at [Loaders](/doc/feature/loaders.md)
- **How chunking works?** See [Chunker](/doc/feature/chunker.md)
- **How retrieval works?** See [Hybrid Search](/doc/feature/hybrid_search_retrieval.md)
- **How to extend?** See [Architecture Overview](/doc/feature/architecture_overview.md)
