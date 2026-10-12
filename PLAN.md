# antar — Build Plan (time-boxed to the submission window)

**Status: COMPLETE.** Kept as the build record. Demo-first; scope was cut aggressively.

## Phase 0 — Foundations ✅
- [x] Tool setup: Entire enabled, neatlogs+litellm+openai installed (docs/setup.md)
- [x] Doc suite (PRD/ARCH/DESIGN/REQ/PLAN/MATH/REFERENCES)
- [x] `.env` filled (NEATLOGS_API_KEY, LITELLM_API_KEY) via scripts/load-env.sh
- [x] cfo.ai account + MCP auth (Hermes MCP, OAuth)

## Phase 1 — Walking skeleton, traced ✅
- [x] `llm.py` BYOK client factory + tests
- [x] `tools/ast_scan.py` → technique inventory on a fixture repo
- [x] `orchestrator.py` root WORKFLOW span
- [x] First traced run committed (neatlogs doctor probe PASS)

## Phase 2 — Core value ✅
- [x] `tools/arxiv_search.py` w/ backoff + `tools/rag.py` hybrid retrieval → PAPERS.md
- [x] `agents/verifier.py` SOD gate → approved-only gaps
- [x] `report.py` → GAPS.md + RELATED_WORK.md (+ TECHNIQUES.md, PAPERS.md)
- [x] End-to-end run on a real repo (antar-demo-target), all 4 artifacts

## Phase 3 — Rubric differentiators ✅
- [x] Failure-recovery: arXiv backoff+degrade; harness revision loop on test failure (EV-5)
- [x] Failure→fix evidence: verifier fence-parse + gap-logic fix → 0→14 gaps, in traces (EV-1)
- [x] `entire graph` + `entire enable` repo-context evidence (EV-3)
- [x] cfo.ai business plan from traced token costs (EV-4) — docs/BUSINESS-PLAN.md
- [x] Multi-agent upgrade: scanner/researcher/verifier/planner/coder/tester/github agents
- [x] Harness learning (arXiv:2609.35738) test-time revision loop — MATH.md §8
- [x] Owner-scoped GitHub/GitLab writes (repo_access guard)
- [x] Hybrid RAG discovery (BM25 + local dense + RRF + recency), keyless
- [x] FastAPI webapp + hardened MCP server (auth + RBAC)

## Phase 4 — Package & submit ✅
- [x] Demo video ≤3 min (92s) covering neatlogs + Entire + cfo.ai → examples/antar-demo.mp4
- [x] README polish (badges, video, diagrams), hackathon.md finalized, evidence linked
- [x] Built in public: 2 #neatHack posts (links in hackathon.md)
- [x] Submitted via quote-post

## Cut list (dropped — deliberate scope control)
- Streamlit front page (used FastAPI webapp instead) · multi-repo batch mode ·
  PDF parsing · Discord bot · GRPO proposer training (future work)

## Evidence hygiene
Dated, sanitized `hackathon.md` entries after each session; no keys/PII committed.
