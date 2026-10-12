# antar — Product Requirements Document

> **Product:** `antar` (Sanskrit अन्तर — *gap / difference*)
> **One-liner:** An autonomous agent that finds the gap between what an ML codebase does and what the current literature says it *should* do — then proves each finding with evidence.
> **Event:** neatHack (neatlogs) · Oct 10–12 2026 · track: "Build an agent that works (literally)"
> **Repo:** https://github.com/guglxni/antar · **Author:** Aaryan Guglani (@guglxni)

---

## 1. Problem

ML engineers ship models but rarely survey the literature systematically. Consequences:

- Using SGD when AdamW + warmup is standard.
- Missing gradient clipping → training instability they're debugging blind.
- A 3-month-old paper solves exactly their bottleneck.
- Hours on arXiv when the search could be grounded in their *actual code*.

Existing "paper summarizers" are detached from the user's codebase. Existing code analyzers ignore the literature. Nobody closes the loop with **verification** and **evidence**.

## 2. Solution

Point `antar` at any ML repository. It:

1. **Scans** the codebase (AST) → extracts the techniques actually in use.
2. **Hunts** arXiv for the state of the art on each technique.
3. **Verifies** every candidate finding with an independent sub-agent (segregation of duties) — kills hallucinated paper IDs before they ship.
4. **Reports** a ranked, evidence-backed gap analysis (`GAPS.md`) + a LaTeX-ready `RELATED_WORK.md`.

It **recovers from tool failures** mid-run (retry → fallback → degraded-mode), and every step is **traced** so a human can audit exactly what the agent saw and decided.

## 3. Goals / Non-goals

**Goals**
- End-to-end autonomous run on a real repo in < 5 minutes.
- Zero hallucinated citations (verifier gate).
- Observable: every LLM/tool call traced (neatlogs).
- Recoverable: a tool failure never silently aborts the run.
- Auditable: full development history checkpointed (Entire).
- Viable: unit-economics business plan (cfo.ai).

**Non-goals** (deliberate)
- Does **not** modify the target source code (advisory only).
- Does **not** parse full paper PDFs (abstracts are sufficient for gap analysis).
- Does **not** send the user's source to third parties (only derived query strings).
- Not a general coding assistant; not a paper *writing* tool.

## 4. Users & Use cases

| Persona | Use case |
|---|---|
| ML engineer | "Am I missing a standard technique?" before a training run |
| Researcher | Bootstrap a Related Work section with verified citations |
| Team lead | Drift check on a legacy model repo before a rebuild |
| Student | Learn SOTA for a technique grounded in working code |

## 5. Functional requirements

See **REQUIREMENTS.md** for the numbered, testable list. Summary:

- **FR-1** Ingest a local path or git URL.
- **FR-2** AST-scan Python (`.py`) → technique inventory w/ file:line evidence.
- **FR-3** Query arXiv per technique; rank by relevance + recency.
- **FR-4** Independent verification sub-agent confirms each gap (SOD).
- **FR-5** Emit `TECHNIQUES.md`, `PAPERS.md`, `GAPS.md`, `RELATED_WORK.md`.
- **FR-6** Retry/fallback on tool failure; log the recovery as a trace.
- **FR-7** BYOK LLM (OpenAI / Groq / Anthropic / hackathon LiteLLM).
- **FR-8** Full tracing; token + cost capture per run.

## 6. Success metrics (the judging rubric, internalized)

| Axis (weight) | How antar scores |
|---|---|
| The agent (30%) | Completes a substantial task end-to-end; plan→act→verify→recover loop |
| Partner tools (25%) | neatlogs traces, Entire checkpoints + `entire graph`, cfo.ai business plan — each with evidence |
| Demo video (20%) | ≤3 min, explicitly covers all three tools |
| Build in public (15%) | #neatHack posts during the build |
| Usefulness/originality (10%) | Real problem, code-grounded (not another paper summarizer) |

**KPIs:** ≥95% citation precision (verifier-approved / total claimed) · 0 silent aborts on injected failure · < $0.05 LLM cost per full run (haiku) · 100% of runs traced.

## 7. Constraints

- **Time:** ~8 build hours remaining; demo-first scope.
- **Budget:** $20 LiteLLM shared key → default `claude-haiku`, BYOK for heavier.
- **Code window:** all code written Oct 10–12 (this repo is fresh; see DISCLOSURE).
- **No Bedrock** in hackathon AWS; models come via LiteLLM.

## 8. Disclosure

`antar` is a from-scratch v2 rethink of an earlier prototype concept
([SAGE-GitAgent](https://github.com/guglxni/SAGE-GitAgent), built for a prior,
unrelated hackathon). **No code was carried over.** Reused: design learnings, the
ML-technique taxonomy, and output-calibration examples. All code here is new,
written within the neatHack window, and checkpointed with Entire.

## 9. Open questions / Risks

- arXiv rate limits on large repos → mitigate w/ batching + backoff (see MATH.md).
- LLM summarization drift → mitigate w/ verifier + citation cross-check.
- $20 budget exhaustion → default haiku; pre-cache a demo run (offline fallback for demo).
