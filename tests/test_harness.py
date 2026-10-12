"""Harness-revision loop tests (execution report + repo intake; no network/LLM)."""
from __future__ import annotations

from pathlib import Path

from antar.agents import tester
from antar.tools import repo_intake


def test_execution_report_prompt_block():
    r = tester.ExecutionReport(0.5, False, "1 failed, 1 passed", "", 1, 0.2, 2, ["rev 1: fail"])
    block = r.to_prompt_block()
    assert "FAIL" in block and "revision 2" in block and "rev 1" in block


def test_run_tests_no_cmd_passes(tmp_path: Path):
    r = tester.run_tests(str(tmp_path), "", revision=0)
    assert r.passed and r.score == 1.0


def test_run_tests_passing(tmp_path: Path):
    r = tester.run_tests(str(tmp_path), "exit 0", revision=1)
    assert r.passed and r.returncode == 0


def test_run_tests_failing_captures_tail(tmp_path: Path):
    r = tester.run_tests(str(tmp_path), "echo '3 passed, 1 failed'; exit 1", revision=1)
    assert not r.passed
    assert r.score == 0.75
    assert "failed" in r.stdout_tail


def test_repo_intake_local(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    local = repo_intake.resolve(str(tmp_path))
    assert local.host == "local" and not local.cloned and local.path == tmp_path.resolve()
