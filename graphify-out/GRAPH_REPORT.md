# Graph Report - .  (2026-08-12)

## Corpus Check
- 36 files · ~11,695 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 182 nodes · 373 edges · 23 communities (17 shown, 6 thin omitted)
- Extraction: 83% EXTRACTED · 16% INFERRED · 1% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.55)
- Token cost: 84,662 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Docs & Agent Specs|Docs & Agent Specs]]
- [[_COMMUNITY_Chunking Pipeline|Chunking Pipeline]]
- [[_COMMUNITY_Loaders Core Ops|Loaders Core Ops]]
- [[_COMMUNITY_Pydantic Data Models|Pydantic Data Models]]
- [[_COMMUNITY_PMC JSON Converter|PMC JSON Converter]]
- [[_COMMUNITY_ChunkerLoader Config|Chunker/Loader Config]]
- [[_COMMUNITY_Basic Document Ingestion|Basic Document Ingestion]]
- [[_COMMUNITY_Loader Factory|Loader Factory]]
- [[_COMMUNITY_PMC Fetcher|PMC Fetcher]]
- [[_COMMUNITY_Loader Text Cleaning|Loader Text Cleaning]]
- [[_COMMUNITY_ExcelCSV Extraction|Excel/CSV Extraction]]
- [[_COMMUNITY_JSON Loader Service|JSON Loader Service]]
- [[_COMMUNITY_App Settings|App Settings]]
- [[_COMMUNITY_JSON Extraction Script|JSON Extraction Script]]
- [[_COMMUNITY_PDF Extraction Script|PDF Extraction Script]]
- [[_COMMUNITY_Claude Local Settings|Claude Local Settings]]
- [[_COMMUNITY_Incident Handler Graphify Ref|Incident Handler Graphify Ref]]
- [[_COMMUNITY_CLAUDE Rule 2|CLAUDE Rule 2]]
- [[_COMMUNITY_CLAUDE Rule 4|CLAUDE Rule 4]]
- [[_COMMUNITY_Bug Index|Bug Index]]
- [[_COMMUNITY_PMC Fetcher Feature Doc|PMC Fetcher Feature Doc]]
- [[_COMMUNITY_Incident Writeup Template|Incident Writeup Template]]

