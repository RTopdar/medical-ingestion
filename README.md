# Medical Ingestion

Learning project for vector data ingestion, parsing, RAG pipelines, and database connections.

## Goals

Build modular, reusable components that can be:

- **Called separately** — Each ingestion, parsing, RAG, or DB pipeline is a standalone callable module
- **Composed together** — Pipelines can be chained and mixed to build complex workflows
- **Tested independently** — Each component has its own test suite and can be validated in isolation

## Architecture

```text
ingestion/      — data extraction & parsing
  ├── loaders/  — PDF, docs, APIs, DBs
  ├── parsers/  — text extraction, chunking
  └── pipeline/ — compose loaders + parsers

embeddings/     — embedding generation
  └── embed.py  — vectorize text via embedding models

vector_db/      — vector storage
  ├── chroma.py — Chroma integration
  ├── faiss.py  — FAISS integration
  └── base.py   — abstract vector store interface

rag/            — retrieval-augmented generation
  ├── retriever.py — vector + metadata search
  ├── generator.py — LLM-based answer generation
  └── pipeline.py  — orchestrate retrieval + generation

storage/        — traditional DB connectors
  └── sql.py    — SQL database operations
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

### Modular — Call components separately

```python
from ingestion.loaders import PDFLoader
from ingestion.parsers import TextChunker
from embeddings.embed import Embedder

# Extract text from PDF
loader = PDFLoader("docs/paper.pdf")
text = loader.load()

# Chunk and prepare
chunker = TextChunker(chunk_size=1024)
chunks = chunker.chunk(text)

# Embed chunks
embedder = Embedder()
vectors = embedder.embed(chunks)
```

### Cohesive — Chain pipelines together

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

## Development

```bash
# Install dependencies
uv sync

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
