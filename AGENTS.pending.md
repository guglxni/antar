# AGENTS.md — operating guide for AI coding agents in this repo
# (STAGED — rename to AGENTS.md to activate; that file is approval-gated)

You are helping build **antar** under a hackathon deadline. Read `PRD.md`,
`ARCHITECTURE.md`, and `DESIGN.md` first. This file is the source of truth for *how* to work here.

## Hard rules (never violate)

1. **Every run is traced.** All LLM calls go through `llm.get_client()`, which returns a
   `neatlogs.wrap()`-ed client. Never instantiate a raw `OpenAI()` for model calls.
2. **Every stage is a span.** New pipeline stage ⇒ decorate with `@neatlogs.span(kind=...)`.
3. **Commit early, commit often.** Entire hooks capture each commit as a checkpoint.
   Do not disable the hooks. Do not `git commit --no-verify`.
4. **Never commit secrets.** `.env` is gitignored. Keys live only in env vars / `.env`.
   If you see a key in a diff, stop and refuse to commit it.
5. **Verifier is mandatory.** No gap reaches `report.py` without `verdict == "APPROVED"`.
6. **Advisory only.** antar never writes to the *target* repository it analyzes.
7. **Recover, don't abort.** Tool failures route through the recovery policy
   (DESIGN.md §6). A stage must degrade, not silently kill the run.

## Repo context tools (use them)

```bash
entire graph search "arxiv query construction"     # find code by meaning
entire graph impact --symbol arxiv_search          # what breaks if I change this
entire checkpoint list                             # history of changes
git log --oneline                                  # Entire-Checkpoint trailers attached
```

## Coding conventions

- Python 3.11, `uv` for deps. Type hints + `dataclasses`.
- Stdlib `ast` only for scanning — **no heavy tree-sitter dep** in the shipped tool.
- `rich` for console. Small functions; one responsibility per module.
- Tests: `pytest`. Every FR in REQUIREMENTS.md has a test. Recovery paths need an
  *injected-failure* test (mock a 500 / timeout and assert the run still completes).

## Definition of done (per feature)

- [ ] Code + type hints
- [ ] Test passes (incl. failure-injection for tools)
- [ ] A traced run shows the new span with tokens/cost
- [ ] Committed (Entire checkpoint created)
- [ ] `hackathon.md` entry appended (dated, evidence linked)
