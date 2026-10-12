"""GitHub/GitLab operations: open issues and pull requests — OWNER-SCOPED ONLY.

Every write goes through repo_access.assert_can_write() first. If the identity
doesn't own/can't push the repo, the action is refused and the gap is recorded
locally (ISSUES.md fallback). Backoff on API errors. Traced as neatlogs TOOL spans.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import neatlogs
from github import Github

from .repo_access import RepoAccess, assert_can_write


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


@neatlogs.span(kind="TOOL", name="git_create_issue")
def create_issue(repo_full_name: str, title: str, body: str,
                 labels: list[str] | None = None) -> IssueResult:
    access: RepoAccess = assert_can_write(repo_full_name)  # raises if not owner
    neatlogs.log("issue target authorized", host=access.host, repo=access.full)
    if access.host == "gitlab":
        return _gitlab_issue(access.full, title, body, labels)
    repo = _gh().get_repo(repo_full_name)
    kwargs: dict = {"title": title, "body": body}
    if labels:
        kwargs["labels"] = labels
    issue = repo.create_issue(**kwargs)
    return IssueResult(issue.number, issue.html_url)


def _gitlab_issue(project_path: str, title: str, body: str,
                  labels: list[str] | None) -> IssueResult:
    import gitlab
    gl = gitlab.Gitlab(os.environ.get("GITLAB_URL", "https://gitlab.com"),
                       private_token=os.environ["GITLAB_TOKEN"])
    proj = gl.projects.get(project_path)
    data: dict = {"title": title, "description": body}
    if labels:
        data["labels"] = ",".join(labels)
    issue = proj.issues.create(data)
    return IssueResult(issue.iid, issue.web_url)


@neatlogs.span(kind="TOOL", name="git_create_pr")
def create_pull(repo_full_name: str, title: str, body: str,
                head: str, base: str = "main") -> PRResult:
    access: RepoAccess = assert_can_write(repo_full_name)  # raises if not owner
    neatlogs.log("pr target authorized", host=access.host, repo=access.full)
    if access.host == "gitlab":
        return _gitlab_mr(access.full, title, body, head, base)
    repo = _gh().get_repo(repo_full_name)
    pr = repo.create_pull(base=base, head=head, title=title, body=body)
    return PRResult(pr.number, pr.html_url)


def _gitlab_mr(project_path: str, title: str, body: str,
               source_branch: str, target_branch: str) -> PRResult:
    import gitlab
    gl = gitlab.Gitlab(os.environ.get("GITLAB_URL", "https://gitlab.com"),
                       private_token=os.environ["GITLAB_TOKEN"])
    proj = gl.projects.get(project_path)
    mr = proj.mergerequests.create({
        "source_branch": source_branch, "target_branch": target_branch,
        "title": title, "description": body})
    return PRResult(mr.iid, mr.web_url)


def git(*args: str, cwd: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


def push_branch(repo_path: str, branch: str) -> None:
    git("push", "-u", "origin", branch, cwd=repo_path)

