"""antar webapp — FastAPI backend + minimal UI to run and inspect the agent.

Serves the pipeline over HTTP for the demo and for remote use. Security:
- SecurityHeadersMiddleware, tight CORS (no wildcard in prod).
- Optional bearer auth on mutating endpoints (ANTAR_WEB_TOKEN).
- Read-only /health and /api/scan are safe; /api/run mutates (owner-scoped downstream).
"""
from __future__ import annotations

import os

import neatlogs
from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .orchestrator import run
from .tools import ast_scan, repo_intake, rag, arxiv_search

app = FastAPI(title="antar", version="0.2.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

# CORS — tighten via ANTAR_CORS_ORIGINS (comma-separated); never "*" with credentials.
_origins = [o.strip() for o in os.environ.get("ANTAR_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins or ["http://localhost:8501"],
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

_bearer = HTTPBearer(auto_error=False)


def _auth(creds: HTTPAuthorizationCredentials | None = Security(_bearer)) -> None:
    token = os.environ.get("ANTAR_WEB_TOKEN")
    if token and (creds is None or creds.credentials != token):
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Content-Security-Policy", "default-src 'self'")
    return resp


class RunRequest(BaseModel):
    repo: str
    mode: str = "report"           # report | issues | pr
    allow_pr: bool = False
    max_prs: int = 1


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "antar", "version": "0.2.0"}


@app.get("/api/scan")
def api_scan(repo: str) -> dict:
    local = repo_intake.resolve(repo)
    techs = ast_scan.scan_repo(str(local.path))
    return {"repo": local.full, "techniques": [t.__dict__ for t in techs]}


@app.get("/api/papers")
def api_papers(q: str, max_results: int = 8) -> dict:
    raw = arxiv_search.search(q, max_results=max_results * 2)
    return {"query": q, "papers": [p.__dict__ for p in rag.rerank(q, raw, top_k=max_results)]}


@app.post("/api/run", dependencies=[Security(_auth)])
def api_run(req: RunRequest) -> dict:
    if req.mode == "pr" and not req.allow_pr:
        raise HTTPException(400, "mode=pr requires allow_pr=true")
    rep = run(req.repo, mode=req.mode, allow_pr=req.allow_pr, max_prs=req.max_prs)
    return {"techniques": rep.techniques, "papers": rep.papers,
            "verified_gaps": rep.verified_gaps, "issues": rep.issues, "prs": rep.prs}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


_INDEX_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>antar</title>
<style>body{font-family:system-ui;margin:2rem;max-width:720px}input,select,button{padding:.5rem;margin:.25rem 0;width:100%}button{background:#1a73e8;color:#fff;border:0;border-radius:6px;cursor:pointer}#out{white-space:pre-wrap;background:#f6f8fa;padding:1rem;border-radius:6px;margin-top:1rem}</style></head>
<body><h1>antar <small>— the gap between your code and the literature</small></h1>
<input id="repo" placeholder="owner/repo or local path (you must own it for issues/PRs)">
<select id="mode"><option>report</option><option>issues</option><option>pr</option></select>
<label><input type="checkbox" id="allow_pr" style="width:auto"> allow PR (owner-scoped)</label>
<button onclick="run()">Run antar</button>
<div id="out"></div>
<script>
async function run(){
  const body={repo:repo.value,mode:mode.value,allow_pr:allow_pr.checked,max_prs:1};
  out.textContent="running…";
  const r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  out.textContent=JSON.stringify(await r.json(),null,2);
}
</script></body></html>"""
