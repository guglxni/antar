"""graphify integration — auto-build + query a target repo's knowledge graph.

Auto-wires `graphify update <repo>` when no graph exists, then answers structural
queries via `graphify query --graph <graph.json>`. Falls back gracefully to plain
AST scanning when graphify is unavailable or the graph can't be built.

Per the graphify CLI: `update` is AST-only (no LLM/API cost); `query` does BFS
traversal of graph.json. We default to `--no-cluster --no-viz` for speed in CI.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import neatlogs


def available() -> bool:
    return shutil.which("graphify") is not None


def graph_path(repo_path: str | Path) -> Path:
    return Path(repo_path) / "graphify-out" / "graph.json"


def has_graph(repo_path: str | Path) -> bool:
    return graph_path(repo_path).exists()


@neatlogs.span(kind="TOOL", name="graphify_update")
def ensure_graph(repo_path: str | Path, timeout: int = 300) -> bool:
    """Build the graph if missing (or stale). Returns True if a graph is usable.

    AST-only, no network/model calls. Uses --no-cluster to skip LLM community naming.
    """
    if not available():
        return False
    gp = graph_path(repo_path)
    if gp.exists():
        return True
    try:
        subprocess.run(["graphify", "update", str(repo_path), "--no-cluster"],
                       cwd=str(repo_path), capture_output=True, text=True,
                       timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, OSError) as e:
        neatlogs.log("graphify update failed", level="warning", error=str(e))
        return False
    ok = gp.exists()
    if not ok:
        neatlogs.log("graphify produced no graph.json", level="warning")
    return ok


@neatlogs.span(kind="TOOL", name="graphify_query")
def query(repo_path: str | Path, question: str, budget: int = 1200) -> str:
    """BFS-traverse the graph for a question. Returns text (may be empty)."""
    if not has_graph(repo_path):
        return ""
    try:
        out = subprocess.run(
            ["graphify", "query", question, "--graph", str(graph_path(repo_path)),
             "--budget", str(budget)],
            cwd=str(repo_path), capture_output=True, text=True, timeout=120, check=False)
        return out.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


@neatlogs.span(kind="TOOL", name="graphify_explain")
def explain(repo_path: str | Path, node: str) -> str:
    """Plain-language explanation of a node and its neighbors."""
    if not has_graph(repo_path):
        return ""
    try:
        out = subprocess.run(
            ["graphify", "explain", node, "--graph", str(graph_path(repo_path))],
            cwd=str(repo_path), capture_output=True, text=True, timeout=60, check=False)
        return out.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def technique_hints(repo_path: str | Path, technique: str) -> list[str]:
    """Pull file locations for a technique from the graph (fallback to [])."""
    gp = graph_path(repo_path)
    if not gp.exists():
        return []
    try:
        data = json.loads(gp.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    hits: list[str] = []
    needle = technique.replace("_", "").lower()
    for node in data.get("nodes", []):
        label = str(node.get("norm_label") or node.get("label") or "").replace("_", "").lower()
        if needle and needle in label:
            loc = node.get("source_location", "")
            src = node.get("source_file", "")
            if src:
                hits.append(f"{src}:{loc}" if loc else src)
    return hits[:10]
