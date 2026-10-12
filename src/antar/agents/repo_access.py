"""Repo access & ownership guard. Issues/PRs are OWNER-ONLY.

A remote write (issue/PR/push) is allowed ONLY when the authenticated identity
owns the repo (GitHub: owner.login == me.login AND permissions.push) or holds
Developer+ access (GitLab: access_level >= DEVELOPER). Otherwise the action is
refused and the gap is reported locally instead. This is a hard safety boundary.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse


class OwnershipError(PermissionError):
    """Raised when a write is attempted on a repo the identity doesn't own."""


def _gh_cli_token() -> str | None:
    """Reuse the user's `gh` session token (keyring) if present."""
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


@dataclass
class RepoAccess:
    host: str            # "github" | "gitlab"
    owner: str           # repo owner/namespace
    name: str            # repo name
    full: str            # "owner/name" (github) or "group/proj" (gitlab)
    can_write: bool      # push/owner/developer+
    reason: str


def parse_target(repo: str) -> tuple[str, str, str]:
    """Return (host_hint, owner, name) from 'owner/name' or a git URL."""
    if repo.startswith("git@"):
        # git@host:owner/name.git
        host_part, _, path_part = repo.partition(":")
        host = "gitlab" if "gitlab" in host_part else "github"
        parts = [p for p in path_part.strip("/").split("/") if p]
        name = parts[-1].removesuffix(".git")
        owner = "/".join(parts[:-1])
        return host, owner, name
    if repo.startswith(("http://", "https://")):
        u = urlparse(repo)
        host = "gitlab" if "gitlab" in u.netloc else "github"
        parts = [p for p in u.path.strip("/").split("/") if p]
        name = parts[-1].removesuffix(".git")
        owner = "/".join(parts[:-1])
        return host, owner, name
    parts = repo.split("/")
    return "github", parts[0], "/".join(parts[1:])


# ── GitHub ────────────────────────────────────────────────────────────────

def github_access(repo_full: str) -> RepoAccess:
    from github import Github
    token = os.environ.get("GITHUB_TOKEN") or _gh_cli_token()
    if not token:
        raise OwnershipError("No GitHub token (set GITHUB_TOKEN or `gh auth login`).")
    g = Github(token)
    me = g.get_user().login
    repo = g.get_repo(repo_full)
    owner = repo.owner.login
    perms = getattr(repo, "permissions", None)
    push = bool(getattr(perms, "push", False) or getattr(perms, "admin", False)
                or getattr(perms, "maintain", False))
    is_owner = owner.lower() == me.lower()
    can_write = is_owner and push
    reason = ("owner+push" if can_write else
              f"not owner (owner={owner}, you={me}) or no push perm")
    return RepoAccess("github", owner, repo.name, repo_full, can_write, reason)


# ── GitLab ────────────────────────────────────────────────────────────────

def gitlab_access(project_path: str) -> RepoAccess:
    import gitlab
    from gitlab import const
    url = os.environ.get("GITLAB_URL", "https://gitlab.com")
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        raise OwnershipError("GITLAB_TOKEN not set (owner-scoped writes need it).")
    gl = gitlab.Gitlab(url, private_token=token)
    gl.auth()
    proj = gl.projects.get(project_path)
    # permission = max of project membership + group membership
    level = 0
    pa = getattr(proj, "permissions", None) or {}
    for k in ("project_access", "group_access"):
        node = pa.get(k)
        if node:
            level = max(level, node.get("access_level", 0))
    can_write = level >= const.DEVELOPER_ACCESS
    owner = proj.namespace.get("full_path", "") if isinstance(proj.namespace, dict) else ""
    return RepoAccess("gitlab", owner, proj.name, project_path, can_write,
                      f"access_level={level} (need >= {const.DEVELOPER_ACCESS})")


# ── unified guard ─────────────────────────────────────────────────────────

def assert_can_write(repo: str) -> RepoAccess:
    """Resolve access for a target; raise OwnershipError if not writable by owner."""
    host, owner, name = parse_target(repo)
    full = f"{owner}/{name}"
    access = gitlab_access(full) if host == "gitlab" else github_access(full)
    if not access.can_write:
        raise OwnershipError(f"Refusing write to {access.full}: {access.reason}")
    return access


def default_branch(repo_path: str) -> str:
    try:
        return subprocess.run(["git", "symbolic-ref", "--short", "HEAD"],
                              cwd=repo_path, capture_output=True, text=True).stdout.strip() or "main"
    except Exception:
        return "main"
