# Graph Report - .  (2026-09-13)

## Corpus Check
- 118 files · ~65,633 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1018 nodes · 1997 edges · 84 communities (58 shown, 26 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 300 edges (avg confidence: 0.55)
- Token cost: 600,590 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_LLM Chat Router|LLM Chat Router]]
- [[_COMMUNITY_Clinical Trials Fetcher|Clinical Trials Fetcher]]
- [[_COMMUNITY_Agent Rules & Guidelines|Agent Rules & Guidelines]]
- [[_COMMUNITY_Chunking Data Models|Chunking Data Models]]
- [[_COMMUNITY_Chunk Store & Dedup|Chunk Store & Dedup]]
- [[_COMMUNITY_Loader Factory Pattern|Loader Factory Pattern]]
- [[_COMMUNITY_Document Chunking Logic|Document Chunking Logic]]
- [[_COMMUNITY_Architecture Decisions|Architecture Decisions]]
- [[_COMMUNITY_Ingestion Script Pipeline|Ingestion Script Pipeline]]
- [[_COMMUNITY_Qdrant Vector Store Setup|Qdrant Vector Store Setup]]
- [[_COMMUNITY_Alembic Migrations & BM25 Build|Alembic Migrations & BM25 Build]]
- [[_COMMUNITY_JSON-to-PDF Conversion Scripts|JSON-to-PDF Conversion Scripts]]
- [[_COMMUNITY_Hybrid Retrieval Search|Hybrid Retrieval Search]]
- [[_COMMUNITY_Chunk Store Embedding Sync|Chunk Store Embedding Sync]]
- [[_COMMUNITY_Alembic Migration Management|Alembic Migration Management]]
- [[_COMMUNITY_Chunker Markdown Sectioning|Chunker Markdown Sectioning]]
- [[_COMMUNITY_PDF Loader Tests|PDF Loader Tests]]
- [[_COMMUNITY_BM25 Index Implementation|BM25 Index Implementation]]
- [[_COMMUNITY_Citation Mapping & RAG Answers|Citation Mapping & RAG Answers]]
- [[_COMMUNITY_Base Loader Config|Base Loader Config]]
- [[_COMMUNITY_BM25 & Citation Concepts|BM25 & Citation Concepts]]
- [[_COMMUNITY_RAGAS Eval Runner|RAGAS Eval Runner]]
- [[_COMMUNITY_Chunk Metadata Integration Tests|Chunk Metadata Integration Tests]]
- [[_COMMUNITY_Embedding Cache Rationale|Embedding Cache Rationale]]
- [[_COMMUNITY_ExcelJSON Ingestion Scripts|Excel/JSON Ingestion Scripts]]
- [[_COMMUNITY_Main CLI Entry Point|Main CLI Entry Point]]
- [[_COMMUNITY_Prototype ExcelJSON Scripts|Prototype Excel/JSON Scripts]]
- [[_COMMUNITY_Ingest Documents Tests|Ingest Documents Tests]]
- [[_COMMUNITY_PMC JSON Converter|PMC JSON Converter]]
- [[_COMMUNITY_Basic Document Ingestion Prototype|Basic Document Ingestion Prototype]]
- [[_COMMUNITY_PMC Fetcher Prototype|PMC Fetcher Prototype]]
- [[_COMMUNITY_Basic Document Ingestion (Duplicate)|Basic Document Ingestion (Duplicate)]]
- [[_COMMUNITY_PMC Fetcher (Duplicate)|PMC Fetcher (Duplicate)]]
- [[_COMMUNITY_Basic Ingestion & PMC Prototypes|Basic Ingestion & PMC Prototypes]]
- [[_COMMUNITY_Embedder Methods|Embedder Methods]]
- [[_COMMUNITY_HybridSimilarity Search Demos|Hybrid/Similarity Search Demos]]
- [[_COMMUNITY_Hybrid Search Demo Script|Hybrid Search Demo Script]]
- [[_COMMUNITY_Ingestion Embedder Methods|Ingestion Embedder Methods]]
- [[_COMMUNITY_Reranker & Search Rationale|Reranker & Search Rationale]]
- [[_COMMUNITY_Golden Set Eval Data|Golden Set Eval Data]]
- [[_COMMUNITY_RAGAS LLM Adapter|RAGAS LLM Adapter]]
- [[_COMMUNITY_PMC Converter Prototype Functions|PMC Converter Prototype Functions]]
- [[_COMMUNITY_JSON Loader Service|JSON Loader Service]]
- [[_COMMUNITY_Similarity Search Demo Script|Similarity Search Demo Script]]
- [[_COMMUNITY_Chunk Metadata Test Rationale|Chunk Metadata Test Rationale]]
- [[_COMMUNITY_Chunker Main & Tests|Chunker Main & Tests]]
- [[_COMMUNITY_ExcelCSV Extraction (Duplicate)|Excel/CSV Extraction (Duplicate)]]
- [[_COMMUNITY_RAGAS Adapter Tests|RAGAS Adapter Tests]]
- [[_COMMUNITY_RAGAS Adapter Stub & Embedder|RAGAS Adapter Stub & Embedder]]
- [[_COMMUNITY_Loader Text Cleaning & JSON Parse|Loader Text Cleaning & JSON Parse]]
- [[_COMMUNITY_Chunk Metadata Extraction Tests|Chunk Metadata Extraction Tests]]
- [[_COMMUNITY_Chunker Service Methods|Chunker Service Methods]]
- [[_COMMUNITY_PDF Extraction Prototype|PDF Extraction Prototype]]
- [[_COMMUNITY_PDF Loader Section Path|PDF Loader Section Path]]
- [[_COMMUNITY_Basic Ingestion Helper Functions|Basic Ingestion Helper Functions]]
- [[_COMMUNITY_Incident Handler & Settings|Incident Handler & Settings]]
- [[_COMMUNITY_Text Loader Service|Text Loader Service]]
- [[_COMMUNITY_BM25 Search Demo Functions|BM25 Search Demo Functions]]
- [[_COMMUNITY_Skills Lock & Qdrant Advisor|Skills Lock & Qdrant Advisor]]
- [[_COMMUNITY_Tests Package Init|Tests Package Init]]
- [[_COMMUNITY_Baseline Migration Downgrade|Baseline Migration Downgrade]]
- [[_COMMUNITY_Incident Handler Graph Reference|Incident Handler Graph Reference]]
- [[_COMMUNITY_BM25 Index Load|BM25 Index Load]]
- [[_COMMUNITY_BM25 Index Save|BM25 Index Save]]
- [[_COMMUNITY_Chat Router Streaming|Chat Router Streaming]]
- [[_COMMUNITY_Chunk Store Failed Add|Chunk Store Failed Add]]
- [[_COMMUNITY_Chunk Store Failed Get|Chunk Store Failed Get]]
- [[_COMMUNITY_CLAUDE.md Rule 2|CLAUDE.md Rule 2]]
- [[_COMMUNITY_CLAUDE.md Rule 4|CLAUDE.md Rule 4]]
- [[_COMMUNITY_Bug Doc Index|Bug Doc Index]]
- [[_COMMUNITY_PMC Fetcher Module Concept|PMC Fetcher Module Concept]]
- [[_COMMUNITY_Incident Writeup Template|Incident Writeup Template]]
- [[_COMMUNITY_CSV Loader Function|CSV Loader Function]]
- [[_COMMUNITY_Excel Loader Function|Excel Loader Function]]
- [[_COMMUNITY_JSON Loader Function|JSON Loader Function]]
- [[_COMMUNITY_PDF Loader Function|PDF Loader Function]]
- [[_COMMUNITY_Text Loader Load Function|Text Loader Load Function]]
- [[_COMMUNITY_SQL Query Builder|SQL Query Builder]]
- [[_COMMUNITY_SQL Query With Eligibility|SQL Query With Eligibility]]
- [[_COMMUNITY_Chunk Content Hash|Chunk Content Hash]]
- [[_COMMUNITY_IngestedDocument Content Hash|IngestedDocument Content Hash]]

