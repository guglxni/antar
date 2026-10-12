"""Report-writer tests (offline)."""
from __future__ import annotations

from pathlib import Path

from antar.report import write_reports
from antar.state import RunState


def _state():
    s = RunState(repo="o/r")
    s.techniques = [{"name": "adamw", "category": "optimizer", "confidence": 1.0,
                     "evidence": ["trainer.py:9"]}]
    s.papers = {"gradient_clipping": [{"arxiv_id": "1905.11881",
                                       "title": "Why gradient clipping accelerates training",
                                       "published": "2019-05-28"}]}
    s.gaps = [{"technique": "gradient_clipping", "kind": "missing",
               "paper": {"arxiv_id": "1905.11881", "title": "Why gradient clipping..."},
               "claim": "missing", "reason": "endorsed", "evidence": ["trainer.py:9"]}]
    return s


def test_write_reports_creates_all_four(tmp_path: Path):
    written = write_reports(_state(), out_dir=tmp_path)
    for name in ["TECHNIQUES.md", "PAPERS.md", "GAPS.md", "RELATED_WORK.md"]:
        assert name in written
        p = Path(written[name])
        assert p.exists() and p.stat().st_size > 0


def test_gaps_md_contains_verifier_reason(tmp_path: Path):
    written = write_reports(_state(), out_dir=tmp_path)
    gaps = Path(written["GAPS.md"]).read_text()
    assert "gradient_clipping" in gaps and "APPROVED" in gaps
