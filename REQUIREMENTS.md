# antar — Requirements (numbered & testable)

Status: `✅ done` `🚧 in progress` `⬜ planned`. Each FR maps to a test in `tests/`.

## Functional

| ID | Requirement | Acceptance | Status |
|----|-------------|-----------|--------|
| FR-1 | Accept a local path or public git URL | clones to temp / reads in place; errors clearly on bad input | ⬜ |
| FR-2 | AST-scan `.py` files → technique inventory | returns technique + file:line for ≥90% of known taxonomy hits on a fixture repo | ⬜ |
| FR-3 | Query arXiv per technique | returns ranked candidates (id, title, abstract, date) with relevance score | ⬜ |
| FR-4 | Verify each candidate gap via sub-agent | verifier returns APPROVED/REJECTED/UNCERTAIN; rejected gaps never in GAPS.md | ⬜ |
| FR-5 | Emit 4 artifacts | `TECHNIQUES.md` `PAPERS.md` `GAPS.md` `RELATED_WORK.md` all written, non-empty | ⬜ |
| FR-6 | Recover from tool failure | injected arXiv 500 → backoff + degrade; run completes; recovery span present | ⬜ |
| FR-7 | BYOK LLM | runs on OPENAI/GROQ/ANTHROPIC/LITELLM key per precedence; `ANTAR_MODEL` overrides | ⬜ |
| FR-8 | Full tracing + cost | every run = 1 root WORKFLOW trace; per-span tokens+cost visible | ⬜ |

## Non-functional

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-1 | Runtime on a small repo | < 5 min end-to-end | ⬜ |
| NFR-2 | LLM cost per run (haiku) | < $0.05 | ⬜ |
| NFR-3 | Citation precision | ≥95% (approved/claimed) | ⬜ |
| NFR-4 | No source exfiltration | only query strings leave the machine | ⬜ |
| NFR-5 | Offline demo fallback | pre-cached run replays with no API | ⬜ |

## Evidence requirements (neatHack)

| ID | Evidence | Where it lives |
|----|----------|----------------|
| EV-1 | Agent improved: before/after traces w/ compared numbers | links in hackathon.md |
| EV-2 | neatlogs used | trace links / screenshots |
| EV-3 | Entire used | `entire checkpoint list` + `entire graph` output |
| EV-4 | cfo.ai used | business plan (pricing/cost/revenue/runway) |
| EV-5 | Recovers from failure | one trace showing failed action + recovery |
| EV-6 | Built in public | #neatHack post links |
| EV-7 | Code written in window | public repo, commits dated Oct 10–12 |
