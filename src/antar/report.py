"""Report writer — emit the markdown artifacts the docs promise.

Writes TECHNIQUES.md, PAPERS.md, GAPS.md, RELATED_WORK.md into the run's output
dir (default ./antar-out/). These are antar's deliverables for report mode and
the human-readable record behind any issues/PRs it opens.
"""
from __future__ import annotations

from pathlib import Path

import neatlogs


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")


@neatlogs.span(kind="CHAIN", name="write_reports")
def write_reports(state, out_dir: str | Path = "antar-out") -> dict:
    """Write all four artifacts from a RunState. Returns {name: path}."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    # TECHNIQUES.md — what the code is doing now
    t = out / "TECHNIQUES.md"
    t.write_text(_techniques_md(state))
    written["TECHNIQUES.md"] = str(t)

    # PAPERS.md — what the literature says
    p = out / "PAPERS.md"
    p.write_text(_papers_md(state))
    written["PAPERS.md"] = str(p)

    # GAPS.md — verified gaps only
    g = out / "GAPS.md"
    g.write_text(_gaps_md(state))
    written["GAPS.md"] = str(g)

    # RELATED_WORK.md — LaTeX-ready bibliography
    r = out / "RELATED_WORK.md"
    r.write_text(_related_work_md(state))
    written["RELATED_WORK.md"] = str(r)

    return written


def _techniques_md(state) -> str:
    lines = ["# TECHNIQUES — detected in the codebase", ""]
    if not state.techniques:
        lines.append("_No techniques detected._")
    for t in state.techniques:
        ev = ", ".join(t.get("evidence", [])[:6])
        lines.append(f"- **{t.get('name')}** ({t.get('category')}) — conf {t.get('confidence', 0):.2f}")
        if ev:
            lines.append(f"  - evidence: `{ev}`")
    return "\n".join(lines) + "\n"


def _papers_md(state) -> str:
    lines = ["# PAPERS — literature per technique", ""]
    for tech, papers in state.papers.items():
        lines.append(f"## {tech}")
        for p in papers[:5]:
            lines.append(f"- [{p.get('arxiv_id')}] {_md_escape(p.get('title', ''))} ({p.get('published','')})")
        lines.append("")
    return "\n".join(lines)


def _gaps_md(state) -> str:
    sev_icon = {"critical": "🔴", "improvement": "🟡", "experimental": "🟢"}
    lines = ["# GAPS — verified findings", ""]
    if not state.gaps:
        lines.append("_No verified gaps._")
    for g in state.gaps:
        icon = sev_icon.get(g.get("severity", "improvement"), "🟡")
        p = g.get("paper", {})
        lines.append(f"### {icon} {g.get('technique')} ({g.get('kind', 'gap')})")
        lines.append(f"- **Paper:** [{p.get('arxiv_id','')}] {_md_escape(p.get('title',''))}")
        lines.append(f"- **Claim:** {g.get('claim','')}")
        lines.append(f"- **Verifier:** APPROVED — {g.get('reason','')}")
        ev = ", ".join(g.get("evidence", [])[:6])
        if ev:
            lines.append(f"- **Evidence:** `{ev}`")
        lines.append("")
    return "\n".join(lines)


def _related_work_md(state) -> str:
    lines = ["# RELATED WORK — LaTeX-ready", "", "```latex"]
    seen = set()
    for tech, papers in state.papers.items():
        for p in papers:
            aid = p.get("arxiv_id", "")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            key = aid.replace(".", "")
            title = _md_escape(p.get("title", "")).replace("{", "").replace("}", "")
            lines.append(f"\\bibitem{{{key}}} {title}. arXiv:{aid} ({p.get('published','')[:4]}).")
    lines.append("```")
    return "\n".join(lines) + "\n"
