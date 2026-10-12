# antar — Hackathon Proposal (the pitch)

## The problem, precisely
ML code drifts from the state of the art. Engineers ship and iterate but rarely survey
the literature, so they debug bottlenecks a paper already solved, skip standard
techniques, and lose hours to ungrounded arXiv searches.

## The agent
`antar` reads your actual code, hunts the current literature, **independently verifies**
each finding (segregation of duties), and hands back a ranked, evidence-backed gap report
with a LaTeX-ready Related Work section. It recovers from its own tool failures and is
fully observable end-to-end.

## Why it wins the rubric
- **The agent (30%):** a real plan→act→verify→recover→iterate loop on a substantial task,
  not a thin wrapper. Verification and recovery are first-class.
- **Partner tools (25%):** neatlogs traces every span; Entire checkpoints every commit and
  maps the repo; cfo.ai turns the agent's *own traced token costs* into its business plan.
- **Demo (20%):** the traces and checkpoints ARE the demo — judges see the agent think.
- **Build in public (15%):** #neatHack posts throughout.
- **Originality (10%):** code-grounded (not another abstract summarizer) + a verifier that
  tries to *disprove* its own claims — "overturned, not hidden."

## The business (cfo.ai)
Unit cost per scan from real traces → tiered pricing (free / pro / team) → gross margin →
runway. Illustrative: at ~$0.04/scan cost and $0.50/scan pro price → ~92% gross margin.

## The ask
Judge the loop, the evidence, and the verification discipline — that's the whole product.
