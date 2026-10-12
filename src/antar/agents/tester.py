"""Tester agent — run the test/lint command, produce a structured ExecutionReport.

The ExecutionReport is the harness-learning feedback artifact (arXiv:2609.35738 §4.1,
Appendix E.2): scores, failing traces, and revision history feed the next revision.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field

import neatlogs


@dataclass
class ExecutionReport:
    """Feedback object consumed by the harness proposer (paper §4.1)."""
    score: float                 # 1.0 pass, else fraction of tests passed, 0.0 on hard fail
    passed: bool
    stdout_tail: str             # last lines — the "failed-example trace excerpt"
    stderr_tail: str
    returncode: int
    duration_s: float
    revision: int = 0            # which harness revision this report belongs to
    history: list[str] = field(default_factory=list)  # prior revision summaries

    def to_prompt_block(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (f"### Execution report (revision {self.revision}) — {status}\n"
                f"score: {self.score:.2f} · exit {self.returncode} · {self.duration_s:.1f}s\n"
                f"--- failing output (tail) ---\n{self.stdout_tail}\n{self.stderr_tail}\n"
                + (f"--- revision history ---\n" + "\n".join(self.history) if self.history else ""))


def _tail(text: str, n: int = 40) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:])


@neatlogs.span(kind="TOOL", name="run_tests")
def run_tests(repo_path: str, test_cmd: str, revision: int = 0,
              history: list[str] | None = None, timeout: int = 300) -> ExecutionReport:
    if not test_cmd:
        return ExecutionReport(1.0, True, "(no test_cmd — treated as pass)", "", 0, 0.0,
                               revision, history or [])
    t0 = time.time()
    try:
        proc = subprocess.run(test_cmd, shell=True, cwd=repo_path,
                              capture_output=True, text=True, timeout=timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        rc, err = 124, err + "\nTIMEOUT"
    dur = time.time() - t0

    passed = rc == 0
    # crude score: 1.0 pass; else fraction of "passed" vs "failed" pytest lines if present
    score = 1.0 if passed else _estimate_score(out)
    return ExecutionReport(score, passed, _tail(out), _tail(err), rc, dur,
                           revision, history or [])


def _estimate_score(pytest_out: str) -> float:
    import re
    m_pass = re.search(r"(\d+) passed", pytest_out)
    m_fail = re.search(r"(\d+) failed", pytest_out)
    if m_pass and m_fail:
        p, f = int(m_pass.group(1)), int(m_fail.group(1))
        return p / max(1, p + f)
    return 0.0
