---
name: antar
description: Find the gap between an ML codebase and the current literature, with verified, evidence-backed findings. Use when pointing the agent at an ML repo to produce TECHNIQUES/PAPERS/GAPS/RELATED_WORK.
---

# antar skill

`antar` (Sanskrit: *gap*) closes the code↔literature gap for an ML repository.

## When to use
- Before a training run: "am I missing a standard technique?"
- Bootstrapping a Related Work section with verified citations.
- Drift-checking a legacy model repo.

## Inputs
- `repo`: local path or public git URL.
- LLM key (any of `OPENAI_API_KEY`/`GROQ_API_KEY`/`ANTHROPIC_API_KEY`/`LITELLM_API_KEY`).
- `NEATLOGS_API_KEY` for tracing (required).

## Pipeline
1. `scan` — AST-extract techniques w/ file:line evidence → TECHNIQUES.md
2. `hunt` — arXiv per technique, ranked by relevance+recency → PAPERS.md
3. `verify` — SOD sub-agent approves/rejects each gap (hallucination gate)
4. `report` — GAPS.md (ranked, evidence) + RELATED_WORK.md (LaTeX-ready)

## Guarantees
- Advisory only; never modifies the target repo.
- Every gap verified; unverifiable ⇒ marked UNCERTAIN, not hidden.
- Recovers from tool failure (retry/fallback/degrade); recovery is traced.
- Every step traced (neatlogs); every commit checkpointed (Entire).

## Run
```bash
python -m antar run <repo>          # full traced pipeline
python -m antar run <repo> --offline # replay cached demo (no API)
```

## Evidence & business
- neatlogs traces → before/after improvement + recovery evidence.
- Entire `checkpoint list` + `entire graph` → development + repo-context evidence.
- cfo.ai → pricing/cost/revenue/runway from traced unit costs.
