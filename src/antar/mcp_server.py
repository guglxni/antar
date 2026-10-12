"""Expose the antar pipeline as MCP tools so other agents can call it.

Run:  python -m antar.mcp_server        (stdio)
Open-sourceable (MIT). Built with fastmcp.
"""
from __future__ import annotations

from fastmcp import FastMCP

from .orchestrator import run
from .tools import arxiv_search, ast_scan

mcp = FastMCP("antar")


@mcp.tool()
def scan_repo(repo: str) -> list[dict]:
    """AST-scan a repo and return its ML technique inventory."""
    return [t.__dict__ for t in ast_scan.scan_repo(repo)]


@mcp.tool()
def find_gaps(repo: str) -> dict:
    """Run scan→research→verify and return verified gaps (report mode)."""
    rep = run(repo, mode="report")
    return {"techniques": rep.techniques, "papers": rep.papers,
            "verified_gaps": rep.verified_gaps}


@mcp.tool()
def open_issues(repo: str) -> dict:
    """Run the pipeline and open a GitHub issue per verified gap."""
    rep = run(repo, mode="issues")
    return {"issues": rep.issues, "verified_gaps": rep.verified_gaps}


@mcp.tool()
def fix_gap(repo: str, max_prs: int = 1) -> dict:
    """Full loop: verify a gap, code the fix, open a PR (requires allow)."""
    rep = run(repo, mode="pr", allow_pr=True, max_prs=max_prs)
    return {"prs": rep.prs, "issues": rep.issues}


@mcp.tool()
def search_papers(query: str, max_results: int = 8) -> list[dict]:
    """Direct arXiv search (used by the researcher agent)."""
    return [p.__dict__ for p in arxiv_search.search(query, max_results)]


if __name__ == "__main__":
    mcp.run()
