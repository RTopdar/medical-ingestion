# Implementation Plan

> Living doc. Update this file every time new architecture, module, or major decision is added. Do not let this drift from actual codebase state.

## Status

Learning project for vector data ingestion, parsing, RAG, and DB connections. Foundation layer complete: settings, env config, Pydantic data models. Ingestion layer functional for PDF, Excel/CSV, and JSON sources (loaders + chunker wired via `scripts/ingest_documents.py`); JSON path includes a real data source (PMC/PubMed fetcher). Embeddings, vector DB, RAG, and storage layers still planned. See `INGESTION_GUIDE.md` for the end-to-end usage walkthrough.

## Architecture

**Design Principle:** Modular + Composable. Each pipeline (ingestion, embedding, RAG, storage) is:

- Callable standalone with its own interface
- Chainable with other pipelines
- Independently testable and deployable

**Layers:**

1. **Settings & Config** — Environment loading (shell priority > .env)
2. **Ingestion** — Document loading and parsing (loaders, parsers, chunkers)
3. **Embeddings** — Text-to-vector conversion via embedding models
4. **Vector DB** — Storage abstraction (Chroma, FAISS backends)
5. **RAG** — Retriever + Generator orchestration
6. **Storage** — Relational DB connectors for metadata/context

## Components

### 1. settings.py

- **Purpose:** Centralized config from environment
- **Status:** ✓ Created
- **Key files:** `settings.py`
- **Exports:** `Settings` class, `settings` singleton

### 2. models/

- **Purpose:** Pydantic data contracts — single source of truth for all data structures
- **Status:** ✓ Created
- **Key files:**
  - `models/documents.py` — Document, Chunk, Metadata
  - `models/vectors.py` — Vector, EmbeddingRequest, EmbeddingResult
  - `models/rag.py` — RAGQuery, RAGResponse, RetrievedContext
- **Exports:** All via `models/__init__.py`
- **Convention:** Every new data type gets a Pydantic model here; no dicts, tuples, or ad-hoc classes

### 4. ingestion/

- **Purpose:** Extract, parse, and chunk documents from multiple source formats into Pydantic `Document`/`Chunk` objects
- **Status:** ✓ Created (PDF, Excel/CSV, JSON, chunking)
- **Key files:**
  - `ingestion/loaders.py` — `LoaderFactory` + Pydantic-based loader services: `PDFLoaderService` (Docling), `TextLoaderService`, `ExcelCSVLoaderService` (Unstructured), `JSONLoaderService` (nested metadata flattening + common-field content extraction for clinical/research JSON). All return `models.documents.Document` objects.
  - `ingestion/chunker.py` — `ChunkerService` + `ChunkerConfig`. Splits `Document`s into `Chunk`s via `RecursiveCharacterTextSplitter`, preserving parent metadata. `chunk_size`/`chunk_overlap` now default from `settings.chunk_size`/`settings.chunk_overlap` (previously hardcoded) — single source of truth for chunk sizing is `.env`/`settings.py`.
  - `ingestion/pdf_extraction.py` — standalone LangChain-`Document`-based PDF loader (Docling), independent of the Pydantic loader stack. Demo/reference script, not used by `scripts/ingest_documents.py`.
  - `ingestion/json_extraction.py` — standalone LangChain-`Document`-based JSON loader, same relationship to `JSONLoaderService` as `pdf_extraction.py` has to `PDFLoaderService` (simpler, non-Pydantic reference implementation).
  - `ingestion/pmc_json_converter.py` — fetches papers from PMC/PubMed Central E-utilities (search + full-text XML fetch) and writes them as structured JSON (`dummy_docs/pmc_documents.json`) matching the schema `JSONLoaderService` expects (`publication_info`, `authors`, `research_data`, etc.). Populates real sample data for the JSON ingestion path.
- **Data flow:** JSON is now a first-class ingestion source alongside PDF and Excel/CSV — `pmc_json_converter.py` → `dummy_docs/*.json` → `JSONLoaderService` → `Document` → `ChunkerService` → `Chunk`.

### 4a. scripts/