## God Nodes (most connected - your core abstractions)
1. `Document` - 29 edges
2. `Metadata` - 25 edges
3. `doc/feature/index.md (Architecture Bundle Index)` - 17 edges
4. `Loaders (concept doc)` - 14 edges
5. `Chunk` - 13 edges
6. `ChunkerService` - 11 edges
7. `LoaderFactory` - 11 edges
8. `Ingest Pipeline Script (concept doc)` - 11 edges
9. `ChunkerConfig` - 10 edges
10. `ExcelCSVLoaderService` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Path` --uses--> `Document`  [INFERRED]
  ingestion/json_extraction.py → models/documents.py
- `Document` --uses--> `Document`  [INFERRED]
  ingestion/json_extraction.py → models/documents.py
- `Path` --uses--> `Document`  [INFERRED]
  ingestion/pdf_extraction.py → models/documents.py
- `Document` --uses--> `Document`  [INFERRED]
  ingestion/pdf_extraction.py → models/documents.py
- `Allow Bash(python3 *) Permission` --conceptually_related_to--> `incident-handler Agent`  [AMBIGUOUS]
  .claude/settings.local.json → .claude/agents/incident-handler.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Incident Handling Workflow (CLAUDE.md rules #2/#4 + incident-handler agent)** — agents_incident_handler_incident_handler, doc_index_incident_index, incidents_inc_xxx_short_slug_incident_writeup, claude_rule_2, claude_rule_4, agents_incident_handler_graphify_knowledge_graph [INFERRED 0.85]
- **Standalone Reference Scripts Superseded by Production Loaders** — feature_pdf_extraction_doc, feature_json_extraction_doc, feature_excel_csv_extraction_doc, feature_basic_document_ingestion_doc, feature_loaders_doc [EXTRACTED 1.00]
- **OKF Self-Healing Documentation System** — agents_rules_doc, claude_overrides_doc, doc_index_root, feature_index_bundle, bug_index_bundle, agents_doc_sync_agent, agents_incident_handler_agent [EXTRACTED 1.00]
- **Core Production Ingestion Pipeline (Load -> Chunk)** — feature_loaders_doc, feature_chunker_doc, feature_ingest_documents_script_doc, feature_models_doc, feature_pmc_json_converter_doc [EXTRACTED 1.00]

## Communities (23 total, 6 thin omitted)

### Community 0 - "Docs & Agent Specs"
Cohesion: 0.12
Nodes (34): doc-sync Agent, incident-handler Agent, doc/bug/index.md (Incident Bundle Index), ChunkerConfig/RecursiveChunker Doc-Code Mismatch, Medical Data Sources API Strategy (rule #9), OKF (Open Knowledge Format v0.2) Bundle, Pydantic Models Single Source of Truth (rule #6), Self-Healing Documentation (+26 more)

### Community 1 - "Chunking Pipeline"
Cohesion: 0.20
Nodes (17): ChunkerConfig, ChunkerService, Config, Configuration for text chunking., Convert Documents to Chunks using configurable strategy., chunk_documents(), ingest_csv_excel_documents(), ingest_json_documents() (+9 more)

### Community 2 - "Loaders Core Ops"
Cohesion: 0.23
Nodes (8): ExcelCSVLoaderService, Document, Load all .txt files from directory and return raw Documents (no chunking)., Load Excel and CSV files using Unstructured for intelligent structure extraction, Load all .csv and .xlsx files from directory and return Documents., Load single CSV file using Unstructured., Load Excel file using Unstructured (handles multiple sheets)., Load all .json files and extract max metadata.

### Community 3 - "Pydantic Data Models"
Cohesion: 0.44
Nodes (8): BaseModel, Chunk, RAGQuery, RAGResponse, RetrievedContext, EmbeddingRequest, EmbeddingResult, Vector

### Community 4 - "PMC JSON Converter"
Cohesion: 0.25
Nodes (10): fetch_and_save_json(), fetch_pmc_full_text(), papers_to_json(), Path, Fetch PMC papers and convert to structured JSON with rich metadata., Convert fetched papers to JSON format with rich metadata., Search PMC for open-access papers., Fetch papers from PMC and save as JSON. (+2 more)

### Community 5 - "Chunker/Loader Config"
Cohesion: 0.38
Nodes (8): Chunk, Document, Split Documents into Chunks with metadata preservation., Config, Load plain text files and convert to Pydantic Documents., TextLoaderService, Document, Metadata

### Community 6 - "Basic Document Ingestion"
Cohesion: 0.33
Nodes (9): ingest_from_directory(), ingest_single_file(), load_single_dummy_pubmed(), load_text_file(), Document, Load plain text file and return Document object.     Ref: https://docs.langchain, Ingest a single text file and return chunked Document objects.      Args:, Load all text files from a directory and return chunked Document objects.      A (+1 more)

### Community 7 - "Loader Factory"
Cohesion: 0.33
Nodes (6): LoaderConfig, LoaderFactory, Path, Configuration for document loaders., Factory for creating loaders based on source type., Create Excel/CSV loader.

### Community 8 - "PMC Fetcher"
Cohesion: 0.27
Nodes (9): fetch_dummy_papers(), fetch_pmc_full_text(), Fetch full-text papers from PMC Open Access and save to dummy_docs., Search PMC for open-access papers.      Args:         query: Search query, Fetch and save dummy papers from PMC.      Args:         query: Search query, Fetch full text of PMC paper.      Args:         pmcid: PMC ID      Returns:, Save paper to text file in dummy_docs.      Args:         paper: Paper dict from, save_paper() (+1 more)

### Community 9 - "Loader Text Cleaning"
Cohesion: 0.29
Nodes (4): PDFLoaderService, Load PDFs via Docling and convert to Pydantic Documents., Load all PDFs from directory and return raw Documents, Clean extracted text from encoding issues, whitespace, and artifacts.

### Community 10 - "Excel/CSV Extraction"
Cohesion: 0.38
Nodes (6): load_csv_documents(), load_excel_documents(), Document, Path, Load all CSV files from directory using Unstructured for intelligent parsing., Load all Excel files from directory using Unstructured for intelligent parsing.

### Community 11 - "JSON Loader Service"
Cohesion: 0.40
Nodes (4): JSONLoaderService, Load JSON files with complex nested metadata extraction., Load single JSON file with nested metadata preservation., Flatten nested JSON to dot notation for queryable metadata.

### Community 12 - "App Settings"
Cohesion: 0.33
Nodes (3): Configuration loaded from environment (shell priority > .env)., Validate required settings., Settings

### Community 13 - "JSON Extraction Script"
Cohesion: 0.40
Nodes (4): load_json_documents(), Document, Path, Load all JSON files from directory, treating each top-level object     (or each

### Community 14 - "PDF Extraction Script"
Cohesion: 0.40
Nodes (4): load_pdf_documents(), Document, Path, Load all PDF files from directory using Docling for structure-aware parsing.

### Community 15 - "Claude Local Settings"
Cohesion: 0.67
Nodes (3): incident-handler Agent, Allow Bash(python3 *) Permission, Local Claude Settings Permissions

## Ambiguous Edges - Review These
- `Allow Bash(python3 *) Permission` → `incident-handler Agent`  [AMBIGUOUS]
  .claude/settings.local.json · relation: conceptually_related_to
- `INGESTION_GUIDE.md` → `ChunkerConfig/RecursiveChunker Doc-Code Mismatch`  [AMBIGUOUS]
  INGESTION_GUIDE.md · relation: conceptually_related_to
- `README.md` → `Chunker (concept doc)`  [AMBIGUOUS]
  README.md · relation: semantically_similar_to
- `README.md` → `Loaders (concept doc)`  [AMBIGUOUS]
  README.md · relation: semantically_similar_to

## Knowledge Gaps
- **14 isolated node(s):** `Local Claude Settings Permissions`, `incident-handler Agent`, `Graphify Knowledge Graph (investigation aid)`, `doc/INDEX.md Incident Index`, `doc/incidents/INC-XXX-short-slug.md Write-up Template` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Allow Bash(python3 *) Permission` and `incident-handler Agent`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `INGESTION_GUIDE.md` and `ChunkerConfig/RecursiveChunker Doc-Code Mismatch`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `README.md` and `Chunker (concept doc)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `README.md` and `Loaders (concept doc)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `Document` connect `Chunker/Loader Config` to `Chunking Pipeline`, `Loaders Core Ops`, `Pydantic Data Models`, `Basic Document Ingestion`, `Loader Factory`, `Loader Text Cleaning`, `Excel/CSV Extraction`, `JSON Loader Service`, `JSON Extraction Script`, `PDF Extraction Script`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Why does `Metadata` connect `Chunker/Loader Config` to `Chunking Pipeline`, `Loaders Core Ops`, `Pydantic Data Models`, `Loader Factory`, `Loader Text Cleaning`, `JSON Loader Service`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `Document` connect `Basic Document Ingestion` to `Chunker/Loader Config`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._