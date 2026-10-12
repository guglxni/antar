"""Orchestrator — the coordinator. plan → dispatch → settle → report.

Root neatlogs WORKFLOW span. Dispatches specialised sub-agents, checkpoints
state with Entire after every stage, recovers from tool failure, and
(optionally) drives issues → PRs. Never writes code/papers itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import neatlogs

from .agents import github_ops, harness, planner, verifier
from .llm import get_client, init_tracing
from .state import RunState
from .tools import arxiv_search, ast_scan, repo_intake

STATE_PATH = ".antar/run_state.json"


@neatlogs.span(kind="TOOL", name="arxiv_search")
def _research(technique: str) -> list[arxiv_search.Paper]:
    from .tools import rag
    raw = arxiv_search.search(technique)
    return rag.rerank(technique, raw, top_k=5)  # hybrid BM25+dense+RRF+recency


@neatlogs.span(kind="TOOL", name="ast_scan")
def _scan(repo: str) -> list[ast_scan.Technique]:
    return ast_scan.scan_repo(repo)


@dataclass
class RunReport:
    techniques: int
    papers: int
    verified_gaps: int
    issues: list
    prs: list


def run(repo: str, mode: str = "report", allow_pr: bool = False,
        max_prs: int = 1, offline: bool = False) -> RunReport:
    """Full multi-agent pipeline. mode: report | issues | pr."""
    init_tracing()
    state = RunState(repo=repo)

    with neatlogs.trace("antar-run", kind="WORKFLOW"):
        # 0. INTAKE — resolve/clone to a local working copy
        local = repo_intake.resolve(repo)
        repo_path = str(local.path)
        state.advance("intake", STATE_PATH)

        # 1. SCAN
        techniques = _scan(repo_path)
        state.techniques = [t.__dict__ for t in techniques]
        state.advance("scanned", STATE_PATH)

        # 2. RESEARCH + VERIFY
        approved: list[dict] = []
        n_papers = 0
        for t in techniques:
            papers = _research(t.name.replace("_", " "))
            n_papers += len(papers)
            state.papers[t.name] = [p.__dict__ for p in papers]
            for p in papers[:3]:  # top-3 per technique
                claim = f"Repo may be missing/misusing {t.name}; see {p.title}"
                v = verifier.verify_gap(claim, t.name, p.arxiv_id, p.title,
                                        p.abstract, t.evidence)
                if v.verdict == "APPROVED":
                    approved.append({"technique": t.name, "paper": p.__dict__,
                                     "claim": claim, "reason": v.reason,
                                     "evidence": t.evidence})
        state.gaps = approved
        state.advance("verified", STATE_PATH)

        # 3. PLAN + ISSUES
        issues: list = []
        repo_files = _list_py_files(repo_path)
        plans: dict[str, planner.FixPlan] = {}
        if mode in {"issues", "pr"}:
            for g in approved:
                try:
                    plan = planner.plan_fix(g, repo_files)
                    plans[g["technique"]] = plan
                    r = github_ops.create_issue(local.full, plan.issue_title,
                                                body=plan.issue_body,
                                                labels=["antar", "ml-gap"])
                    issues.append(r.url)
                except Exception as e:
                    neatlogs.log("issue creation failed", level="warning",
                                 error=str(e), gap=g["technique"])
        state.issues = issues
        state.advance("issues", STATE_PATH)

        # 4. PRs (opt-in, capped) — harness-revision loop: propose→execute→read→revise
        prs: list = []
        if mode == "pr" and allow_pr:
            for g in approved[:max_prs]:
                try:
                    plan = plans.get(g["technique"]) or planner.plan_fix(g, repo_files)
                    branch = f"antar/{g['technique']}"
                    github_ops.git("checkout", "-b", branch, cwd=repo_path)
                    fnames = plan.target_files or _evidence_files(g)
                    result = harness.revise_until_pass(
                        repo_path, plan.fix_summary, fnames, plan.test_cmd)
                    neatlogs.log("harness revision done", success=result.success,
                                 revisions=result.revisions, gap=g["technique"])
                    if not result.success:
                        neatlogs.log("gap not resolved within revision budget",
                                     level="warning", gap=g["technique"])
                        continue
                    github_ops.push_branch(repo_path, branch)
                    pr = github_ops.create_pull(
                        local.full, f"[antar] Address {g['technique']} gap",
                        body=_pr_body(g), head=branch, base=local.default_branch)
                    prs.append(pr.url)
                except Exception as e:
                    neatlogs.log("pr creation failed", level="warning",
                                 error=str(e), gap=g["technique"])
        state.prs = prs
        state.advance("done", STATE_PATH)

    return RunReport(len(techniques), n_papers, len(approved), issues, prs)


def _list_py_files(repo_path: str) -> list[str]:
    from pathlib import Path
    root = Path(repo_path)
    return [str(p.relative_to(root)) for p in sorted(root.rglob("*.py"))
            if not any(x in p.parts for x in {".venv", "venv", ".git", "node_modules"})][:50]


def _evidence_files(g: dict) -> list[str]:
    return sorted({e.split(":")[0] for e in g.get("evidence", [])})


def _issue_body(g: dict) -> str:
    return (f"### Detected gap: `{g['technique']}`\n\n"
            f"**Paper:** [{g['paper']['arxiv_id']}] {g['paper']['title']}\n\n"
            f"**Claim:** {g['claim']}\n\n"
            f"**Verifier:** APPROVED — {g['reason']}\n\n"
            f"**Evidence:** " + ", ".join(g.get("evidence", [])[:8]) +
            "\n\n_Generated by antar (verified)._")


def _fix_instruction(g: dict) -> str:
    return (f"Implement the standard technique `{g['technique']}` as described in "
            f"the paper '{g['paper']['title']}'. Minimal, correct change. Add/adjust "
            f"tests. Do not refactor unrelated code.")


def _pr_body(g: dict) -> str:
    return (f"Addresses the verified `{g['technique']}` gap.\n\n"
            f"**Paper:** [{g['paper']['arxiv_id']}] {g['paper']['title']}\n"
            f"**Verifier note:** {g['reason']}\n\n_Generated by antar._")
