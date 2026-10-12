"""AST-based technique scanner. Stdlib `ast` only — no heavy deps.

Walks a target repo's .py files, matches Call/Attribute/Name nodes against the
ML-technique taxonomy, returns Technique objects with file:line evidence.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

# name fragment -> (technique, category, weight)
SIGNATURES: dict[str, tuple[str, str, float]] = {
    "AdamW": ("adamw", "optimizer", 1.0),
    "Adam": ("adam", "optimizer", 1.0),
    "SGD": ("sgd", "optimizer", 1.0),
    "clip_grad_norm_": ("gradient_clipping", "regularizer", 1.0),
    "CosineAnnealing": ("cosine_annealing", "scheduler", 1.0),
    "CosineAnnealingWarmRestarts": ("cosine_annealing", "scheduler", 1.0),
    "warmup": ("warmup", "scheduler", 0.5),
    "autocast": ("mixed_precision", "precision", 0.9),
    "GradScaler": ("mixed_precision", "precision", 1.0),
    "Dropout": ("dropout", "regularizer", 1.0),
    "BatchNorm": ("batch_norm", "normalization", 1.0),
    "LayerNorm": ("layer_norm", "normalization", 1.0),
    "MultiheadAttention": ("multihead_attention", "architecture", 1.0),
    "data_augmentation": ("augmentation", "data", 0.4),
    "early_stopping": ("early_stopping", "training", 0.6),
    "checkpoint": ("checkpointing", "training", 0.3),
}


@dataclass
class Technique:
    name: str
    category: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def add(self, loc: str, weight: float) -> None:
        self.evidence.append(loc)
        # noisy-or combination (MATH.md §1)
        self.confidence = 1 - (1 - self.confidence) * (1 - weight)


class _Visitor(ast.NodeVisitor):
    def __init__(self, path: Path, found: dict[str, Technique]):
        self.path = path
        self.found = found

    def _record(self, name: str, lineno: int) -> None:
        for frag, (tech, cat, w) in SIGNATURES.items():
            if frag in name:
                key = tech
                if key not in self.found:
                    self.found[key] = Technique(tech, cat)
                rel = str(self.path)
                self.found[key].add(f"{rel}:{lineno}", w)

    def visit_Call(self, node: ast.Call) -> None:
        name = ""
        f = node.func
        if isinstance(f, ast.Attribute):
            name = f.attr
        elif isinstance(f, ast.Name):
            name = f.id
        if name:
            self._record(name, node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._record(node.attr, node.lineno)
        self.generic_visit(node)


def scan_repo(repo_path: str | Path) -> list[Technique]:
    """Scan all .py under repo_path; return techniques with confidence >= 0.5."""
    root = Path(repo_path)
    found: dict[str, Technique] = {}
    for py in sorted(root.rglob("*.py")):
        if any(p in py.parts for p in {".venv", "venv", "node_modules", ".git"}):
            continue
        try:
            tree = ast.parse(py.read_text(errors="ignore"))
        except SyntaxError:
            continue
        _Visitor(py.relative_to(root), found).visit(tree)
    return [t for t in found.values() if t.confidence >= 0.5]
