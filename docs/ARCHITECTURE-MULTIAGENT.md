# antar — Multi-Agent Architecture (v2)

> Upgrade: from *reviewer/gap-reporter* → **autonomous research-to-PR agent**.
> antar now closes the full loop: **detect a gap → open an issue → write the fix →
> verify → open a PR.** It is also itself an **MCP server**, so other agents can call it.

## 1. Agent topology

<p align="center"><img src="diagrams/architecture.svg" alt="antar architecture" width="1000"/></p>

> **Research foundation.** antar's coder implements the test-time adaptation loop from
> *Harness Learning Enables Generalizable Test-Time Adaptation* (arXiv:2609.35738) — see §3a
> below and MATH.md §8. The agent improves by revising its **harness** from **execution
> feedback**, not by touching model weights.

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
              Planner → FixPlan (issue spec)      │
                    │                             │
              GitHub/GitLab.create_issue() ────────┘   (ISSUES MODE, owner-scoped)
                    │
              HarnessRevisionLoop (paper §4.2):
                x_t = {fix_summary, current harness, execution report}
                proposer (aider) applies a candidate fix
                Tester runs test_cmd → ExecutionReport (score, failing traces)
                if fail → report feeds the NEXT revision (≤ T rounds)
                    │ tests pass
              push branch → create_pull()/MR ──▶ PR referencing the issue  (PR MODE, owner-scoped)
```

State is checkpointed (Entire) after every stage; a crash resumes from the last stage.

### 3a. Harness learning (arXiv:2609.35738) — how antar applies it

The paper frames an agent as **model + harness** and shows you improve the agent by
**revising the harness from execution feedback**, not by touching model weights. antar
adopts the paper's *test-time inference loop* (we keep solver & proposer frozen — no RL):

- **Harness** = the fix applied to the target code by the Coder.
- **Proposer** = the Coder (aider), which reads `{task, current harness, execution report}`
  and emits a targeted revision.
- **Execution report** = the Tester's `ExecutionReport` (score, failing-output tail, exit
  code, revision history) — the paper's Appendix E.2 artifact.
- **Selection** = retain the revision iff the test score passes; else the report becomes
  the feedback for the next round (`_revision_prompt` includes the prior report).

This is the "self-improving / recovers-from-failure" evidence: a neatlogs trace showing
`rev 1: FAIL → diagnosis → rev 2: PASS`. We implement the **inference-time** loop only;
training the proposer with GRPO (paper §4.3) is future work, noted in LIMITATIONS.

<p align="center"><img src="diagrams/harness-loop.svg" alt="harness revision loop" width="820"/></p>

The verification / segregation-of-duties model:

<p align="center"><img src="diagrams/sod-verification.svg" alt="verification SOD" width="820"/></p>

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

## Guardrails: OWNER-SCOPED WRITES (hard boundary)

Issues/PRs/pushes are allowed **only** on repos the authenticated identity owns:
- **GitHub:** `repo.owner.login == authenticated_user.login` AND `permissions.push/admin/maintain`.
- **GitLab:** `access_level >= DEVELOPER` (30) from project/group membership.

`agents/repo_access.assert_can_write()` enforces this on **every** write and raises
`OwnershipError` otherwise. Verified live: a repo you don't own (e.g. `karpathy/minGPT`)
is refused. PR mode additionally requires `--mode pr --allow-pr` + `GITHUB_TOKEN` (or
`GITLAB_TOKEN`), a `--max-prs` cap, and dry-run by default.

## Modes & scope control

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
