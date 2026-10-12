"""Harness-revision loop — the antar coder as test-time adapter.

Implements the inner loop of harness learning (arXiv:2609.35738 §4.2) for code fixes:

    x_t = { task description, current harness, execution report }
    y_i ~ proposer(· | x_t)            # a candidate fix (SEARCH/REPLACE)
    h'_i = Apply(h_{t-1}, y_i)         # apply the edit
    h_t  = Select(...)                 # retain iff dev score improves
    repeat for T rounds using the new execution report

We do NOT train the proposer (no RL / weight updates — solver & proposer stay frozen);
we reuse the paper's *inference-time* loop: feedback from each execution guides the next
revision. The "harness" here is the fix applied to the target code; the "execution report"
is the tester's structured feedback. Coder (aider) is the proposer; Tester produces reports.

Every round is a neatlogs span so the self-improvement is itself traceable evidence.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import neatlogs

from ..agents import tester
from ..llm import resolve_config

_MAX_REVISIONS = 3


def _aider_model_string() -> str:
    cfg = resolve_config()
    if cfg.base_url:
        os.environ.setdefault("OPENAI_API_BASE", cfg.base_url)
        if cfg.provider == "litellm":
            os.environ.setdefault("OPENAI_API_KEY", cfg.api_key)
    return cfg.model


@dataclass
class RevisionResult:
    success: bool
    revisions: int
    final_report: tester.ExecutionReport
    history: list[str] = field(default_factory=list)


@neatlogs.span(kind="AGENT", name="harness_revision_loop")
def revise_until_pass(repo_path: str, fix_summary: str, fnames: list[str],
                      test_cmd: str, max_revisions: int = _MAX_REVISIONS) -> RevisionResult:
    """Propose → apply → execute → read report → revise, until tests pass or budget out.

    Returns RevisionResult; never raises (recovery handled by caller/orchestrator).
    """
    from aider.coders import Coder
    from aider.io import InputOutput
    from aider.models import Model

    model = Model(_aider_model_string())
    io = InputOutput(yes=True)
    history: list[str] = []
    report = tester.ExecutionReport(0.0, False, "", "", 1, 0.0, 0, [])

    for t in range(1, max_revisions + 1):
        # x_t = task + current harness + execution report (paper §4.2 / App E.1)
        instruction = _revision_prompt(fix_summary, report, t)
        with neatlogs.trace(f"propose_revision_{t}", kind="LLM"):
            coder = Coder.create(main_model=model, fnames=fnames, io=io,
                                 auto_commits=True, dirty_commits=True)
            coder.run(instruction)

        # execute + score (Eq. 3: mean score over the "question set" = the test run)
        report = tester.run_tests(repo_path, test_cmd, revision=t, history=list(history))
        history.append(f"rev {t}: score={report.score:.2f} rc={report.returncode}")

        if report.passed:
            return RevisionResult(True, t, report, history)
        # else: loop again — the execution report becomes feedback for the next revision

    return RevisionResult(False, max_revisions, report, history)


def _revision_prompt(fix_summary: str, report: tester.ExecutionReport, round_no: int) -> str:
    base = f"Task: {fix_summary}\n"
    if round_no == 1:
        return base + "\nImplement the minimal, correct change. Do not hard-code answers."
    # subsequent rounds: feed the execution report (the harness-learning signal)
    return (base + "\nThe previous attempt did not pass. Diagnose the failure from this "
            "execution report and make a targeted revision (do not revert unrelated work):\n\n"
            + report.to_prompt_block())
