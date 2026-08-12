---
type: Bundle Index
title: medical-ingestion incident index
description: OKF bundle indexing every bug/incident found in this repo, whether fixed by us or introduced by us.
status: stable
---

# Incident Index

Check this file FIRST when a new problem is reported — before touching the codebase — to see if it's a known/resolved issue.

| ID | Summary | Status | Doc |
|----|---------|--------|-----|
| _none yet_ | | | |

## Conventions

- ID format: `INC-001`, `INC-002`, ... sequential, never reused.
- Status: `open`, `resolved`, `wontfix`.
- Each incident gets its own OKF concept file: `doc/bug/incidents/INC-XXX-short-slug.md`, with frontmatter `type: Incident`, `title`, `description`, `status` (mirrors the table's Status column), `resource` (path to the affected file, if applicable), `tags`.
- Incident file body must contain: **Root cause**, **Resolution method**, **Final status** (resolved or not).
- Link related concept docs from [doc/feature/](/doc/feature/index.md) in the incident body when the bug lives in a documented module — e.g. `Affects: [Chunker](/doc/feature/chunker.md)`.

## Related

- [doc/index.md](/doc/index.md) — top-level index of both `doc/` subtrees
- [doc/feature/index.md](/doc/feature/index.md) — architecture bundle (check before fixing, to understand the module's documented design first)
