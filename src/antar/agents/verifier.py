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

_VERIFY_PROMPT = """You are an adversarial verifier. Evaluate whether the claimed gap is REAL.

Claimed gap: {claim}
Technique: {technique}
Is the technique PRESENT in the code? {present}
Code context: this is a PyTorch training loop using an optimizer; the relevant
training-step code sites are: {evidence}. (If the technique is reported MISSING,
these are the locations where it would normally appear.)
Supporting paper: [{arxiv_id}] {title}
Paper abstract: {abstract}

Rules:
- APPROVED  — the abstract endorses/recommends the technique as beneficial or standard
  for training, AND (if reported MISSING) it is plausibly absent from the cited code.
  A paper that *improves on* or *builds on* a technique still counts as endorsing it.
- REJECTED — the paper is unrelated to the technique, OR the technique is clearly already present.
- UNCERTAIN — the abstract neither supports nor relates to the claim.

Do NOT reject merely because evidence is sparse when the technique is reported MISSING;
judge whether the paper supports adopting it. Respond with ONLY valid JSON:
{{"verdict": "APPROVED|REJECTED|UNCERTAIN", "reason": "<one sentence>"}}"""


@dataclass
class Verdict:
    verdict: str  # APPROVED | REJECTED | UNCERTAIN
    reason: str


@neatlogs.span(kind="AGENT", name="verifier")
def verify_gap(claim: str, technique: str, arxiv_id: str, title: str,
               abstract: str, evidence: list[str], present: bool = False) -> Verdict:
    client, model = get_client()
    prompt = _VERIFY_PROMPT.format(
        claim=claim, technique=technique, present=("yes" if present else "no"),
        arxiv_id=arxiv_id, title=title,
        abstract=abstract[:1500], evidence=", ".join(evidence[:8]) or "(none cited)",
    )
    for _ in range(2):  # empty/garbage -> re-prompt once (DESIGN.md §6)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = (resp.choices[0].message.content or "").strip()
        # strip markdown code fences (models often wrap JSON in ```json ... ```)
        if text.startswith("```"):
            text = text.split("```", 2)[1] if "```" in text[3:] else text
            text = text.removeprefix("json").strip().rstrip("`").strip()
        try:
            data = json.loads(text)
            verdict = str(data.get("verdict", "UNCERTAIN")).upper()
            if verdict not in {"APPROVED", "REJECTED", "UNCERTAIN"}:
                verdict = "UNCERTAIN"
            return Verdict(verdict, str(data.get("reason", ""))[:300])
        except (json.JSONDecodeError, AttributeError):
            continue
    return Verdict("UNCERTAIN", "verifier produced unparseable output")
