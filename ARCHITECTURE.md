# antar — System Architecture

## 1. High-level

```
                 ┌────────────────────────────────────────────────────┐
                 │                    antar agent                      │
                 │  plan → act → verify → (recover) → report           │
                 └────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼───────────────────────────┐
        │                          │                           │
   ┌────▼─────┐             ┌──────▼──────┐            ┌───────▼───────┐
   │  scan    │             │    hunt     │            │    verify     │
   │ codebase │             │   papers    │            │  (SOD gate)   │
   │  (AST)   │             │  (arXiv)    │            │  sub-agent    │
   └────┬─────┘             └──────┬──────┘            └───────┬───────┘
        │ TECHNIQUES.md            │ PAPERS.md                 │ approved
        │                          │                           │ gaps only
        └──────────────┬───────────┴───────────────┬───────────┘
                       │                           │
                 ┌─────▼──────┐             ┌──────▼───────┐
                 │  identify  │             │    report    │
                 │   gaps     │────────────▶│   GAPS.md    │
                 └────────────┘             │ RELATED_WORK │
                                            └──────────────┘

  Cross-cutting (every box): neatlogs tracing · Entire checkpoints · state store
```

## 2. Pipeline stages

| # | Stage | Input | Tool | Output | Span kind |
|---|-------|-------|------|--------|-----------|
| 1 | `scan` | repo path/URL | `ast_scan` (stdlib `ast`) | `TECHNIQUES.md` | `TOOL` |
| 2 | `hunt` | techniques | `arxiv_search` (Atom API) | `PAPERS.md` | `RETRIEVER` |
| 3 | `verify` | candidate gaps | `verify_subagent` (LLM) | approved/rejected | `AGENT` |
| 4 | `identify_gaps` | techniques × verified papers | LLM | ranked gaps | `LLM` |
| 5 | `report` | all artifacts | writer | `GAPS.md`, `RELATED_WORK.md` | `CHAIN` |

The **orchestrator** is the root `WORKFLOW` span. Each stage is a child span, so the
neatlogs dashboard shows the full tree with per-span tokens, cost, and latency.

## 3. The agent loop (maps to the rubric's 8 axes)

```
goal = "close the code↔literature gap for <repo>"
state = load_checkpoint()            # Entire: resume across retries   [STATE]
plan  = decompose(goal)              # ordered stage list              [PLANNING]
for step in plan:
    ctx   = select_relevant(state)   # leave out the rest              [CONTEXT]
    try:
        out = call_tool(step, ctx)   # choose tool, supply inputs      [TOOL USE]
        ok  = verify(out)            # is the result correct?          [VERIFICATION]
    except ToolError as e:
        out = recover(e, step)       # retry / fallback / degrade      [RECOVERY]
    state = update(state, out)       # retain across steps & failures  [STATE]
    save_checkpoint(state)           # Entire
report = compose(state)              # each result guides next step    [ITERATION]
keep_running_until_done()            # long task to completion         [EXECUTION]
```

## 4. Segregation of Duties (verification)

Critical gaps never reach `GAPS.md` unverified. The **verifier sub-agent** is a
separate LLM call with a narrow mandate:

- Input: a claimed gap + the paper ID + the code evidence (file:line).
- Check: does the paper ID resolve on arXiv? Does the abstract actually support
  the claim? Is the technique genuinely absent from the code evidence?
- Output: `APPROVED | REJECTED | UNCERTAIN` + reason.

This is the "prove each claim" mechanism and the answer to the rubric's
**Verification** axis. See MATH.md §4 for the precision model.

## 5. Failure & recovery model

| Failure | Detection | Recovery |
|---|---|---|
| arXiv timeout / 5xx | HTTP status / latency span | exponential backoff (≤3), then cached results, then degrade stage |
| Malformed Atom XML | parse error span | skip entry, count, continue; never abort run |
| LLM empty/garbage | verifier rejects | re-prompt w/ tighter schema (≤2), else mark UNCERTAIN |
| Rate limit (429) | status span | honor `Retry-After`, queue remaining queries |
| Checkpoint conflict | Entire status | restore last good checkpoint, replay from there |

Every recovery is itself a traced span → the "agent recovers from failures"
evidence is literally a trace showing a failed action and what the agent did next.

## 6. Tracing architecture (neatlogs)

