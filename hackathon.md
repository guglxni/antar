# antar — hackathon build log

> Maintained per the official neatHack build-companion skill
> (https://neatlogs.com/hackathon/skill). Dated, evidence-linked, sanitized.
> No API keys, .env contents, PII, or private traces ever appear here.

## Project
**antar** (Sanskrit: *gap*) — an agent that finds the verified gap between an ML
codebase and the current literature, and reports it with evidence.

**Problem:** ML code drifts from SOTA; engineers debug bottlenecks papers already solved.

## Team
- Aaryan Guglani — @guglxni (solo)

## Stack
- **Agent runtime:** Python 3.11, stdlib `ast` scanning, custom plan→act→verify→recover loop
- **LLM:** BYOK — OpenAI / Groq / Anthropic / hackathon LiteLLM (`claude-haiku` default)
- **Tracing:** neatlogs (`init` + `wrap` + `span`) — every run traced
- **Repo context/history:** Entire CLI (git hooks → per-commit checkpoints) + `entire graph`
- **Business plan:** cfo.ai via MCP (`https://api.cfo.ai/mcp`)
- **Data:** arXiv public API (no key)

## Requirements (confirmed from https://neatlogs.com/hackathon)
- Must use neatlogs + Entire + cfo.ai, with a clear role for each.
- All code written Oct 10–12; public repo; commits dated in window.
- Submit = quote-post of official neatlogs X post, 19:00–23:55 IST Oct 12.
- Demo video ≤3 min covering all three tools.

## Build log
### 2026-10-12 (setup)
- Created fresh repo `antar`; `git init` on branch `main`.
- Installed Entire CLI v0.11.4 (darwin/arm64) → `~/.local/bin/entire`; ran
  `entire enable --yes --agent claude-code` (5 git hooks installed, git-refs backend).
- Created `.venv`; installed `neatlogs 1.4.26`, `openai 2.54`, `litellm`, `python-dotenv`.
- Authored doc suite: PRD, ARCHITECTURE, DESIGN, REQUIREMENTS, PLAN, PROPOSAL, MATH,
  REFERENCES, SKILL, docs/setup.md.
- PENDING: fill `.env` (NEATLOGS_API_KEY, LITELLM_API_KEY); cfo.ai account + MCP auth.

## Demo
- URL/instructions: TBD. Offline fallback = pre-cached golden run in `examples/`.

## Known limitations / next steps
- Abstracts only (no full-PDF parsing). Python targets only. Advisory (no code edits).
- Next: walking skeleton → core value → rubric differentiators → package (see PLAN.md).

## Submission
- [ ] public repo, commits in window
- [ ] demo video ≤3 min (covers neatlogs/Entire/cfo.ai)
- [ ] evidence: traces (EV-1,2,5), Entire checkpoints+graph (EV-3), cfo.ai plan (EV-4), #neatHack posts (EV-6)
- [ ] quote-post submission before cutoff
