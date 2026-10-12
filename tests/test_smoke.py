"""Smoke tests for the core non-network pieces."""
from __future__ import annotations

import textwrap
from pathlib import Path

from antar.state import RunState
from antar.tools import ast_scan


def test_ast_scan_detects_optimizer(tmp_path: Path):
    (tmp_path / "trainer.py").write_text(textwrap.dedent(
        """
        import torch
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
        norm = torch.nn.LayerNorm(128)
        """
    ))
    techs = {t.name for t in ast_scan.scan_repo(tmp_path)}
    assert "adamw" in techs
    assert "layer_norm" in techs


def test_ast_scan_ignores_venv(tmp_path: Path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "junk.py").write_text("import torch\nSGD(x)")
    (tmp_path / "main.py").write_text("import torch\nAdamW(p)")
    techs = {t.name for t in ast_scan.scan_repo(tmp_path)}
    assert "adamw" in techs


def test_runstate_roundtrip(tmp_path: Path):
    s = RunState(repo="x/y")
    s.advance("scanned", tmp_path / "state.json")
    loaded = RunState.load(tmp_path / "state.json")
    assert loaded.repo == "x/y" and loaded.stage == "scanned"
