# Graph Report - .  (2026-08-09)

## Corpus Check
- Corpus is ~1,126 words - fits in a single context window. You may not need a graph.

## Summary
- 31 nodes · 46 edges · 5 communities
- Extraction: 72% EXTRACTED · 26% INFERRED · 2% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.91)
- Token cost: 900 input · 1,200 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Incident Index Format|Incident Index Format]]
- [[_COMMUNITY_Incident Handler Workflow|Incident Handler Workflow]]
- [[_COMMUNITY_Implementation Plan Maintenance|Implementation Plan Maintenance]]
- [[_COMMUNITY_Dedicated Incident Agent Rule|Dedicated Incident Agent Rule]]
- [[_COMMUNITY_Knowledge Graph Rule|Knowledge Graph Rule]]

## God Nodes (most connected - your core abstractions)
1. `doc/INDEX.md — Incident Index` - 9 edges
2. `AGENTS.md — Agent Instructions` - 7 edges
3. `CLAUDE.md — Project Instructions` - 7 edges
4. `incident-handler Agent` - 6 edges
5. `Bug/Issue Handling via doc/ Rule (AGENTS.md)` - 5 edges
6. `Bug/Issue Handling via doc/ Rule (CLAUDE.md)` - 5 edges
7. `Dedicated Agent for Bug Handling Rule (AGENTS.md)` - 3 edges
8. `Knowledge Graph Before Code Rule (AGENTS.md)` - 3 edges
9. `doc/incidents/INC-XXX File Pattern (AGENTS.md)` - 3 edges
10. `Dedicated Agent for Incident Handling Rule (CLAUDE.md)` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Allow Bash(python3 *) Permission` --conceptually_related_to--> `incident-handler Agent`  [AMBIGUOUS]
  .claude/settings.local.json → .claude/agents/incident-handler.md
- `Implementation Plan Maintenance Rule (AGENTS.md)` --semantically_similar_to--> `Implementation Plan Maintenance Rule (CLAUDE.md)`  [INFERRED] [semantically similar]
  /home/rounak/Desktop/Projects/medical-ingestion/AGENTS.md → /home/rounak/Desktop/Projects/medical-ingestion/CLAUDE.md
- `Bug/Issue Handling via doc/ Rule (AGENTS.md)` --semantically_similar_to--> `Bug/Issue Handling via doc/ Rule (CLAUDE.md)`  [INFERRED] [semantically similar]
  /home/rounak/Desktop/Projects/medical-ingestion/AGENTS.md → /home/rounak/Desktop/Projects/medical-ingestion/CLAUDE.md
- `Dedicated Agent for Bug Handling Rule (AGENTS.md)` --semantically_similar_to--> `Dedicated Agent for Incident Handling Rule (CLAUDE.md)`  [INFERRED] [semantically similar]
  /home/rounak/Desktop/Projects/medical-ingestion/AGENTS.md → /home/rounak/Desktop/Projects/medical-ingestion/CLAUDE.md
- `Knowledge Graph Before Code Rule (AGENTS.md)` --semantically_similar_to--> `Knowledge Graph Before Code Rule (CLAUDE.md)`  [INFERRED] [semantically similar]
  /home/rounak/Desktop/Projects/medical-ingestion/AGENTS.md → /home/rounak/Desktop/Projects/medical-ingestion/CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Incident Handling Workflow: check index -> investigate -> fix -> document -> update index** — claude_bug_issue_handling_rule, claude_dedicated_agent_rule, doc_index_md, claude_incident_handler_subagent [INFERRED 0.85]
- **Living Documentation Governance Pattern: plan and incident index kept in sync with code** — implementation_plan_md, doc_index_md, claude_implementation_plan_rule, claude_bug_issue_handling_rule [INFERRED 0.75]
- **Incident Handling Workflow (CLAUDE.md rules #2/#4 + incident-handler agent)** — agents_incident_handler_incident_handler, doc_index_incident_index, incidents_inc_xxx_short_slug_incident_writeup, claude_rule_2, claude_rule_4, agents_incident_handler_graphify_knowledge_graph [INFERRED 0.85]

## Communities (5 total, 0 thin omitted)

### Community 0 - "Incident Index Format"
Cohesion: 0.39
Nodes (9): Bug/Issue Handling via doc/ Rule (AGENTS.md), doc/incidents/INC-XXX File Pattern (AGENTS.md), Bug/Issue Handling via doc/ Rule (CLAUDE.md), doc/incidents/INC-XXX-short-slug.md Pattern (CLAUDE.md), INC-XXX Sequential ID Format Convention, doc/incidents/INC-XXX-short-slug.md File Convention (doc/INDEX.md), Incident File Content Requirement (root cause, resolution, status), doc/INDEX.md — Incident Index (+1 more)

### Community 1 - "Incident Handler Workflow"
Cohesion: 0.29
Nodes (8): Graphify Knowledge Graph (investigation aid), incident-handler Agent, CLAUDE.md Rule #2 (Bug/Issue Handling via doc/), CLAUDE.md Rule #4 (Knowledge Graph Before Code), Allow Bash(python3 *) Permission, Local Claude Settings Permissions, doc/INDEX.md Incident Index, doc/incidents/INC-XXX-short-slug.md Write-up Template

### Community 2 - "Implementation Plan Maintenance"
Cohesion: 0.47
Nodes (5): Implementation Plan Maintenance Rule (AGENTS.md), AGENTS.md — Agent Instructions, Implementation Plan Maintenance Rule (CLAUDE.md), CLAUDE.md — Project Instructions, Implementation Plan Changelog Convention

### Community 3 - "Dedicated Incident Agent Rule"
Cohesion: 0.67
Nodes (4): Dedicated Agent for Bug Handling Rule (AGENTS.md), incident-handler Subagent (.claude/agents/incident-handler.md), Dedicated Agent for Incident Handling Rule (CLAUDE.md), incident-handler Subagent (CLAUDE.md reference)

### Community 4 - "Knowledge Graph Rule"
Cohesion: 0.67
Nodes (4): graphify Knowledge Graph, Knowledge Graph Before Code Rule (AGENTS.md), graphify Skill/Knowledge Graph (CLAUDE.md reference), Knowledge Graph Before Code Rule (CLAUDE.md)

## Ambiguous Edges - Review These
- `Allow Bash(python3 *) Permission` → `incident-handler Agent`  [AMBIGUOUS]
  .claude/settings.local.json · relation: conceptually_related_to

## Knowledge Gaps
- **7 isolated node(s):** `Implementation Plan Changelog Convention`, `INC-XXX Sequential ID Format Convention`, `Incident Status Values (open/resolved/wontfix)`, `Local Claude Settings Permissions`, `Graphify Knowledge Graph (investigation aid)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Allow Bash(python3 *) Permission` and `incident-handler Agent`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `AGENTS.md — Agent Instructions` connect `Implementation Plan Maintenance` to `Incident Index Format`, `Dedicated Incident Agent Rule`, `Knowledge Graph Rule`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `CLAUDE.md — Project Instructions` connect `Implementation Plan Maintenance` to `Incident Index Format`, `Dedicated Incident Agent Rule`, `Knowledge Graph Rule`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `doc/INDEX.md — Incident Index` connect `Incident Index Format` to `Implementation Plan Maintenance`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Bug/Issue Handling via doc/ Rule (AGENTS.md)` (e.g. with `Bug/Issue Handling via doc/ Rule (CLAUDE.md)` and `Incident File Content Requirement (root cause, resolution, status)`) actually correct?**
  _`Bug/Issue Handling via doc/ Rule (AGENTS.md)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Implementation Plan Changelog Convention`, `INC-XXX Sequential ID Format Convention`, `Incident Status Values (open/resolved/wontfix)` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._