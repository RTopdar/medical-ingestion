# Agent Instructions — medical-ingestion

These rules apply to any AI coding agent working in this repo.

## 1. Implementation Plan

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) holds the architecture and design of this project.
- Update it every time something new is added (module, service, dependency, major decision). Treat drift between this file and the actual code as a bug.
- Before starting non-trivial work, read this file first.

## 2. `doc/` Structure — Two OKF Bundles + Index of Indexes

`doc/` holds two independent **OKF (Open Knowledge Format v0.2) bundles**. Never mix their content:

- **`doc/bug/`** — incidents. [doc/bug/index.md](doc/bug/index.md) is the bundle index; each incident gets its own OKF concept file under `doc/bug/incidents/`.
- **`doc/feature/`** — architecture. [doc/feature/index.md](doc/feature/index.md) is the bundle index; each concept (module, service, script) gets its own small OKF file under `doc/feature/`.
- **[doc/index.md](doc/index.md)** — index of indexes. Points to both bundle indexes above and holds no content of its own. Read this first when you don't already know which bundle is relevant.

### OKF format (applies to both bundles)

- Every `.md` file (except reserved `index.md`/`log.md`) has YAML frontmatter with at minimum a `type` field (`Module`, `Bundle Index`, `Incident`, etc.); recommended fields: `title`, `description`, `resource` (path to the source file it documents/affects), `tags`, `status`.
- **One concept per file, kept small.** A module, script, or incident gets its own doc — never bundle multiple concepts into one large file. This keeps each doc independently fetchable: an agent pulls exactly the one file relevant to its question, not the whole bundle.
- Cross-link concepts with bundle-relative markdown links (`[Chunker](/doc/feature/chunker.md)`), not prose descriptions of "see the chunker file." Bug docs link to the feature docs they affect, and vice versa when relevant.
- Each bundle's `index.md` lists and links every concept doc in it — update it whenever a concept doc is added or removed.
- Reference: [Google Cloud OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

### Mandatory: read before you write

**Before suggesting or making any change to a module, check its `doc/feature/` concept doc (and `doc/bug/index.md` for prior incidents in that area) first.** This is not optional research — it's how you get context on what the current implementation is actually meant to do before touching it. If no concept doc exists yet for the module, that's a signal docs have drifted (flag it / delegate to `doc-sync`), not a reason to skip the check.

### Bug/Issue Handling (`doc/bug/`)

- **When a new problem is reported:**
  1. Check `doc/bug/index.md` first for a matching or related incident. If a resolution already exists, apply/reference it — do not re-derive from scratch.
  2. Also check the relevant `doc/feature/` concept doc for the affected module, per "Mandatory: read before you write" above.
  3. If nothing matches, only then investigate the codebase, fix it, and create a new incident file.
- **Each incident file** (`doc/bug/incidents/INC-XXX-short-slug.md`) must contain:
  - Root cause
  - Resolution method
  - Final status: resolved or not resolved
- **When a new bug/issue is introduced** (by us or discovered as a side effect), it also gets logged in the index, not just fixes.
- Keep `doc/bug/index.md` continuously up to date — it's the source of truth for "has this happened before."

## 3. Dedicated Agent for Bug Handling

- Rule #2's bug-handling flow (checking `doc/bug/index.md`, investigating, writing up root cause/resolution, updating the index) should be delegated to a dedicated subagent rather than done inline in the main thread. Reason: dedicated agent stays focused on just this task, won't drop steps over a long session.
- Main thread's job: receive the problem report, hand it to the `incident-handler` subagent (`.claude/agents/incident-handler.md`), relay the result.

## 4. Doc-Sync Agent for Architecture Documentation

- Keep [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [AGENTS.md](AGENTS.md), and the [doc/feature/](doc/feature/index.md) OKF bundle in sync with the actual codebase.
- When code changes introduce new modules, services, major decisions, or agents, delegate to the `doc-sync` subagent (`.claude/agents/doc-sync.md`) to scan diffs and update docs.
- Doc-sync ensures architecture docs never drift from reality — treat code as source of truth, docs as the reflection. This is the project's **self-healing documentation** mechanism: docs are expected to auto-correct after every significant change rather than decay silently.
- **Self-healing scope**: doc-sync updates `IMPLEMENTATION_PLAN.md` (narrative architecture + open decisions) AND `doc/feature/*.md` (OKF concept docs — add a new file per new module, update `resource`/content on changed modules, remove or mark `status: deprecated` on removed ones, keep `doc/feature/index.md` links current). It does not touch `doc/bug/` — that subtree is owned exclusively by `incident-handler` (rule #3).

## 5. Knowledge Graph Before Code

- This project uses `graphify` to build a persistent knowledge graph of the codebase.
- **Order of lookup for any "where is X" / "how does X work" / architecture question, or before editing a module you haven't touched yet this session:**
  1. `doc/index.md` → relevant bundle index (`doc/feature/index.md` or `doc/bug/index.md`) → the specific concept doc. Fastest, hand-curated, cheapest.
  2. `graphify` knowledge graph (`/graphify query "..."`) if the doc bundle doesn't have the answer or seems stale.
  3. Raw code grep/read only if neither of the above resolves it.
- This is enforced by instruction, not tooling — there is no hook that blocks edits pending a graphify check (a hard gate can't reliably tell whether a given edit needed one). Treat skipping steps 1–2 as a process violation to self-correct on, the same way skipping tests before claiming a fix works would be.
- If you skip straight to raw code because the task is trivial (a one-line typo fix, a rename with no behavior change), that's fine — use judgment. The requirement is for anything touching an module's actual logic or where "how does this currently work" matters.

## 6. Pydantic Models — Single Source of Truth

- **All data structures use Pydantic models.** No plain dicts, tuples, or ad-hoc classes.
- **Location:** `models/` directory at project root, organized by domain:
  - `models/documents.py` — Document, Chunk, Metadata
  - `models/vectors.py` — Vector, EmbeddingRequest, EmbeddingResult
  - `models/rag.py` — RAGQuery, RAGResponse, RetrievedContext
- **Naming:** PascalCase classes (e.g., `Document`), snake_case files.
- **Enforcement:** Every module imports from `models.*`. Never define data classes in feature modules.
- **Update contract:** When adding a new data type, add its Pydantic model to the appropriate file in `models/` and update [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) in the same commit. No data model should appear in code before it's in `models/`.

## 7. 500-Line File Limit — Hard Cap

- **No code file exceeds 500 lines.** Applies to every `.py` file, no exceptions.
- **A file crossing 500 lines is not a "trim it" problem — it's a "this module has too many responsibilities" problem.** Split by responsibility, not by cutting arbitrarily in half.
- **Before adding to a file that's already near 500 lines** (i.e. an addition would push it over, or it's already within ~50 lines of the cap): stop, look at the module's actual responsibilities, and split first. Don't write past the cap and clean up after.
- **How to split:**
  - Group by responsibility (e.g. one loader class per file, not all loaders in one `loaders.py`).
  - Use subpackages when a group of files shares a domain — e.g. `ingestion/loaders/` as a package (`__init__.py` re-exporting `LoaderFactory`, plus `pdf.py`, `json_loader.py`, `excel_csv.py`, `text.py`, `base.py` for shared `LoaderConfig`).
  - Keep the public interface stable: callers doing `from ingestion.loaders import LoaderFactory` shouldn't need to change when the file splits into a package — re-export from `__init__.py`.
  - Apply DRY: shared logic (e.g. `_clean_text`, repeated across loader classes today) moves to a shared base/util module during the split, not copy-pasted into each new file.
- **Example:** `ingestion/loaders.py` was split into `ingestion/loaders/` (`base.py`, `pdf.py`, `text.py`, `excel_csv.py`, `json_loader.py`, `factory.py`, `__init__.py` re-exporting `LoaderFactory` and all services) at 439 lines, before it crossed the cap — this is the reference pattern for future splits.
- **Check architecture before adding new code.** Before writing a new class/function, check the relevant `doc/feature/` concept doc (rule #2) and current file line count. If the natural home for new code is a file near/over the cap, split as part of that change — don't defer it.
- **Non-code files** (docs, config, data) are not subject to this cap — see rule #2 for `doc/` file-size philosophy (small OKF concept docs), which is a similar principle applied differently.

## 8. LangChain — Always Consult MCP Docs First

- Whenever you encounter or need to generate **any LangChain code**, query the `docs-langchain` MCP server first.
- **Why:** LangChain APIs evolve; MCP docs are authoritative and current. Prevents writing deprecated or incorrect patterns.
- **Scope:** All `langchain*` packages — imports, class usage, chains, retrievers, agents, memory, callbacks, loaders, embeddings, vector stores.
- **Execution:** Use the MCP server or WebFetch to read current docs before writing code. Cite the doc link in comments if the pattern is non-obvious.

## 9. Virtual Environment — Always Activate First

- **Before running any Python command, check for and activate the virtual environment.**
- Look for `.venv/` directory in project root.
- Activate with: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
- Verify activation: prompt shows `(.venv)` prefix or `which python` returns `.venv/...`
- This applies to: `python`, `pip`, `pytest`, `uv run`, or any Python-based CLI tools
- **Never run naked Python commands** — always activate first to ensure correct dependencies and isolation

## 10. Medical Data Sources — API Integration

**Primary free APIs for medical/clinical data:**

- **PubMed E-utilities** (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`): 35M+ papers; no key; 3 req/sec rate limit. Methods: `esearch` (search), `efetch` (metadata + abstract), `elink` (related). Returns XML/JSON.

- **PMC Open Access** (subset via PubMed): ~2M freely available full-text papers; use db=pmc in E-utilities; same rate limits as PubMed. Provides complete article body text.

- **ClinicalTrials.gov API v2** (`https://clinicaltrials.gov/api/v2/`): 500K+ trials; no auth; search by condition/drug/phase/status/sponsor/location; returns normalized JSON.

**Strategy for paper data:**

1. Use **PubMed esearch** to find papers, get metadata + abstract
2. Use **PMC Open Access** to fetch full text of freely available papers (cross-reference via title/authors or direct PMC ID lookup)
3. Combine results: metadata (PubMed) + body text (PMC) in single ingestion record
4. Fall back to abstract-only for non-open-access papers

**Implementation:** `ingestion/pmc_json_converter.py` implements this strategy — searches PMC via E-utilities, fetches full-text XML, and writes structured JSON (`dummy_docs/pmc_documents.json`) matching the schema `JSONLoaderService` (`ingestion/loaders.py`) expects.

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