## God Nodes (most connected - your core abstractions)
1. `Chunk` - 57 edges
2. `LoaderConfig` - 51 edges
3. `ChunkerService` - 47 edges
4. `PDFLoaderService` - 34 edges
5. `medical-ingestion Architecture Bundle Index` - 34 edges
6. `Embedder` - 32 edges
7. `Settings` - 31 edges
8. `LiteLLMModelParams` - 30 edges
9. `Document` - 29 edges
10. `ChunkStore` - 29 edges

## Surprising Connections (you probably didn't know these)
- `papers_to_json()` --shares_data_with--> `JSONLoaderService`  [EXTRACTED]
  doc/feature/pmc_json_converter.md → ingestion/loaders/json_loader.py
- `build_ragas_llm()` --calls--> `ChatRouterService`  [EXTRACTED]
  doc/feature/ragas_adapters.md → llm/chat_router.py
- `Basic Document Ingestion script` --conceptually_related_to--> `ChunkerService`  [EXTRACTED]
  doc/feature/basic_document_ingestion.md → ingestion/chunker.py
- `Chunker` --implements--> `ChunkerService`  [EXTRACTED]
  doc/feature/chunker.md → ingestion/chunker.py
- `chunk_documents()` --calls--> `ChunkerService`  [EXTRACTED]
  doc/feature/ingest_documents_script.md → ingestion/chunker.py

