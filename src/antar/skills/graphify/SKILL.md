---
name: graphify
description: Query a target repo's knowledge graph for scoped code context. Use before editing to locate symbols and understand relationships without broad grep.
---

# graphify skill (Scanner + Coder)

When analyzing or editing a target repo, prefer its graphify knowledge graph over
grep-and-read exploration.

- If `graphify-out/graph.json` exists in the target repo, run:
  - `graphify query "<concept>"` — scoped subgraph for a concept
  - `graphify path "<A>" "<B>"` — relationship between two symbols
  - `graphify explain "<concept>"` — focused explanation
- To (re)build the graph for a target repo (AST-only, no API cost):
  - `graphify update <repo_path>`
- Fall back to stdlib `ast` scanning (tools/ast_scan.py) when no graph is present.

Rationale: a precomputed deterministic code map beats repeated grep/open cycles,
and gives the Coder precise file:line targets for minimal edits.