```python
import os, neatlogs
from openai import OpenAI
neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="antar-agent")
client = neatlogs.wrap(OpenAI(...))          # LLM spans automatic

@neatlogs.span(kind="TOOL", name="arxiv_search")
def arxiv_search(q): ...

with neatlogs.trace("antar-run", kind="WORKFLOW"):   # root span
    run_pipeline()
```

- Root = `WORKFLOW`; stages nest under it.
- LLM spans capture the exact prompt/response + token breakdown + cost.
- `span.set_attribute("neatlogs.tool.name", ...)` on tool spans.
- Failure→fix evidence = two traces (before/after) with compared numbers.

## 7. Repository context & history (Entire)

- `entire enable` installs git hooks; **every commit → a checkpoint** with an
  `Entire-Checkpoint:` trailer (context, decisions, changed files).
- `entire graph` builds a local tree-sitter map: `entire graph search`,
  `entire graph impact --symbol X`, `entire graph diff` — used during dev to
  locate code and reason about changes; its output is judging evidence.
- 100% local, no egress — safe to run inside the agent loop.

## 8. Business model (cfo.ai)

The agent's own **neatlogs token/cost data feeds the cfo.ai unit economics**:
cost-per-scan (tokens × model price) → gross margin → pricing tiers → runway.
Built via the cfo.ai MCP server (`https://api.cfo.ai/mcp`). See MATH.md §5 for
the pricing/cost model and cfo.ai for the live plan.

## 9. Component / directory map (actual)

```
antar/
├── PRD.md  ARCHITECTURE.md  DESIGN.md  REQUIREMENTS.md  PLAN.md  PROPOSAL.md
├── AGENTS.md  CLAUDE.md  SKILL.md  MATH.md  REFERENCES.md  hackathon.md
├── docs/                         # setup.md · OPERATIONS.md · BUSINESS-PLAN.md ·
│                                 #   ARCHITECTURE-MULTIAGENT.md · diagrams/
├── .env.example                  # BYOK + keys template (never the real .env)
├── Dockerfile  .github/workflows/ci.yml  .pre-commit-config.yaml
├── scripts/                      # load-env.sh (terminal secret loader) · deploy-aws.sh
├── demo/                         # HyperFrames demo composition → examples/antar-demo.mp4
├── src/antar/
│   ├── __init__.py  __main__.py  # CLI entry: `python -m antar run …` / `mcp`
│   ├── llm.py                    # BYOK client factory (OpenAI/Groq/Anthropic/LiteLLM)
│   ├── orchestrator.py           # plan→act→verify→recover loop (root WORKFLOW)
│   ├── state.py                  # RunState + checkpoint save/restore (resume)
│   ├── report.py                 # writes TECHNIQUES/PAPERS/GAPS/RELATED_WORK.md
│   ├── webapp.py                 # FastAPI app (security headers, CORS, bearer auth)
│   ├── mcp_server.py             # fastmcp server (TokenVerifier auth + write-gate RBAC)
│   ├── tools/
│   │   ├── ast_scan.py           # technique extractor (stdlib ast) + graphify enrich
│   │   ├── arxiv_search.py       # arXiv Atom API w/ backoff + jitter
│   │   ├── rag.py                # hybrid BM25 + local-embedding + RRF + recency
│   │   ├── graphify_integration.py  # auto-build + query target repo's knowledge graph
│   │   └── repo_intake.py        # clone GitHub/GitLab → local workspace
│   ├── agents/
│   │   ├── verifier.py           # SOD verification sub-agent (adversarial)
│   │   ├── planner.py            # gap → issue/fix spec
│   │   ├── harness.py            # harness-learning revision loop (aider Coder)
│   │   ├── tester.py             # run tests → ExecutionReport (feedback artifact)
│   │   ├── github_ops.py         # PyGithub/python-gitlab issue/PR/MR (owner-scoped)
│   │   └── repo_access.py        # ownership guard — assert_can_write() on every write
│   └── skills/                   # graphify · adversarial-verification · github-ops
└── tests/                        # smoke · harness · rag · repo_access · graphify (21 tests)
```

## 10. Deployment / runtime

- **Primary:** traced CLI (`python -m antar run <repo>`) with Rich console output —
  most credible to judges, zero deploy risk.
- **Webapp:** FastAPI (`uvicorn antar.webapp:app`) — security headers, CORS, bearer auth.
- **Demo insurance:** the rendered demo video committed under `examples/` so the
  3-minute submission never depends on a live API.
