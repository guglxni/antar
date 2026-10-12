# antar — Requirements (numbered & testable)

Status: `✅ done` `🚧 in progress` `⬜ planned`. Each FR maps to a test in `tests/`.
Status reflects the **verified live run** on `guglxni/antar-demo-target` (2026-10-12).

## Functional

| ID | Requirement | Acceptance | Status |
|----|-------------|-----------|--------|
| FR-1 | Accept a local path or public git URL | `repo_intake.resolve()` clones GitHub/GitLab or reads in place | ✅ |
| FR-2 | AST-scan `.py` → technique inventory | technique + file:line, noisy-or confidence; verified on demo repo (4 detected) | ✅ |
| FR-3 | Query arXiv per technique | hybrid RAG: BM25 + local embedding + RRF + recency → ranked candidates | ✅ |
| FR-4 | Verify each candidate gap via sub-agent | APPROVED/REJECTED/UNCERTAIN; rejected never ship. 14 approved live | ✅ |
| FR-5 | Emit 4 artifacts | `TECHNIQUES.md` `PAPERS.md` `GAPS.md` `RELATED_WORK.md` written per run (`report.py`) | ✅ |
| FR-6 | Recover from tool failure | backoff+degrade on arXiv; harness revision loop on test failure; recovery spans traced | ✅ |
| FR-7 | BYOK LLM | OPENAI/GROQ/ANTHROPIC/LITELLM precedence; `ANTAR_MODEL` overrides | ✅ |
| FR-8 | Full tracing + cost | 1 root WORKFLOW trace per run; per-span tokens+cost; doctor probe PASS | ✅ |
| FR-9 | Owner-scoped writes | `repo_access.assert_can_write()` refuses non-owned repos (verified live) | ✅ |
| FR-10 | Open issue per verified gap | GitHub/GitLab issue; 25 opened on demo repo | ✅ |
| FR-11 | Code the fix + open PR | harness-learning loop → push → PR; PR #26 open | ✅ |
| FR-12 | MCP server | `scan_repo`/`find_gaps`/`search_papers`/`open_issues`/`fix_gap`; bearer auth + RBAC | ✅ |

## Non-functional

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-1 | Runtime on a small repo | < 5 min | ✅ (~2 min report mode) |
| NFR-2 | LLM cost per run (haiku) | < $0.05 | ✅ (measured via traces; see BUSINESS-PLAN) |
| NFR-3 | Citation precision | ≥95% (approved/claimed) | 🚧 (SOD gate active; formal audit = future) |
| NFR-4 | No source exfiltration | only query strings leave the machine | ✅ (arXiv queries only; embeddings local) |
| NFR-5 | Offline demo fallback | pre-cached run replays with no API | 🚧 (golden-run replay is a stub) |

## Evidence requirements (neatHack)

| ID | Evidence | Where it lives | Status |
|----|----------|----------------|--------|
| EV-1 | Agent improved: before/after traces w/ compared numbers | verifier fence-parse + gap-logic fix → 0→14 gaps (traces; hackathon.md) | ✅ |
| EV-2 | neatlogs used | workflow `antar-agent` traces; doctor probe trace read back | ✅ |
| EV-3 | Entire used | `entire enable` git hooks + `entire graph` (checkpoints accrue on agent-session commits) | ✅ |
| EV-4 | cfo.ai used | live plan via MCP — docs/BUSINESS-PLAN.md links | ✅ |
| EV-5 | Recovers from failure | harness revision loop + recovery spans (traces) | ✅ |
| EV-6 | Built in public | #neatHack posts (links in hackathon.md) | ✅ |
| EV-7 | Code written in window | public repo, 24 commits dated Oct 12 | ✅ |
