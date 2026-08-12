# CLAUDE.md — medical-ingestion

Project-specific instructions for Claude Code. Extends [AGENTS.md](AGENTS.md) with Claude Code-specific tool bindings and overrides.

## Core Rules

Follow **all 9 rules + Behavioral Guidelines** in [AGENTS.md](AGENTS.md). This file documents Claude Code-specific implementations only.

## Claude Code-Specific Overrides

### Rule #3 - Dedicated Agent for Incident Handling

When the user reports a bug/issue, use the `Agent` tool with:

```python
subagent_type: "incident-handler"
```

Agent specification: `.claude/agents/incident-handler.md`

Full cycle: check `doc/bug/INDEX.md` → investigate if needed → fix → write incident doc → update index → relay summary back.

### Rule #4 - Doc-Sync Agent for Self-Healing Documentation

After significant code changes, use the `Agent` tool with:

```python
subagent_type: "doc-sync"
```

Agent specification: `.claude/agents/doc-sync.md`

Scans git diff for new modules/services/agents/decisions and updates `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, and the `doc/feature/` OKF bundle to match code.

**Self-healing doc structure:** `doc/` has two independent subtrees — `doc/bug/` (incident index + incident files, owned by `incident-handler`) and `doc/feature/` (OKF v0.2 architecture bundle, one small concept file per module, owned by `doc-sync`). Each concept doc under `doc/feature/` has YAML frontmatter (`type`, `title`, `description`, `resource`, `tags`, `status`) and cross-links to related concepts via bundle-relative markdown links. `doc/feature/index.md` is the bundle index — always kept current with every concept doc it links to. See AGENTS.md rule #2 for the full spec and rule #4 for the update contract.

### Rule #5 - Knowledge Graph Before Code

Query the knowledge graph using the `graphify` **Skill** (not just the knowledge graph concept):

```bash
/graphify                          # build or refresh graph
/graphify query "<question>"       # ask the existing graph
/graphify path "Node1" "Node2"     # shortest path between concepts
/graphify explain "Node"           # plain-language node explanation
```

**Why Skill instead of raw graphify:** Skill bundles the full pipeline (detect → extract → cluster → export) in one place. Raw graphify CLI needs manual step-by-step orchestration.

Invoke via `Skill` tool: `skill: "graphify"` with optional `args: "<command>"` (e.g., `args: "query \"how does ingestion work\""`)

Only fall back to raw code reading when the graph doesn't have the answer.

### Rule #6 - Pydantic Models

One additional requirement: When adding a new data type, also update [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) in the same commit. No data model should appear in code before it's in `models/` and the plan is updated.

### Rule #8 - Virtual Environment

Always activate `.venv/` before running Python commands:

```bash
source .venv/bin/activate
```

Verify: prompt shows `(.venv)` prefix or `which python` returns `.venv/...`

---

## Memory System

This project has a persistent memory system at `.claude/projects/-home-rounak-Desktop-Projects-medical-ingestion/memory/`. Use `MEMORY.md` as the index, and write discrete memories to separate files when the user explicitly asks to remember something or when patterns emerge that future conversations should know about. Do not save:

- Code patterns, conventions, architecture (queryable via graphify or codebase)
- Git history (use git log / git blame)
- Debugging solutions (in the code/commit message)
- Ephemeral task state (current conversation)
