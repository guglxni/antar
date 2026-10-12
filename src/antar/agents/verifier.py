"""SOD verification sub-agent. Adversarially tries to DISPROVE each claimed gap.

Separate LLM call, narrow mandate, strict output schema. Rejected gaps never ship.
Precision model: MATH.md §4.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import neatlogs

from ..llm import get_client

_VERIFY_PROMPT = """You are an adversarial verifier. Try to DISPROVE the claimed gap below.

Claimed gap: {claim}
Technique said to be missing/misused: {technique}
Supporting paper: [{arxiv_id}] {title}
Paper abstract: {abstract}
Code evidence (file:line where technique should/should not be): {evidence}

Decide one verdict:
- APPROVED  — the abstract genuinely supports the claim AND the technique is plausibly absent/misused at the cited lines.
- REJECTED  — the paper id is wrong, the abstract does not support the claim, or the technique is clearly present.
- UNCERTAIN — evidence is insufficient to confirm or deny.

Respond with ONLY valid JSON: {{"verdict": "APPROVED|REJECTED|UNCERTAIN", "reason": "<one sentence>"}}"""


@dataclass
class Verdict:
    verdict: str  # APPROVED | REJECTED | UNCERTAIN
    reason: str


@neatlogs.span(kind="AGENT", name="verifier")
def verify_gap(claim: str, technique: str, arxiv_id: str, title: str,
               abstract: str, evidence: list[str]) -> Verdict:
    client, model = get_client()
    prompt = _VERIFY_PROMPT.format(
        claim=claim, technique=technique, arxiv_id=arxiv_id, title=title,
        abstract=abstract[:1500], evidence=", ".join(evidence[:8]),
    )
    for _ in range(2):  # empty/garbage -> re-prompt once (DESIGN.md §6)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = (resp.choices[0].message.content or "").strip()
        try:
            data = json.loads(text)
            verdict = str(data.get("verdict", "UNCERTAIN")).upper()
            if verdict not in {"APPROVED", "REJECTED", "UNCERTAIN"}:
                verdict = "UNCERTAIN"
            return Verdict(verdict, str(data.get("reason", ""))[:300])
        except (json.JSONDecodeError, AttributeError):
            continue
    return Verdict("UNCERTAIN", "verifier produced unparseable output")
