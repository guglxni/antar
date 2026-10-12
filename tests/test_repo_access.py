"""Owner-scoping guard tests (no network — parse_target + error paths)."""
from __future__ import annotations

import pytest

from antar.agents.repo_access import OwnershipError, parse_target


def test_parse_owner_name():
    assert parse_target("guglxni/antar") == ("github", "guglxni", "antar")


def test_parse_github_url():
    host, owner, name = parse_target("https://github.com/guglxni/antar.git")
    assert host == "github" and owner == "guglxni" and name == "antar"


def test_parse_gitlab_url():
    host, owner, name = parse_target("https://gitlab.com/mygroup/proj.git")
    assert host == "gitlab" and owner == "mygroup" and name == "proj"


def test_parse_ssh_url():
    host, owner, name = parse_target("git@github.com:guglxni/antar.git")
    assert owner == "guglxni" and name == "antar"


def test_assert_can_write_foreign_repo_refused(monkeypatch):
    """A repo the identity doesn't own must be refused (uses gh token if present)."""
    pytest.importorskip("github")
    import shutil
    import pytest as _pytest
    from antar.agents.repo_access import assert_can_write, OwnershipError
    if shutil.which("gh") is None:
        _pytest.skip("gh CLI not available for token")
    with _pytest.raises(OwnershipError):
        assert_can_write("karpathy/minGPT")  # not owned by the authed identity
