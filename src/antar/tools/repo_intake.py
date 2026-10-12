"""Repo intake: resolve a target (local path | owner/name | git URL) to a local
working copy. Clones into a workspace, records the default branch, and detects
the host so owner-scoped writes can be enforced upstream.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..agents.repo_access import parse_target

WORKSPACE = Path(".antar/workspaces")


@dataclass
class LocalRepo:
    path: Path
    host: str            # github | gitlab | local
    full: str            # owner/name (or local dir name)
    default_branch: str
    cloned: bool


def _git(*args: str, cwd: str | Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, check=True).stdout.strip()


def _default_branch(path: Path) -> str:
    try:
        return _git("symbolic-ref", "--short", "HEAD", cwd=path) or "main"
    except Exception:
        return "main"


def resolve(repo: str, workspace: Path = WORKSPACE) -> LocalRepo:
    """Return a LocalRepo for a path, owner/name (GitHub), or git URL. Clone if remote."""
    p = Path(repo)
    if p.exists() and (p / ".git").exists():
        return LocalRepo(p.resolve(), "local", p.name, _default_branch(p), cloned=False)

    host, owner, name = parse_target(repo)
    if host == "local":
        raise FileNotFoundError(f"repo not found locally and not a URL: {repo}")

    url = repo if repo.startswith(("http", "git@")) else f"https://{host}.com/{owner}/{name}.git"
    dest = workspace / owner.replace("/", "_") / name
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "50", url, str(dest)],
                       capture_output=True, text=True, check=True)
        cloned = True
    else:
        cloned = False
    return LocalRepo(dest.resolve(), host, f"{owner}/{name}", _default_branch(dest), cloned)
