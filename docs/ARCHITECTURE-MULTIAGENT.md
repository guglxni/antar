# antar — Multi-Agent Architecture (v2)

> Upgrade: from *reviewer/gap-reporter* → **autonomous research-to-PR agent**.
> antar now closes the full loop: **detect a gap → open an issue → write the fix →
> verify → open a PR.** It is also itself an **MCP server**, so other agents can call it.

## 1. Agent topology

```
                        ┌─────────────────────────────────────────┐
                        │           ORCHESTRATOR (coordinator)     │
                        │   plan → dispatch → settle → report      │
                        │   root neatlogs WORKFLOW span            │
                        │   Entire RunState checkpoint per stage   │
                        └───────┬───────────────┬─────────────────┘
                                │               │                 
        ┌───────────────────────┘               └───────────────────────────┐
        │ worker pool (specialised sub-agents, each a neatlogs AGENT span)  │
        │                                                                   │
 ┌──────▼──────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐
 │  Scanner    │  │ Research │  │ Verifier │  │ Planner │  │  Coder       │
 │  (AST/graph)│→ │  (arXiv) │→ │ (SOD     │→ │ (issue  │→ │  (aider      │
 │             │  │          │  │  gate)   │  │  draft) │  │  embedded)   │
 └─────────────┘  └──────────┘  └──────────┘  └────┬────┘  └──────┬───────┘
                                                    │             │
                                              ┌─────▼─────┐ ┌─────▼──────┐
                                              │ GitHub    │ │  Tester    │
                                              │ (issue/PR │ │  (run tests│
                                              │  PyGithub)│ │  /lint)    │
                                              └───────────┘ └─────┬──────┘
                                                                  │ pass
                                                            ┌─────▼──────┐
                                                            │ GitHub PR  │
                                                            └────────────┘
```

Each worker is an independent agent with a narrow mandate, its own neatlogs `AGENT`
span, and its own Entire-attached reasoning. The orchestrator never writes code or
papers itself — it decomposes, dispatches, settles disagreements, and composes the report.

## 2. The agents (roles & skills)

| Agent | Mandate | Tools | Skill equipped | Output |
|---|---|---|---|---|
| **Orchestrator** | decompose goal, dispatch, settle, compose | state store, message bus | `agent-orchestrator` pattern | run plan, final report |
| **Scanner** | map the codebase, extract techniques | stdlib `ast`, **graphify** / `entire graph` | **graphify** (code→knowledge graph) | technique inventory + code map |
| **Researcher** | find SOTA papers per technique | arXiv API | literature-ranking (MATH §3) | ranked papers w/ abstracts |
| **Verifier** | **disprove** each claimed gap (SOD) | arXiv fetch + code evidence | adversarial-verification | APPROVED/REJECTED/UNCERTAIN |
| **Planner** | turn an approved gap into an actionable issue spec | repo map + gap | issue-spec writing | issue draft (title/body/acceptance) |
| **Coder** | implement the fix on a branch | **aider** (`Coder`) | **graphify** for context + code-editing | commits on a feature branch |
| **Tester** | validate the change | pytest/lint via aider `--test-cmd` | test-authoring | pass/fail + logs |
| **GitHub** | open the issue, open the PR | **PyGithub** | github-ops | issue #, PR # |

**Segregation of duties:** Verifier never shares a context window with Researcher; Coder
never approves its own work — Tester does. This is the trust model.

## 3. The end-to-end loop (issue → PR)

```
scan ─▶ research ─▶ verify ─▶ [approved gaps]
                                   │
                    ┌──────────────┴──────────────┐
                    ▼ for each approved gap        │
              Planner → issue spec                │
                    │                             │
              GitHub.create_issue()  ─────────────┘   (ISSUES MODE)
                    │
              Coder (aider on a new branch, equipped w/ graphify code map)
                    │
              Tester (pytest --test-cmd; on fail → back to Coder w/ error, ≤N loops)
                    │ pass
              GitHub.create_pull()  ──▶ PR referencing the issue   (PR MODE)
```

State is checkpointed (Entire) after every stage; a crash resumes from the last stage.

## 4. antar AS an MCP server

Expose the whole pipeline as tools other agents can call (fastmcp):

| MCP tool | Args | Returns |
|---|---|---|
| `scan_repo` | `repo` | technique inventory (JSON) |
| `find_gaps` | `repo` | verified gap list |
| `open_issues` | `repo`, `gaps[]` | issue URLs |
| `fix_gap` | `repo`, `gap_id` | branch + PR URL |
| `get_trace` | `run_id` | neatlogs trace summary |

Run: `python -m antar.mcp_server` → serves over stdio/SSE. This makes antar composable —
another orchestrator (or Claude Code) can drive it. **Open-sourceable** as-is (MIT).

## 5. Equipping agents with skills (graphify et al.)

- **graphify** — Scanner + Coder run `graphify query "<concept>"` /
  `graphify path "<A>" "<B>"` against the target repo to get a scoped subgraph instead of
  grep-and-read. (graphify-out/ on the *target* repo, generated on demand, AST-only, no API cost.)
- **entire graph** — used on *antar's own* repo during development for repo-context evidence.
- Skill manifests live under `src/antar/skills/*/SKILL.md` so each agent's capabilities are
  declarative and swappable.

## 6. Failure & recovery (multi-agent)

- Coder test failure → loop back to Coder with the error (max 3), then mark gap `FAILED`.
- aider crash / nonzero exit → restore Entire RunState, retry once, else skip gap.
- GitHub API error → backoff; if issue creation fails, fall back to writing `ISSUES.md`.
- Every recovery = a neatlogs span → the "agent recovers from failures" evidence.

## 7. Tracing & evidence (all mandatory tools)

- **neatlogs:** orchestrator root `WORKFLOW`; each agent an `AGENT` span; tool calls
  `TOOL`/`RETRIEVER`; aider's LLM calls traced via the wrapped client.
- **Entire:** `entire enable` on antar's repo (done); each commit a checkpoint.
- **cfo.ai:** unit cost now includes *issue + PR authoring* tokens, not just scan.

## 8. Modes & scope control

| Mode | Flag | Behaviour |
|---|---|---|
| Report only | `--mode report` | scan→research→verify→GAPS.md (original) |
| Issues | `--mode issues` | + Planner + `GitHub.create_issue` per approved gap |
| PRs | `--mode pr` | full loop incl. Coder + Tester + `create_pull` |
| Offline | `--offline` | replay cached golden run (demo insurance) |

Guardrails: PR mode requires `--allow-pr` + a `GITHUB_TOKEN`; dry-run default on.
Max gaps→PRs capped (`--max-prs`) to bound cost/time.

## 9. New directory additions

```
src/antar/
├── orchestrator.py        # coordinator (root WORKFLOW)
├── agents/
│   ├── scanner.py         # AST + graphify
│   ├── researcher.py      # arXiv
│   ├── verifier.py        # SOD gate
│   ├── planner.py         # issue spec
│   ├── coder.py           # aider wrapper
│   ├── tester.py          # pytest/lint
│   └── github_ops.py      # PyGithub issue/PR
├── mcp_server.py          # fastmcp exposure of the pipeline
├── skills/
│   ├── graphify/SKILL.md
│   ├── adversarial-verification/SKILL.md
│   └── github-ops/SKILL.md
├── state.py               # RunState + Entire checkpoint save/restore
└── llm.py                 # BYOK client (shared by all LLM agents)
```
