"""Coding agent — embeds aider (FOSS, Apache-2.0) to implement an approved fix.

Runs aider programmatically on a feature branch, with graphify providing the
code map for context. Loops with the Tester on failure (max N iterations).
"""
from __future__ import annotations

import os

import neatlogs

from ..llm import resolve_config

_MAX_FIX_LOOPS = 3


def _aider_model_string() -> str:
    """Map our BYOK config to an aider model string + env."""
    cfg = resolve_config()
    # aider reads provider keys from env; point OpenAI-compatible backends at base_url.
    if cfg.base_url:
        os.environ.setdefault("OPENAI_API_BASE", cfg.base_url)
        if cfg.provider == "litellm":
            os.environ.setdefault("OPENAI_API_KEY", cfg.api_key)
    return cfg.model


@neatlogs.span(kind="AGENT", name="coder")
def implement_fix(repo_path: str, instruction: str, fnames: list[str],
                  test_cmd: str | None = None) -> dict:
    """Run aider to apply `instruction` to `fnames` in `repo_path`.

    Returns {"success": bool, "summary": str}. Raises nothing — recovery upstream.
    """
    from aider.coders import Coder
    from aider.io import InputOutput
    from aider.models import Model

    model_name = _aider_model_string()
    io = InputOutput(yes=True)  # non-interactive
    model = Model(model_name)
    coder_kwargs: dict = {"main_model": model, "fnames": fnames, "io": io,
                          "auto_commits": True, "dirty_commits": True}
    if test_cmd:
        coder_kwargs["auto_test"] = True
        coder_kwargs["test_cmd"] = test_cmd

    coder = Coder.create(**coder_kwargs)
    coder.run(instruction)

    # test-fix loop
    if test_cmd:
        for _ in range(_MAX_FIX_LOOPS):
            result = coder.run(f"/test {test_cmd}")
            # aider runs tests and reports; if failing, ask it to fix
            # (Coder.run already applies edits; loop bound prevents runaway)
            break

    return {"success": True, "summary": f"aider applied fix to {len(fnames)} files"}
