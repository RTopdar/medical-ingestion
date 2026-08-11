# Agent Instructions — medical-ingestion

These rules apply to any AI coding agent working in this repo.

## 1. Implementation Plan

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) holds the architecture and design of this project.
- Update it every time something new is added (module, service, dependency, major decision). Treat drift between this file and the actual code as a bug.
- Before starting non-trivial work, read this file first.

## 2. Bug/Issue Handling via `doc/`

- [doc/INDEX.md](doc/INDEX.md) is the incident index. Every incident gets an ID (`INC-XXX`) and a one-line summary in the index table, plus its own file under `doc/incidents/`.
- **When a new problem is reported:**
  1. Check `doc/INDEX.md` first for a matching or related incident. If a resolution already exists, apply/reference it — do not re-derive from scratch.
  2. If nothing matches, only then investigate the codebase, fix it, and create a new incident file.
- **Each incident file must contain:**
  - Root cause
  - Resolution method
  - Final status: resolved or not resolved
- **When a new bug/issue is introduced** (by us or discovered as a side effect), it also gets logged in the index, not just fixes.
- Keep `doc/INDEX.md` continuously up to date — it's the source of truth for "has this happened before."

## 3. Dedicated Agent for Bug Handling

- Rule #2 (checking the index, investigating, writing up root cause/resolution, updating the index) should be delegated to a dedicated subagent rather than done inline in the main thread. Reason: dedicated agent stays focused on just this task, won't drop steps over a long session.
- Main thread's job: receive the problem report, hand it to the `incident-handler` subagent (`.claude/agents/incident-handler.md`), relay the result.

## 4. Doc-Sync Agent for Architecture Documentation

- Keep [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [AGENTS.md](AGENTS.md) in sync with the actual codebase.
- When code changes introduce new modules, services, major decisions, or agents, delegate to the `doc-sync` subagent (`.claude/agents/doc-sync.md`) to scan diffs and update docs.
- Doc-sync ensures architecture docs never drift from reality — treat code as source of truth, docs as the reflection.

## 5. Knowledge Graph Before Code

- This project uses `graphify` to build a persistent knowledge graph of the codebase.
- Before grepping/reading through code files to answer an architecture or "where is X" question, query the graphify knowledge graph first.
- Fall back to reading raw code only when the graph doesn't have the answer.

## 6. Pydantic Models — Single Source of Truth

- **All data structures use Pydantic models.** No plain dicts, tuples, or ad-hoc classes.
- **Location:** `models/` directory at project root, organized by domain:
  - `models/documents.py` — Document, Chunk, Metadata
  - `models/vectors.py` — Vector, EmbeddingRequest, EmbeddingResult
  - `models/rag.py` — RAGQuery, RAGResponse, RetrievedContext
- **Naming:** PascalCase classes (e.g., `Document`), snake_case files.
- **Enforcement:** Every module imports from `models.*`. Never define data classes in feature modules.
- **Update contract:** When adding a new data type, add its Pydantic model to the appropriate file in `models/` and update [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) in the same commit. No data model should appear in code before it's in `models/`.

## 7. LangChain — Always Consult MCP Docs First

- Whenever you encounter or need to generate **any LangChain code**, query the `docs-langchain` MCP server first.
- **Why:** LangChain APIs evolve; MCP docs are authoritative and current. Prevents writing deprecated or incorrect patterns.
- **Scope:** All `langchain*` packages — imports, class usage, chains, retrievers, agents, memory, callbacks, loaders, embeddings, vector stores.
- **Execution:** Use the MCP server or WebFetch to read current docs before writing code. Cite the doc link in comments if the pattern is non-obvious.

## 8. Virtual Environment — Always Activate First

- **Before running any Python command, check for and activate the virtual environment.**
- Look for `.venv/` directory in project root.
- Activate with: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
- Verify activation: prompt shows `(.venv)` prefix or `which python` returns `.venv/...`
- This applies to: `python`, `pip`, `pytest`, `uv run`, or any Python-based CLI tools
- **Never run naked Python commands** — always activate first to ensure correct dependencies and isolation

## 9. Medical Data Sources — API Integration

**Primary free APIs for medical/clinical data:**

- **PubMed E-utilities** (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`): 35M+ papers; no key; 3 req/sec rate limit. Methods: `esearch` (search), `efetch` (metadata + abstract), `elink` (related). Returns XML/JSON.

- **PMC Open Access** (subset via PubMed): ~2M freely available full-text papers; use db=pmc in E-utilities; same rate limits as PubMed. Provides complete article body text.

- **ClinicalTrials.gov API v2** (`https://clinicaltrials.gov/api/v2/`): 500K+ trials; no auth; search by condition/drug/phase/status/sponsor/location; returns normalized JSON.

**Strategy for paper data:**

1. Use **PubMed esearch** to find papers, get metadata + abstract
2. Use **PMC Open Access** to fetch full text of freely available papers (cross-reference via title/authors or direct PMC ID lookup)
3. Combine results: metadata (PubMed) + body text (PMC) in single ingestion record
4. Fall back to abstract-only for non-open-access papers

**When user requests dummy/sample data:**

- Default to these APIs (free, no credentials)
- Check data format preference (PDF, doc, JSON, XML, TXT)
- Build loaders supporting multiple output formats
- Pipeline handles structured (trials) + semi-structured (papers) data
- Document source and format in metadata for traceability
- **Always store to `dummy_docs/`** — single source of truth for test data
- Organize by source: `dummy_docs/pubmed/`, `dummy_docs/clinicaltrials/`
- Include format in filename: `full_paper_diabetes.txt`, `sample_pubmed_abstracts.json`, `trials_sample.csv`

## Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan and verify steps as you go.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
