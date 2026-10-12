# CLAUDE.md — Claude Code session guide (antar)
# (STAGED — rename to CLAUDE.md to activate; that file is approval-gated)

Mirror of AGENTS.md. If they ever disagree, AGENTS.md wins.

## TL;DR for this session
- Repo: `antar`, neatHack submission. Python 3.11 + uv. Branch `main`.
- **Trace everything** via `llm.get_client()` (neatlogs-wrapped). No raw OpenAI clients.
- **Span every stage** with `@neatlogs.span(kind=...)`.
- **Entire hooks are on** — each commit auto-checkpoints. Never `--no-verify`.
- **Verifier gate:** only `verdict == "APPROVED"` gaps reach the report.
- **Advisory:** never edit the target repo being analyzed.
- **Recover, don't abort** (DESIGN.md §6).
- Secrets only in `.env` (gitignored). Refuse to commit any key you see.

## Where things live
- `src/antar/llm.py` — BYOK client factory
- `src/antar/orchestrator.py` — the plan→act→verify→recover loop (root WORKFLOW)
- `src/antar/tools/` — ast_scan, arxiv_search, fetch_abstract
- `src/antar/agents/verifier.py` — SOD gate
- `src/antar/report.py` — GAPS.md / RELATED_WORK.md writer
- `hackathon.md` — build log (append dated, sanitized entries)

## Useful commands
```bash
entire graph search "<concept>"
entire graph impact --symbol <name>
entire checkpoint list
uv pip install <pkg>
pytest -q
python -m antar run <repo>
```
