# antar — Build Plan (time-boxed to the remaining window)

Now → submission close (~23:55 IST). Demo-first; cut scope aggressively.

## Phase 0 — Foundations (done / in progress)
- [x] Tool setup: Entire enabled, neatlogs+litellm+openai installed (docs/setup.md)
- [x] Doc suite (PRD/ARCH/DESIGN/REQ/PLAN/MATH/REFERENCES)
- [ ] `.env` filled (user: NEATLOGS_API_KEY, LITELLM_API_KEY)
- [ ] cfo.ai account + MCP auth (user, browser)

## Phase 1 — Walking skeleton, traced (~60 min)
- [ ] `llm.py` BYOK client factory + unit test
- [ ] `tools/ast_scan.py` → TECHNIQUES.md on a fixture repo (e.g. karpathy/minGPT)
- [ ] `orchestrator.py` root WORKFLOW span wrapping one stage
- [ ] **First traced run committed** (EV-2 + first Entire checkpoint)
- [ ] #neatHack "kicked off" post (EV-6)

## Phase 2 — Core value (~120 min)
- [ ] `tools/arxiv_search.py` + `fetch_abstract.py` w/ backoff → PAPERS.md
- [ ] `agents/verifier.py` SOD gate → approved-only gaps
- [ ] `report.py` → GAPS.md + RELATED_WORK.md
- [ ] End-to-end run on minGPT, all 4 artifacts

## Phase 3 — Rubric differentiators (~90 min)
- [ ] Failure-recovery: inject arXiv 500 → backoff+degrade; capture recovery trace (EV-5)
- [ ] Failure→fix evidence: pick a real bug from traces, fix, commit before/after traces (EV-1)
- [ ] `entire graph` snapshots committed (EV-3)
- [ ] cfo.ai business plan from traced token costs (EV-4) — see MATH.md §5

## Phase 4 — Package & submit (~60 min)
- [ ] Pre-cached golden run in `examples/` (offline demo fallback)
- [ ] ≤3-min demo video covering neatlogs + Entire + cfo.ai
- [ ] README polish, `hackathon.md` finalized, all evidence linked
- [ ] Submit via quote-post of official neatlogs X post (19:00–23:55 IST)

## Cut list (drop if time pressure)
- Streamlit front page · multi-repo batch mode · PDF parsing · Discord bot

## Daily evidence hygiene
After each session: append dated `hackathon.md` entry (sanitized; no keys/traces w/ PII).
