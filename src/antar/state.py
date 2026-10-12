"""Run state + Entire checkpoint save/restore.

RunState captures the *run* history (resume mid-pipeline on failure).
Entire captures the *development* history (per-commit checkpoints).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RunState:
    repo: str
    stage: str = "init"                 # pipeline cursor for resume
    techniques: list = field(default_factory=list)
    papers: dict = field(default_factory=dict)
    gaps: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    prs: list = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    started_at: float = field(default_factory=time.time)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "RunState":
        return cls(**json.loads(Path(path).read_text()))

    def advance(self, stage: str, path: str | Path) -> None:
        self.stage = stage
        self.save(path)
