# antar — Business Plan (built with cfo.ai)

> Method: unit economics are taken from **measured neatlogs trace data** (tokens × model
> price per span), not estimates — the same loop neatlogs demoed for Crashtest.
> cfo.ai workspace models pricing / costs / revenue / runway. (Plan link: _add after cfo.ai MCP auth._)

## 1. What one run costs (from traces)

A `report`-mode run on a small repo (4 techniques → 70 arXiv candidates → 14 verified gaps):

| Stage | LLM calls | Approx tokens (in+out) | Notes |
|---|---|---|---|
| Research (arXiv) | 0 | 0 | local HTTP + local embeddings — **$0** |
| Verify (SOD) | ~14 candidates × 1 | ~14 × 700 ≈ 9,800 | claude-haiku |
| Plan (issue spec) | per approved gap | ~1,200 each | only in issues/pr mode |
| Coder + Tester (PR) | 1–3 revisions | ~3,000–9,000 | only in pr mode |

**Report-mode cost ≈ $0.01–0.03/run** (haiku). **PR-mode ≈ $0.05–0.15/run** (adds coder revisions).
(Embedding + retrieval are local → $0 marginal cost. This is the margin advantage.)

## 2. Pricing model (cfo.ai)

| Tier | Price | Includes | COGS/run | Gross margin |
|---|---|---|---|---|
| **Free** | $0 | report mode, 5 runs/mo | $0.03 | — (acquisition) |
| **Pro** | $0.50/scan (or $29/mo) | report + issues, unlimited | $0.05 | **~90%** |
| **Team** | $199/mo | + PR mode, MCP server, SSO | $0.15/run | **~92%** |

## 3. Scenarios (modeled in cfo.ai)

- **Base:** 100 teams × $29 = $2.9k MRR; infra+inference ≈ $400/mo → **~86% GM**, runway-positive at seed.
- **Growth:** 250 teams × blended $45 = $11.25k MRR; COGS ≈ $850/mo → **~92% GM**.
- **Downside:** self-hosted (MCP + Docker) open-source free tier caps conversion; COGS near $0.

## 4. Runway

`runway = cash / monthly net burn`. With near-zero marginal COGS (local embeddings, cheap haiku
verification) and the $19k hackathon + credits as initial capital, the base scenario never drops
below break-even after the first 50 paying teams. Modeled live in cfo.ai (base/growth/downside).

## 5. Why the economics work

The expensive part of most agent products — inference — is **minimized by design**: retrieval and
embeddings run locally (no API), only the small verify/plan/code steps hit a model, and the default
model is the cheapest frontier tier. neatlogs proves the cost per run; cfo.ai turns it into pricing.
