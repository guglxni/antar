# antar — Operations (DevOps / DevSecOps)

## Secrets (never in chat, never in git)

Use the terminal loader — reads with hidden input, writes `.env` as `0600`, gitignored:
```bash
./scripts/load-env.sh          # prompts for keys (NEATLOGS / LITELLM / BYOK)
set -a; . ./.env; set +a       # load into the current shell to run the app
```
GitHub needs **no paste**: the code reuses your `gh` keyring session (`gh auth token`).

For the deployed service, secrets live in **AWS Secrets Manager**, referenced by App Runner —
never baked into the image or passed as CLI args.

## RAG discovery engine (FOSS, keyless)

The Researcher uses a **hybrid retrieval** pipeline over arXiv
(`src/antar/tools/rag.py`), following the pattern shared by rag-lens / vstash /
local-semantic-search:

```
arXiv candidates ─▶ BM25 (rank_bm25) ───┐
                  └▶ dense embeddings ──┴─▶ RRF fuse ─▶ recency prior ─▶ ranked
                    (sentence-transformers, bge-small 384-d, LOCAL — no API key)
```

- **RRF** (Cormack et al. 2009): `Σ 1/(k + rank)`, k=60 — no score calibration needed.
- **Recency prior** `e^{-λΔdays}`, half-life 1 yr — favours state of the art.
- **Degrades gracefully**: if the embedding model is unavailable (offline), falls back to
  BM25-only and logs it. Retrieval never aborts the pipeline.

## Webapp (FastAPI)

`src/antar/webapp.py` — `uvicorn antar.webapp:app`.
- Security headers middleware (nosniff, DENY frame, CSP `default-src 'self'`).
- Tight CORS (no wildcard with credentials); mutating `/api/run` behind optional bearer auth.
- Read-only `/health`, `/api/scan`, `/api/papers`; `/api/run` runs the pipeline (owner-scoped downstream).

## MCP server (hardened)

`src/antar/mcp_server.py` — `python -m antar.mcp_server` (stdio) or `ANTAR_MCP_HTTP=1` (http).
- **Auth:** static bearer-token `TokenVerifier` (constant-time compare) when `ANTAR_MCP_TOKEN` is set.
- **RBAC:** `WriteGate` middleware — write tools (`open_issues`, `fix_gap`) require `ANTAR_ALLOW_WRITES=1`.
- stdio transport inherits local security (no auth); http transport is authenticated.

## Container

`Dockerfile` — multi-stage, non-root (`uid 10001`), healthcheck, minimal surface.
```bash
docker build -t antar . && docker run -p 8000:8000 --env-file .env antar
```

## CI (GitHub Actions) — `.github/workflows/ci.yml`

ruff lint → mypy (advisory) → pytest → **gitleaks** secret scan → docker build + hadolint.

## Pre-commit — `.pre-commit-config.yaml`

```bash
pre-commit install   # ruff + ruff-format + gitleaks + detect-private-key + hygiene
```

## AWS deploy — `scripts/deploy-aws.sh`

App Runner (simplest container service). The script: verifies `aws sts get-caller-identity`,
creates an ECR repo (scan-on-push), builds + pushes the image, and prints the App Runner step.
Secrets wired from Secrets Manager. **Requires an authenticated AWS CLI** (see below).
