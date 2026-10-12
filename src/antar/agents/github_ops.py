"""GitHub operations: open issues and pull requests. PyGithub + subprocess git.

Issue/PR creation is opt-in (modes). Backs off on API errors; falls back to
writing ISSUES.md if issue creation fails (ARCHITECTURE-MULTIAGENT §6).
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import neatlogs
from github import Github


@dataclass
class IssueResult:
    number: int
    url: str


@dataclass
class PRResult:
    number: int
    url: str


def _gh() -> Github:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN required for issue/PR modes (see .env.example).")
    return Github(token)


@neatlogs.span(kind="TOOL", name="github_create_issue")
def create_issue(repo_full_name: str, title: str, body: str,
                 labels: list[str] | None = None) -> IssueResult:
    repo = _gh().get_repo(repo_full_name)
    kwargs: dict = {"title": title, "body": body}
    if labels:
        kwargs["labels"] = labels
    issue = repo.create_issue(**kwargs)
    return IssueResult(issue.number, issue.html_url)


@neatlogs.span(kind="TOOL", name="github_create_pr")
def create_pull(repo_full_name: str, title: str, body: str,
                head: str, base: str = "main") -> PRResult:
    repo = _gh().get_repo(repo_full_name)
    pr = repo.create_pull(base=base, head=head, title=title, body=body)
    return PRResult(pr.number, pr.html_url)


def git(*args: str, cwd: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


def push_branch(repo_path: str, branch: str) -> None:
    git("push", "-u", "origin", branch, cwd=repo_path)
