# CLAUDE.md — Claude Code session guide (antar)

Mirror of AGENTS.md. If they ever disagree, AGENTS.md wins.

## TL;DR for this session
- Repo: `antar` (neatHack). Python 3.11 + uv. Branch `main`.
- **Trace everything** via `llm.get_client()` (neatlogs-wrapped). No raw OpenAI clients.
- **Span every stage** with `@neatlogs.span(kind=...)`.
- **Entire hooks are on** — each commit auto-checkpoints. Never `--no-verify`.
- **Verifier gate:** only `verdict == "APPROVED"` gaps ship.
- **Owner-scoped writes only** (GitHub/GitLab) — `repo_access.assert_can_write()`.
- **Recover, don't abort** (DESIGN.md §6).
- Secrets only in `.env` (gitignored). Refuse to commit any key you see.

## Where things live
- `src/antar/llm.py` — BYOK client factory
- `src/antar/orchestrator.py` — the plan→act→verify→recover loop (root WORKFLOW)
- `src/antar/tools/` — ast_scan, arxiv_search, rag, graphify_integration, repo_intake
- `src/antar/agents/` — verifier, planner, harness (coder loop), tester, github_ops, repo_access
- `src/antar/mcp_server.py` — fastmcp server (auth + RBAC)
- `src/antar/webapp.py` — FastAPI webapp
- `hackathon.md` — build log (append dated, sanitized entries)

## Useful commands
```bash
entire graph search "<concept>"
entire graph impact --symbol <name>
entire checkpoint list
uv pip install <pkg>
pytest -q
python -m antar run <repo> --mode report|issues|pr
python -m antar mcp
uvicorn antar.webapp:app --port 8000
```
