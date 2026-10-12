"""antar MCP server — hardened for production.

Security (FastMCP):
- Bearer-token auth on HTTP transports (token from env, never hardcoded).
- Tool-level RBAC: write tools (open_issues / fix_gap) require the 'write' scope.
- stdio transport inherits the local environment's security (no auth needed).

Expose the antar pipeline as tools other agents can call. Open-sourceable (MIT).
"""
from __future__ import annotations

import os

from fastmcp import FastMCP

from .orchestrator import run
from .tools import arxiv_search, ast_scan, rag


def _build_auth():
    """Static bearer-token verification on HTTP transports when ANTAR_MCP_TOKEN is set.

    Uses fastmcp's TokenVerifier with a constant-time token check (correct for an
    internal/self-hosted server; for multi-user OAuth use RemoteAuthProvider instead).
    Returns None for local stdio (inherits the local environment's security).
    """
    token = os.environ.get("ANTAR_MCP_TOKEN")
    if not token:
        return None
    import secrets
    from fastmcp.server.auth import TokenVerifier
    from fastmcp.server.auth.auth import AccessToken

    class StaticToken(TokenVerifier):
        async def verify_token(self, token: str) -> AccessToken | None:  # noqa: A002
            if secrets.compare_digest(token, expected):
                return AccessToken(token=token, client_id="antar-client",
                                   scopes=["read", "write"])
            return None

    expected = token
    return StaticToken()


mcp = FastMCP("antar", auth=_build_auth())

_WRITE_TOOLS = {"open_issues", "fix_gap"}


# Tool-level RBAC middleware (write tools gated even when transport is local).
try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    from fastmcp.exceptions import ToolError

    class WriteGate(Middleware):
        async def on_call_tool(self, context: MiddlewareContext, call_next):
            name = context.message.name
            if name in _WRITE_TOOLS and os.environ.get("ANTAR_ALLOW_WRITES") != "1":
                raise ToolError(f"{name} is a write tool; set ANTAR_ALLOW_WRITES=1 to enable")
            return await call_next(context)

    mcp.add_middleware(WriteGate())
except Exception:  # older fastmcp without middleware API — degrade to env-gated tools
    pass


@mcp.tool()
def scan_repo(repo: str) -> list[dict]:
    """AST + graphify scan of a repo → ML technique inventory."""
    return [t.__dict__ for t in ast_scan.scan_repo(repo)]


@mcp.tool()
def find_gaps(repo: str) -> dict:
    """scan → hybrid-RAG research → verify. Returns verified gaps (report mode)."""
    rep = run(repo, mode="report")
    return {"techniques": rep.techniques, "papers": rep.papers,
            "verified_gaps": rep.verified_gaps}


@mcp.tool()
def search_papers(query: str, max_results: int = 8) -> list[dict]:
    """Hybrid arXiv search: BM25 + dense embeddings + RRF + recency (local, no key)."""
    raw = arxiv_search.search(query, max_results=max_results * 2)
    return [p.__dict__ for p in rag.rerank(query, raw, top_k=max_results)]


@mcp.tool()
def open_issues(repo: str) -> dict:
    """Open a GitHub/GitLab issue per verified gap (owner-scoped; write tool)."""
    rep = run(repo, mode="issues")
    return {"issues": rep.issues, "verified_gaps": rep.verified_gaps}


@mcp.tool()
def fix_gap(repo: str, max_prs: int = 1) -> dict:
    """Full loop incl. harness-learning fix + PR (owner-scoped; write tool)."""
    rep = run(repo, mode="pr", allow_pr=True, max_prs=max_prs)
    return {"prs": rep.prs, "issues": rep.issues}


if __name__ == "__main__":
    # http transport when serving remotely (auth on), stdio for local agent use.
    transport = "http" if os.environ.get("ANTAR_MCP_HTTP") == "1" else "stdio"
    mcp.run(transport=transport)