## Import Cycles
- 1-file cycle: `llm/chat_router.py -> llm/chat_router.py`
- 1-file cycle: `tests/test_chat_router.py -> tests/test_chat_router.py`

## Hyperedges (group relationships)
- **RAGAS evaluation pipeline (golden set -> live pipeline -> judge LLM scoring)** — eval_llm_golden_set_golden_set, eval_ragas_runner_ragasevalrunner, eval_ragas_adapters_build_ragas_llm, eval_ragas_adapters_build_ragas_embeddings [INFERRED 0.85]
- **LoaderFactory constructs configured loader services from shared LoaderConfig** — loaders_factory_loaderfactory, loaders_base_loaderconfig, loaders_excel_csv_excelcsvloaderservice, chunker_load_all_documents [EXTRACTED 1.00]
- **Standalone loader prototype scripts mirroring production loaders** — individual_scripts_basic_document_ingestion, individual_scripts_excel_csv_extraction, individual_scripts_json_extraction, individual_scripts_pdf_extraction [INFERRED 0.80]
- **PMC fetch -> JSON convert -> PDF render pipeline for synthetic ingestion fixtures** — individual_scripts_pmc_json_converter, individual_scripts_json_to_pdf, pmc_documents_json [EXTRACTED 1.00]
- **litellm Router construction from validated pydantic config models** — chat_router_chatrouterservice, config_chatrouterconfig, config_litellmdeployment, config_litellmmodelparams [EXTRACTED 1.00]
- **Hybrid retrieval pipeline: dense + sparse fusion, rerank, cite** — bm25_bm25index, hybrid_hybridretriever, reranker_reranker, search_searchservice [EXTRACTED 0.90]
- **content_hash-based dedup shared across storage and index layers** — vectors_chunk, vectors_ingesteddocument, bm25_bm25index_build, hybrid_hybridretriever_search [INFERRED 0.85]
- **Alembic migration chain managing SQLModel schema** — env_run_migrations_online, 7468fa8fd0b2_baseline_upgrade, 32cedf430be3_add_section_path_and_page_number_fields__upgrade [EXTRACTED 0.90]
- **Document Ingestion Pipeline (load -> chunk -> embed -> store -> index)** — ingest_documents_main, ingest_documents_chunk_documents, ingest_documents_embed_and_store, chunk_store_chunkstore, qdrant_qdrantvectorstore, ingest_documents_rebuild_bm25_index [EXTRACTED 1.00]
- **Content-hash dedup/cache across Postgres and Qdrant** — chunk_store_find_by_hash, chunk_store_sync_to_qdrant, qdrant_find_by_hash, qdrant_upsert_one [EXTRACTED 1.00]
- **Interactive search demo scripts (BM25/dense/hybrid)** — bm25_search_demo_main, similarity_search_demo_main, hybrid_search_demo_main [INFERRED 0.85]
- **Self-Healing Documentation Pipeline** — settings_json_doc_sync_hook, doc_sync_agent, implementation_plan_md, agents_md_rule4_doc_sync_agent [EXTRACTED 1.00]
- **Bug Report to Incident Doc Flow** — incident_handler_agent, agents_md_rule3_incident_agent, claude_md, agents_md_rule2_okf_bundles [EXTRACTED 1.00]
- **Local RAG Infrastructure Stack** — docker_compose_postgres_yml, docker_compose_qdrant_yml, implementation_plan_infrastructure, implementation_plan_embedder_storage, implementation_plan_vector_db [INFERRED 0.85]
- **Production retrieval + generation pipeline (query to answer)** — hybrid_search_retrieval_hybridretriever, reranker_reranker_class, search_service_searchservice_class, chat_router_chatrouterservice, citation_mapping_six_layer_architecture [EXTRACTED 1.00]
- **Ingestion pipeline stages (load to Qdrant sync)** — loaders_loaderfactory, chunker_chunkerservice, embedder_embedder_class, chunk_store_chunkstore_class, qdrant_infrastructure_qdrantvectorstore [EXTRACTED 1.00]
- **RAGAS evaluation loop over live pipeline** — ragas_runner_ragasevalrunner, ragas_adapters_ragas_adapters, llm_golden_set_llm_golden_set, search_service_searchservice_class [EXTRACTED 1.00]