- **Purpose:** Executable entry points that wire ingestion components together
- **Status:** ✓ Created
- **Key files:** `scripts/ingest_documents.py` — full pipeline script (load JSON/PDF/CSV-Excel → chunk → summary stats)
- **Known issue (inconsistency, not yet fixed):** `scripts/ingest_documents.py` calls `ChunkerConfig(chunk_size=..., chunk_overlap=..., separators=[...])` and `RecursiveChunker(...)`, but `ingestion/chunker.py` only defines `ChunkerConfig(chunk_size, chunk_overlap)` (no `separators` field) and `ChunkerService` (no `RecursiveChunker` class). This will raise at runtime — flagged for follow-up fix, not corrected here per doc-sync scope (docs describe code as-is).

### 5. embeddings/ (planned)

- **Purpose:** Generate embeddings via embedding models
- **Key files:** `embeddings/embed.py`

### 6. vector_db/ (planned)

- **Purpose:** Store and query vectors
- **Key files:** `vector_db/base.py` (abstract), `chroma.py`, `faiss.py`

### 7. rag/ (planned)

- **Purpose:** Retrieval + generation
- **Key files:** `retriever.py`, `generator.py`, `pipeline.py`

### 8. storage/ (planned)

- **Purpose:** Relational DB for metadata
- **Key files:** `storage/sql.py`

## Data Sources

**Free medical data APIs for testing/sample data:**

