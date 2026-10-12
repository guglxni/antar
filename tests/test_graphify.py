"""graphify integration tests (graceful fallback; no LLM)."""
from __future__ import annotations

from pathlib import Path

from antar.tools import graphify_integration as gf


def test_available():
    # graphify is installed in this environment
    assert gf.available() is True


def test_ensure_graph_builds(tmp_path: Path):
    (tmp_path / "m.py").write_text("import torch\nopt = torch.optim.AdamW(p)\n")
    ok = gf.ensure_graph(tmp_path)
    # either built or not, must not raise; if built, graph.json exists
    if ok:
        assert gf.has_graph(tmp_path)


def test_technique_hints_empty_without_graph(tmp_path: Path):
    assert gf.technique_hints(tmp_path, "adamw") == []


def test_query_safe_without_graph(tmp_path: Path):
    assert gf.query(tmp_path, "anything") == ""
    assert gf.explain(tmp_path, "node") == ""