## Communities (84 total, 26 thin omitted)

### Community 0 - "LLM Chat Router"
Cohesion: 0.06
Nodes (40): BaseSettings, ChatRouterConfig, ChatRouterService.__init__, ChatRouterService.complete, ChatRouterService.from_settings, LiteLLMDeployment, LiteLLMModelParams, OpenRouter->Groq->OpenRouter fallback chain (+32 more)

### Community 1 - "Clinical Trials Fetcher"
Cohesion: 0.05
Nodes (61): ClinicalTrials Fetcher, fetch_dummy_trials, parse_eligibility, parse_trial, search_trials, Counter, main (visualize_db), print_counts (+53 more)

### Community 2 - "Agent Rules & Guidelines"
Cohesion: 0.06
Nodes (68): Behavioral Guidelines, Rule 10: Medical Data Sources API Integration, Rule 11: OpenRouter MCP Guard, Rule 1: Implementation Plan, Rule 2: doc/ OKF Bundle Structure, Rule 3: Dedicated Agent for Bug Handling, Rule 4: Doc-Sync Agent for Architecture Docs, Rule 5: Knowledge Graph Before Code (+60 more)

### Community 3 - "Chunking Data Models"
Cohesion: 0.07
Nodes (49): BaseModel, Chunk, ChunkerConfig, Config, Configuration for text chunking., load_json_documents(), Document, Path (+41 more)

### Community 4 - "Chunk Store & Dedup"
Cohesion: 0.06
Nodes (34): ABC, ChunkStore.document_seen, ChunkStore.get_all_chunks, ChunkStore.mark_document_seen, Engine, FailedEmbedding, start_postgres.sh script, chunk_documents (+26 more)

### Community 5 - "Loader Factory Pattern"
Cohesion: 0.17
Nodes (19): _load_all_documents, ExcelCSVLoaderService, Path, JSONLoaderService, LoaderFactory (re-export), ExcelCSVLoaderService, Load Excel and CSV files using Unstructured for intelligent structure extraction, LoaderFactory (+11 more)

### Community 6 - "Document Chunking Logic"
Cohesion: 0.11
Nodes (15): chunk_documents(), ChunkerService, Convert Documents to Chunks using configurable strategy., Convert Documents to chunked Documents using RecursiveCharacterTextSplitter,, Test handling of sibling sections (H2 under same H1)., Tests for markdown header splitting and section_path extraction., Test that deeper levels are reset when a shallower level reappears., Test markdown splitting with single H1 header. (+7 more)

### Community 7 - "Architecture Decisions"
Cohesion: 0.13
Nodes (23): System Architecture Overview, Five-Layer RAG Pipeline, Hybrid search (dense+sparse) decision, Postgres cache vs pgvector decision, Chunker, ChunkerConfig, File and Folder Structure, Hybrid Search Retrieval (+15 more)

### Community 8 - "Ingestion Script Pipeline"
Cohesion: 0.15
Nodes (23): chunk_documents(), embed_and_store(), filter_seen_documents(), ingest_csv_excel_documents(), ingest_json_documents(), ingest_pdf_documents(), main(), ChunkStore (+15 more)

### Community 9 - "Qdrant Vector Store Setup"
Cohesion: 0.11
Nodes (12): start_qdrant.sh script, QdrantVectorStore._ensure_collection, QdrantVectorStore._ensure_payload_indexes, QdrantClient, QdrantVectorStore, BM25Index, QdrantVectorStore, Qdrant vector store — one point per unique content_hash.  Per-occurrence provena (+4 more)

### Community 10 - "Alembic Migrations & BM25 Build"
Cohesion: 0.11
Nodes (19): downgrade (drop section_path/page_number), upgrade (add section_path/page_number), upgrade (baseline, no-op), BM25Index.build, Document/Chunk superseded note, run_migrations_offline, run_migrations_online, Chunk (+11 more)

### Community 11 - "JSON-to-PDF Conversion Scripts"
Cohesion: 0.13
Nodes (19): convert_all, doc_to_pdf, convert_all(), doc_to_pdf(), Render pmc_documents.json entries to real PDF files for exercising the PDF inges, safe_filename(), fetch_and_save_json(), fetch_pmc_full_text() (+11 more)