- **PubMed E-utilities** (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`) — 35M+ peer-reviewed papers; no key; 3 req/sec limit; methods: esearch (find), efetch (metadata + abstract), elink (related)
- **PMC Open Access** (~2M full-text papers via PubMed db=pmc) — freely available complete articles; same rate limits; use for full paper content
- **ClinicalTrials.gov API v2** (`https://clinicaltrials.gov/api/v2/`) — 500K+ trials; normalized JSON; search by condition/drug/phase/sponsor

**Paper ingestion strategy:** Use PubMed for metadata + abstracts; combine with PMC full-text for open-access papers. Fall back to abstract-only for restricted-access papers.

**Sample data storage:** All dummy/test data in `dummy_docs/` — organized by source (pubmed/, clinicaltrials/) with format indicators in filenames. Example: `full_paper_diabetes.txt` (combined PubMed metadata + PMC full text).

## Open Decisions

- **Primary embedding model:** sentence-transformers/all-MiniLM-L6-v2 (default, lightweight)
  - Alternatives: OpenAI, custom-trained per domain
- **Default vector DB:** Chroma (local + simple)
  - Alternatives: FAISS (local, large scale), Weaviate, Pinecone
- **RAG retrieval strategy:** Hybrid (vector + metadata filters)
  - Alternatives: Dense-only, BM25 hybrid, multi-stage

**Settled (moved from Open Decisions to Architecture):**

- **Chunk size/overlap source of truth:** `settings.py` (`CHUNK_SIZE`/`CHUNK_OVERLAP` env vars, defaults 1024/100), not hardcoded in `ChunkerConfig`. (inferred from code, `ingestion/chunker.py`)
- **JSON as first-class ingestion source:** JSON is treated on par with PDF and Excel/CSV, with `JSONLoaderService` doing rich nested-metadata extraction for clinical/research-paper schemas (patient_info, clinical_data, publication_info, authors, research_data, surgical_data). (inferred from code, `ingestion/loaders.py`)

## Future Enhancements (Deferred — not yet built)

Retrieval architecture decisions from design discussion, deferred until core pipeline (ingestion → embed → store) is working end-to-end:

- **Chunking:** RecursiveCharacterTextSplitter, 400-800 tokens (~800-1500 char), 100-200 char overlap. Skip TokenTextSplitter — chunk sizes stay well under any embedding model's token ceiling, no need for token-exact splitting. Structure-aware pre-split by section (PMC XML tags for papers) before recursive-split within each section, when source structure is available.
- **Contextual retrieval:** prepend each chunk with LLM-generated (Haiku) short context blurb before embedding — cuts retrieval failure rate significantly (Anthropic's technique).
- **Hybrid retrieval + reranking (enterprise-grade baseline, domain-agnostic):** dense (vector) + sparse (BM25) retrieval, RRF-fused, top-50 → cross-encoder rerank → top-5-10 → LLM. Non-negotiable at enterprise scale — dense-only misses exact-term matches (IDs, codes, dosages, citations).
- **Metadata — known case:** when metadata is knowable (dates, client/policy/event tags), store directly, pre-filter before vector search (pre-filter, not post-filter — shrinks ANN search space, avoids recall bugs).
- **Metadata — unknown case (schema discovery):** two-pass — (1) sample corpus, frontier model (Opus) proposes taxonomy/schema, human review; (2) bulk-tag all docs/chunks against fixed schema via Haiku + Batch API + structured outputs (`output_config.format`). Re-run discovery periodically (schema drift).
- **Metadata — worst case (messy dump, no structure, no timestamps):** embed everything first (needed anyway) → unsupervised clustering (HDBSCAN/k-means) on embeddings to discover latent doc-type structure without any prior metadata → sample representatively *per cluster* (not randomly) for frontier-model schema discovery → bulk-tag cheap as above → escalate to frontier model per-doc only for the low-confidence/outlier tail. Do NOT brute-force every doc through a frontier model — clustering-informed sampling gets equivalent schema quality at a fraction of the cost.
- **Parsing library split:** Docling for the current PubMed/scientific-PDF pipeline (strong table/formula extraction via TableFormer, native hierarchical output matches structure-aware chunking plan, ships `HybridChunker`). **Unstructured for the worst-case messy dump** (unknown/mixed file types, no structure) — `partition()` is format-agnostic (PDF/DOCX/PPTX/HTML/EML/images) with auto OCR/layout fallback, and its normalized element output (Title/NarrativeText/Table/ListItem counts per doc) is a free structural signal feeding the pre-clustering triage step above.
- **Generic entity extraction:** spaCy (`en_core_web_lg`) for universal entities (PERSON, ORG, DATE, MONEY, GPE) — free, fast, local, bulk pass across all docs. For medical-specific text: scispaCy (`en_ner_bc5cdr_md` etc.) for DISEASE/CHEMICAL/GENE entities generic spaCy misses. Runs alongside/before LLM-based schema tagging, not instead of it.
- **Structure-free hierarchical retrieval (RAPTOR):** cluster chunks → LLM-summarize clusters → recurse upward to a summary tree; query traverses top-down. Consider as accuracy upgrade once flat hybrid+rerank baseline is proven — high-value for accuracy-first requirements.
- **Latency levers (in priority order once accuracy baseline works):** metadata pre-filtering (biggest single win, shrinks search space before expensive stages), fewer rerank candidates / faster reranker (reranking dominates retrieval-side latency, not vector search), parallel dense+sparse search, semantic query caching.

## Changelog

- 2026-08-12: doc-sync — documented JSON ingestion path (`ingestion/json_extraction.py`, `ingestion/pmc_json_converter.py`, `JSONLoaderService`), `scripts/ingest_documents.py` pipeline entry point, and settings-driven chunker config (`ChunkerConfig` now reads `chunk_size`/`chunk_overlap` from `settings.py` instead of hardcoded defaults). Moved 2 settled decisions from Open Decisions to Architecture. Flagged a real code inconsistency in `scripts/ingest_documents.py` (references `RecursiveChunker`/`separators` that don't exist in `ingestion/chunker.py`) for follow-up.
- 2026-08-11: Documented deferred retrieval architecture (chunking, hybrid+rerank, metadata auto-discovery incl. worst-case messy-data strategy, NER, RAPTOR) — see Future Enhancements section.
- 2026-08-11: Pydantic models layer — Document, Chunk, Vector, RAGQuery/Response contracts. Added Pydantic-first rule to CLAUDE.md.
- 2026-08-11: Foundation layer — settings.py, .env.example, modular architecture design, README docs.
- 2026-08-09: Added doc-sync agent for self-healing architecture documentation.
- 2026-08-09: Project scaffolded (CLAUDE.md, AGENTS.md, doc/ folder, this plan).
