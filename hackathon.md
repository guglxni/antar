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

### 2026-10-12 (multi-agent + harness-learning build)
- Built the 8-agent system: Orchestrator, Scanner (AST+graphify), Researcher, Verifier (SOD),
  Planner, Coder (aider), Tester, GitHub/GitLab ops. Owner-scoped write guard (verified live).
- Integrated **harness learning** (arXiv:2609.35738): test-time revision loop with an
  ExecutionReport feedback signal (propose → test → revise ≤3 rounds). MATH.md §8.
- Hybrid RAG discovery (BM25 + local bge-small embeddings + RRF + recency), keyless.
- FastAPI webapp (security headers, CORS, bearer auth) + hardened MCP (TokenVerifier + RBAC).
- DevOps: non-root Dockerfile, CI (ruff/mypy/pytest/gitleaks/hadolint), pre-commit,
  AWS App Runner deploy script. neatlogs doctor --local + --probe PASS.

### 2026-10-12 (live end-to-end run — EVIDENCE)
- Target: `guglxni/antar-demo-target` (trainer missing gradient clipping).
- Scan: AdamW/cosine/AMP detected; gradient_clipping correctly flagged MISSING.
- Research: 70 arXiv candidates (hybrid RAG). Verifier approved **14 verified gaps**.
- **Issues mode: 11 real issues opened** (owner-scoped, label `antar, ml-gap`).
- **Failure→fix captured in traces:** verifier JSON-fence parse bug + missing-vs-present
  gap logic flaw → fixed → verified_gaps went 0 → 14. (EV-1 improvement evidence.)
- PR mode (harness-learning fix + PR) running.

### 2026-10-12 (PR loop proven + aider routing fixed)
- PR mode ran the full loop; opened 25 issues total across runs.
- Found + fixed an aider routing bug: bare `claude-haiku` model string → litellm
  "LLM Provider NOT provided". Fix: prefix with provider (`openai/claude-haiku`) and force
  `OPENAI_API_BASE`/`OPENAI_API_KEY` so a stray global `~/.aider.conf.yml` can't hijack routing.
- Verified the programmatic aider `Coder` path applies a real edit via the LiteLLM gateway
  (clip 1.0→0.9, 951/215 tokens traced).
- **PR #26 OPEN** on antar-demo-target: "Add gradient clipping to trainer" — the
  harness-learning fix (clip_grad_norm_ added, compiles), owner-scoped, traced.

### 2026-10-12 (cfo.ai business plan via MCP — EV-4)
- Registered cfo.ai as a Hermes MCP server (`https://api.cfo.ai/mcp`, OAuth) → 34 tools.
- Built the business plan programmatically: `antar unit economics` (Free/Pro/Team × price,
  COGS/run, gross-margin formula) + `antar operating model` (monthly: customers→MRR→cost→
  profit→margin→cash/runway) + a narrative page. Live links in docs/BUSINESS-PLAN.md.
- Unit economics anchored to measured neatlogs trace cost/run.

## Demo
- URL/instructions: TBD. Offline fallback = pre-cached golden run in `examples/`.
- Live demo repo: https://github.com/guglxni/antar-demo-target (11 agent-opened issues).

## Known limitations / next steps
- Abstracts only (no full-PDF parsing). Python targets only. Advisory (no code edits).
- Next: walking skeleton → core value → rubric differentiators → package (see PLAN.md).

## Submission
- [ ] public repo, commits in window
- [ ] demo video ≤3 min (covers neatlogs/Entire/cfo.ai)
- [ ] evidence: traces (EV-1,2,5), Entire checkpoints+graph (EV-3), cfo.ai plan (EV-4), #neatHack posts (EV-6)
- [ ] quote-post submission before cutoff
