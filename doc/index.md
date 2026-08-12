---
type: Bundle Index
title: medical-ingestion doc/ index of indexes
description: Top-level pointer into the two independent OKF bundles under doc/ — feature (architecture) and bug (incidents).
status: stable
---

# doc/ — Index of Indexes

`doc/` has two independent OKF (Open Knowledge Format v0.2) bundles. Each has its own `index.md`; this file only points to them — it holds no content of its own.

| Subtree | Index | Covers |
|---|---|---|
| `doc/feature/` | [doc/feature/index.md](/doc/feature/index.md) | Architecture — one concept doc per module/service/script |
| `doc/bug/` | [doc/bug/index.md](/doc/bug/index.md) | Incidents — one concept doc per bug, whether fixed or introduced |

## Before changing code

Read the relevant concept doc(s) in `doc/feature/` for the module you're about to touch, and check `doc/bug/index.md` for prior incidents in that area, before making changes. See [AGENTS.md](/AGENTS.md) rule #2.
