"""Planner agent — turn a verified gap into an actionable issue/fix spec.

Reads the gap + evidence + (optionally) the graphify code map, and produces a
minimal, testable implementation plan the Coder can execute. Traced AGENT span.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import neatlogs

from ..llm import get_client

_PLAN_PROMPT = """You are a senior ML engineer turning a verified research gap into a minimal fix plan.

Gap technique: {technique}
Paper: [{arxiv_id}] {title}
Abstract: {abstract}
Claim: {claim}
Code evidence (file:line): {evidence}
Repo file list (relevant): {files}

Produce a concrete, minimal plan. Respond with ONLY valid JSON:
{{
  "issue_title": "<short issue title>",
  "issue_body": "<markdown: problem, evidence, acceptance criteria>",
  "fix_summary": "<one sentence: the exact change to make>",
  "target_files": ["<path>", ...],
  "test_cmd": "<e.g. pytest -q or empty if none>",
  "complexity": "low|medium|high"
}}"""


@dataclass
class FixPlan:
    issue_title: str
    issue_body: str
    fix_summary: str
    target_files: list[str]
    test_cmd: str
    complexity: str


@neatlogs.span(kind="AGENT", name="planner")
def plan_fix(gap: dict, repo_files: list[str]) -> FixPlan:
    client, model = get_client()
    p = gap["paper"]
    prompt = _PLAN_PROMPT.format(
        technique=gap["technique"], arxiv_id=p["arxiv_id"], title=p["title"],
        abstract=p.get("abstract", "")[:1200], claim=gap["claim"],
        evidence=", ".join(gap.get("evidence", [])[:8]),
        files=", ".join(repo_files[:30]),
    )
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0)
    text = (resp.choices[0].message.content or "").strip()
    data = json.loads(text[text.find("{"): text.rfind("}") + 1])
    return FixPlan(
        issue_title=str(data.get("issue_title", f"[antar] {gap['technique']}")),
        issue_body=str(data.get("issue_body", gap["claim"])),
        fix_summary=str(data.get("fix_summary", "")),
        target_files=[str(f) for f in data.get("target_files", [])],
        test_cmd=str(data.get("test_cmd", "")),
        complexity=str(data.get("complexity", "medium")),
    )