### Community 12 - "Hybrid Retrieval Search"
Cohesion: 0.13
Nodes (11): HybridRetriever, Hybrid retriever — reciprocal rank fusion over Qdrant dense search + BM25 sparse, Fuses dense + sparse rankings by reciprocal rank, not raw score — cosine similar, Search service — embed query, fuse dense+sparse via RRF, rerank with a cross-enc, Owns the full retrieval stack: BM25 + Qdrant + RRF fusion + cross-encoder rerank, Layer 5: Parse inline citations [1], [2], etc. from LLM answer.          Returns, Stream an LLM answer grounded in the given chunks with citation markers., SearchService (+3 more)

### Community 13 - "Chunk Store Embedding Sync"
Cohesion: 0.12
Nodes (20): ChunkStore, ChunkStore.find_by_hash, ChunkStore.insert_chunks, ChunkStore.sync_to_qdrant, Embedder._embed_batch(), Embedder.embed(), Embedder, EmbedderError (+12 more)

### Community 14 - "Alembic Migration Management"
Cohesion: 0.17
Nodes (18): Alembic Migrations, Baseline Revision 7468fa8fd0b2, create_all drift risk, migrations/env.py, migrations/ (Alembic), Revision 32cedf430be3 (section_path/page_number), Chunk Store, Per-occurrence provenance dedup rationale (+10 more)

### Community 15 - "Chunker Markdown Sectioning"
Cohesion: 0.12
Nodes (10): Document, Split Documents into Chunks with metadata preservation., Check if text contains markdown-style headers (#, ##, ###)., Split text by markdown headers, return Documents with section metadata., Prepend section to page_content if section metadata exists and is non-null., Split Documents into smaller Documents, metadata propagated by LangChain., Test plain text document → section_path is None, page_number is None., Test that section_path is correctly extracted from chunk metadata to Chunk row. (+2 more)

### Community 16 - "PDF Loader Tests"
Cohesion: 0.18
Nodes (17): PDFLoaderService, Load PDFs via Docling and return LangChain Documents with structured metadata., create_test_pdf_with_headings(), Tests for PDF loader with section_path extraction., Test that flattened section string is still populated for backward compatibility, Test that loader handles PDFs without headings gracefully., Test that page numbers are extracted correctly., Create a test PDF with nested heading hierarchy (H1 > H2 > H3). (+9 more)

### Community 17 - "BM25 Index Implementation"
Cohesion: 0.14
Nodes (11): BM25Index, Chunk, Path, BM25 sparse lexical index over chunks — companion to Qdrant's dense index.  Rebu, Wraps bm25s.BM25 with a corpus of {content_hash, text, metadata} aligned to, Index one entry per unique content_hash (first occurrence wins), mirroring, Returns (corpus_entry, score) pairs, highest score first., main() (+3 more)

### Community 18 - "Citation Mapping & RAG Answers"
Cohesion: 0.15
Nodes (17): _enrich_with_citations(), extract_citations_from_answer(), 6-Layer Citation Architecture, HybridRetriever, GOLDEN_SET (37 items), LLM Answer Golden Set, langchain_community vertexai stub workaround, collect_live_records() (+9 more)

### Community 19 - "Base Loader Config"
Cohesion: 0.18
Nodes (12): Document, Path, clean_text(), LoaderConfig, Clean extracted text from encoding issues, whitespace, and artifacts., Configuration for document loaders., Config, ExcelCSVLoaderService._load (+4 more)

### Community 20 - "BM25 & Citation Concepts"
Cohesion: 0.25
Nodes (14): BM25 Sparse Index, BM25Index, content_hash keying (no id-mapping needed), BM25 Search Demo, Citation Mapping in Retrieval Results, Hybrid Search Demo, medical-ingestion Architecture Bundle Index, Qdrant Infrastructure (+6 more)

### Community 21 - "RAGAS Eval Runner"
Cohesion: 0.25
Nodes (7): main(), Path, RagasEvalRunner, RAGAS evaluation runner — scores the live retrieval+generation pipeline (retriev, Owns the golden-set-to-scored-result lifecycle: load golden set, run the     liv, Run the live pipeline once per golden set item. Sequential — SearchService, EvaluationDataset

### Community 22 - "Chunk Metadata Integration Tests"
Cohesion: 0.20
Nodes (8): create_test_pdf_with_headings, Test PDF with 2-level nesting (H1 > H2) → section_path propagates correctly., Test PDF chunks have page_number populated as int., Test that section_path structure exactly matches heading hierarchy., Integration tests for PDF pipeline: load → chunk → embed → Chunk rows., Create a test PDF with 3-level nesting (H1 > H2 > H3)., Test PDF with nested structure → section_path propagates through pipeline with c, TestIntegrationPDFSectionPathAndPageNumber

### Community 23 - "Embedding Cache Rationale"
Cohesion: 0.18
Nodes (12): Chat Router (litellm fallback chain), Provider-level fallback chain rationale, Postgres ChunkStore as read-only embedding cache, One embeddings implementation shared by ingestion and eval, Cache-check cost-saving rationale, Embeddings, build_ragas_embeddings(), Wrap the same Embedder used by ingestion (Postgres-cached OpenRouter embeddings) (+4 more)

### Community 24 - "Excel/JSON Ingestion Scripts"
Cohesion: 0.18
Nodes (8): Excel/CSV Extraction (reference script), Ingest Pipeline Script, JSON Extraction (reference script), ExcelCSVLoaderService, get_logger(), Structured Logging Configuration, Structured JSON logging rationale, PDF Extraction (reference script)

### Community 25 - "Main CLI Entry Point"
Cohesion: 0.20
Nodes (11): BM25Index.search, HybridRetriever.search, display_results(), main(), Interactive medical document search — hybrid retrieval (dense + BM25, RRF-fused), Reranker.rerank, embed_query, SearchService.answer (+3 more)

### Community 26 - "Prototype Excel/JSON Scripts"
Cohesion: 0.20
Nodes (10): load_csv_documents(), load_excel_documents(), Load all CSV files from directory using Unstructured for intelligent parsing., Load all Excel files from directory using Unstructured for intelligent parsing., load_json_documents(), Load all JSON files from directory, treating each top-level object     (or each, Document, Path (+2 more)

### Community 27 - "Ingest Documents Tests"
Cohesion: 0.17
Nodes (11): Tests for ingest_documents.py - verifies section_path and page_number extraction, Test extraction when chunk metadata comes from markdown loader., Test that Chunk rows are constructed with section_path and page_number extracted, Test extraction when metadata doesn't have section_path or page_number keys., Test that section_path and page_number fields are independent of metadata_ dict., Test extraction when chunk metadata comes from PDF loader (realistic scenario)., test_chunk_extraction_from_markdown_metadata(), test_chunk_extraction_from_pdf_metadata() (+3 more)

### Community 28 - "PMC JSON Converter"
Cohesion: 0.25
Nodes (10): fetch_and_save_json(), fetch_pmc_full_text(), papers_to_json(), Path, Fetch PMC papers and convert to structured JSON with rich metadata., Convert fetched papers to JSON format with rich metadata., Search PMC for open-access papers., Fetch papers from PMC and save as JSON. (+2 more)

### Community 29 - "Basic Document Ingestion Prototype"
Cohesion: 0.33
Nodes (9): ingest_from_directory(), ingest_single_file(), load_single_dummy_pubmed(), load_text_file(), Load plain text file and return Document object.     Ref: https://docs.langchain, Ingest a single text file and return chunked Document objects.      Args:, Load all text files from a directory and return chunked Document objects.      A, Load dummy PubMed data from dummy_docs/pubmed directory using TextLoader.      R (+1 more)

### Community 30 - "PMC Fetcher Prototype"
Cohesion: 0.27
Nodes (9): fetch_dummy_papers(), fetch_pmc_full_text(), Fetch full-text papers from PMC Open Access and save to dummy_docs., Save paper to text file in dummy_docs.      Args:         paper: Paper dict from, Search PMC for open-access papers.      Args:         query: Search query, Fetch and save dummy papers from PMC.      Args:         query: Search query, Fetch full text of PMC paper.      Args:         pmcid: PMC ID      Returns:, save_paper() (+1 more)

### Community 31 - "Basic Document Ingestion (Duplicate)"
Cohesion: 0.33
Nodes (9): ingest_from_directory(), ingest_single_file(), load_single_dummy_pubmed(), load_text_file(), Document, Load plain text file and return Document object.     Ref: https://docs.langchain, Ingest a single text file and return chunked Document objects.      Args:, Load all text files from a directory and return chunked Document objects.      A (+1 more)

### Community 32 - "PMC Fetcher (Duplicate)"
Cohesion: 0.27
Nodes (9): fetch_dummy_papers(), fetch_pmc_full_text(), Fetch full-text papers from PMC Open Access and save to dummy_docs., Search PMC for open-access papers.      Args:         query: Search query, Fetch and save dummy papers from PMC.      Args:         query: Search query, Fetch full text of PMC paper.      Args:         pmcid: PMC ID      Returns:, Save paper to text file in dummy_docs.      Args:         paper: Paper dict from, save_paper() (+1 more)

### Community 33 - "Basic Ingestion & PMC Prototypes"
Cohesion: 0.22
Nodes (5): Basic Document Ingestion script, load_single_dummy_pubmed(), PMC Fetcher, papers_to_json(), PMC JSON Converter

### Community 34 - "Embedder Methods"
Cohesion: 0.25
Nodes (8): Embedder.embed, Embedder._embed_batch, Embedder.embed_documents, Embedder.embed_one, Embedder.embed_query, Embedder.embed_with_hashes, EmbedderError, Raised when the OpenRouter embeddings request fails.

### Community 35 - "Hybrid/Similarity Search Demos"
Cohesion: 0.25
Nodes (9): embed_query, main, search_hybrid, stream_llm_response, QdrantVectorStore.search, embed_query, main, search_similarity (+1 more)

### Community 36 - "Hybrid Search Demo Script"
Cohesion: 0.33
Nodes (8): HybridRetriever, embed_query(), main(), Stream LLM response via LangChain OpenRouter, grounding in search results., Embed text via OpenRouter API., Search dense+sparse fused results, display them, and stream LLM response., search_hybrid(), stream_llm_response()

### Community 37 - "Ingestion Embedder Methods"
Cohesion: 0.25
Nodes (4): Embed a list of texts, using Postgres as a cache and batching API calls, Embed a single text string., Embed texts and return their content hashes alongside the vectors, so callers, langchain_core.embeddings.Embeddings interface method, for ragas/LangChain calle

### Community 38 - "Reranker & Search Rationale"
Cohesion: 0.22
Nodes (6): Rerank fused candidates (each carrying a `text` key) by relevance to `query`., embed_query(), Embed text via OpenRouter API., Fuse dense+sparse candidates, then rerank the fused shortlist for final order., Layer 1: Add citation metadata to each result for downstream layers., RuntimeError

### Community 39 - "Golden Set Eval Data"
Cohesion: 0.32
Nodes (6): GOLDEN_SET (retrieval), main(), Golden set generation script for retrieval eval.  Builds eval/golden_set.json fr, GOLDEN_SET (RAGAS), main(), Golden set generation script for LLM answer-generation eval (retrieval/search.py

### Community 40 - "RAGAS LLM Adapter"
Cohesion: 0.25
Nodes (7): build_ragas_llm(), _ensure_openrouter_prefix(), Bare OpenRouter model ids (the old ChatOpenRouter-era convention, still     what, Wrap ChatRouterService (OpenRouter->Groq->OpenRouter fallback) as the     RAGAS, ragas vertexai import stub workaround, LangchainLLMWrapper, SearchService

### Community 41 - "PMC Converter Prototype Functions"
Cohesion: 0.29
Nodes (8): fetch_and_save_json, fetch_dummy_papers, fetch_pmc_full_text (converter), fetch_pmc_full_text (fetcher), papers_to_json, save_paper, search_pmc_papers (converter), search_pmc_papers (fetcher)

### Community 42 - "JSON Loader Service"
Cohesion: 0.29
Nodes (5): Document, Path, Flatten nested JSON to dot notation for queryable metadata., Load all .json files and extract max metadata., Load single JSON file with nested metadata preservation.

### Community 43 - "Similarity Search Demo Script"
Cohesion: 0.36
Nodes (7): embed_query(), main(), Stream LLM response via LangChain OpenRouter, grounding in search results., Embed text via OpenRouter API., Search for similar chunks, display results, and stream LLM response., search_similarity(), stream_llm_response()

### Community 44 - "Chunk Metadata Test Rationale"
Cohesion: 0.25
Nodes (5): Integration tests for Markdown pipeline: load → chunk → embed → Chunk rows., Test Markdown with 3-level nesting (H1 > H2 > H3) → section_path has 3 elements,, Test Markdown chunks have page_number as None., Test Markdown without headers → section_path is None, page_number is None., TestIntegrationMarkdownSectionPath

### Community 45 - "Chunker Main & Tests"
Cohesion: 0.33
Nodes (5): _load_all_documents(), main(), Load Documents from every loader source, skipping sources with no data., Chunk Documents from every loader source and print one sample chunk per source t, Tests for ChunkerService, including markdown header section_path extraction.

### Community 46 - "Excel/CSV Extraction (Duplicate)"
Cohesion: 0.38
Nodes (6): load_csv_documents(), load_excel_documents(), Document, Path, Load all CSV files from directory using Unstructured for intelligent parsing., Load all Excel files from directory using Unstructured for intelligent parsing.

### Community 48 - "RAGAS Adapter Stub & Embedder"
Cohesion: 0.33
Nodes (4): Wires RAGAS's judge LLM and embeddings onto this repo's existing OpenRouter stac, Placeholder — never instantiated. See workaround comment above., _StubChatVertexAI, Embedding service backed by OpenRouter's /embeddings endpoint.

### Community 49 - "Loader Text Cleaning & JSON Parse"
Cohesion: 0.33
Nodes (6): clean_text, JSONLoaderService._flatten_metadata, JSONLoaderService._load_json, JSONLoaderService.load, PDFLoaderService._extract_section_path_from_document, PDFLoaderService.load

### Community 50 - "Chunk Metadata Extraction Tests"
Cohesion: 0.33
Nodes (5): End-to-end integration tests for section_path depth and page_number.  Validates, Integration tests for plain text documents., Integration tests for section_path and page_number extraction in ingest_document, TestIntegrationChunkMetadataExtraction, TestIntegrationPlainTextDocument

### Community 51 - "Chunker Service Methods"
Cohesion: 0.40
Nodes (5): ChunkerService.chunk, ChunkerService._has_markdown_headers, ChunkerService._inject_section_context, ChunkerService._split_by_markdown_headers, chunker.main

### Community 52 - "PDF Extraction Prototype"
Cohesion: 0.40
Nodes (4): load_pdf_documents(), Load all PDF files from directory using Docling for structure-aware parsing., Document, Path

### Community 53 - "PDF Loader Section Path"
Cohesion: 0.40
Nodes (3): Document, Extract hierarchical section path with heading levels from Docling document., Load all PDFs from directory and return Documents.          Uses a single Doclin

### Community 54 - "Basic Ingestion Helper Functions"
Cohesion: 0.50
Nodes (4): ingest_from_directory, ingest_single_file, load_single_dummy_pubmed, load_text_file

### Community 55 - "Incident Handler & Settings"
Cohesion: 0.67
Nodes (3): incident-handler Agent, Allow Bash(python3 *) Permission, Local Claude Settings Permissions

## Ambiguous Edges - Review These
- `Allow Bash(python3 *) Permission` → `incident-handler Agent`  [AMBIGUOUS]
  .claude/settings.local.json · relation: conceptually_related_to
- `Chunker (concept doc)` → `README.md`  [AMBIGUOUS]
  README.md · relation: semantically_similar_to
- `Loaders (concept doc)` → `README.md`  [AMBIGUOUS]
  README.md · relation: semantically_similar_to
- `ChunkerConfig/RecursiveChunker Doc-Code Mismatch` → `INGESTION_GUIDE.md`  [AMBIGUOUS]
  INGESTION_GUIDE.md · relation: conceptually_related_to
- `Claude Code settings.json (hooks)` → `Doc-Sync PostToolUse Hook`  [AMBIGUOUS]
  .claude/settings.json · relation: shares_data_with
- `Per-occurrence provenance dedup rationale` → `Reciprocal Rank Fusion (fuse by rank not score)`  [AMBIGUOUS]
  doc/feature/hybrid_search_retrieval.md · relation: semantically_similar_to

## Knowledge Gaps
- **113 isolated node(s):** `Local Claude Settings Permissions`, `incident-handler Agent`, `Graphify Knowledge Graph (investigation aid)`, `doc/INDEX.md Incident Index`, `doc/incidents/INC-XXX-short-slug.md Write-up Template` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Allow Bash(python3 *) Permission` and `incident-handler Agent`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Chunker (concept doc)` and `README.md`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Loaders (concept doc)` and `README.md`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `ChunkerConfig/RecursiveChunker Doc-Code Mismatch` and `INGESTION_GUIDE.md`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Claude Code settings.json (hooks)` and `Doc-Sync PostToolUse Hook`?**
  _Edge tagged AMBIGUOUS (relation: shares_data_with) - confidence is low._
- **What is the exact relationship between `Per-occurrence provenance dedup rationale` and `Reciprocal Rank Fusion (fuse by rank not score)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `ChunkerService` connect `Document Chunking Logic` to `Basic Ingestion & PMC Prototypes`, `Chunking Data Models`, `Architecture Decisions`, `Ingestion Script Pipeline`, `Chunk Metadata Test Rationale`, `Chunker Main & Tests`, `Chunker Markdown Sectioning`, `Chunk Metadata Extraction Tests`, `Chunker Service Methods`, `Base Loader Config`, `Chunk Metadata Integration Tests`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._