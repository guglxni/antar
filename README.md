<div align="center">

# antar

### अन्तर — *the gap*

**An autonomous agent that finds the verified gap between your ML code and the current literature.**

Point it at a repo → it reads your code, hunts arXiv, **independently verifies** every finding,
recovers from its own failures, and hands you a ranked, evidence-backed gap report.

`MIT` · `Python 3.11` · `neatlogs` · `Entire` · `cfo.ai` · **neatHack 2026**

</div>

---

## What it does

```
TECHNIQUES.md   ← what your code is doing right now (AST, file:line evidence)
PAPERS.md       ← what the literature says about those techniques (arXiv)
GAPS.md         ← 🔴 critical · 🟡 improvement · 🟢 experimental — VERIFIED
RELATED_WORK.md ← LaTeX-ready bibliography
```

Every gap is gated by an independent **verifier sub-agent** (segregation of duties) that
tries to *disprove* the claim before it ships. Unverifiable ⇒ marked `UNCERTAIN`, not hidden.

## Why it's different

- **Code-grounded** — not another abstract summarizer; it starts from *your* AST.
- **Verified** — a second agent cross-checks each citation against the abstract + code evidence.
- **Observable** — every LLM/tool call traced with neatlogs; you watch the agent think.
- **Recoverable** — tool failures trigger retry/fallback/degrade, never a silent abort.
- **Auditable** — full development history checkpointed with Entire.

## Quick start

```bash
# 1. clone + env
git clone https://github.com/guglxni/antar.git && cd antar
uv venv && source .venv/bin/activate && uv pip install -e .
cp .env.example .env        # fill NEATLOGS_API_KEY + one LLM key (BYOK)

# 2. run against any ML repo (traced, recovered, verified)
python -m antar run /path/to/your-ml-project

# 3. offline demo (no API — pre-cached golden run)
python -m antar run --offline
```

See **docs/setup.md** for the full tool setup (neatlogs / Entire / cfo.ai / LiteLLM BYOK).

## The stack (neatHack mandatory trio)

| Tool | Role in antar |
|---|---|
| **neatlogs** | Traces every span → failure→fix + recovery evidence; token/cost per run |
| **Entire** | Git hooks checkpoint every commit; `entire graph` maps the repo |
| **cfo.ai** | Turns the agent's *own traced token costs* into its pricing/runway plan |

## Docs

`PRD.md` · `ARCHITECTURE.md` · `DESIGN.md` · `REQUIREMENTS.md` · `PLAN.md` ·
`PROPOSAL.md` · `MATH.md` · `REFERENCES.md` · `SKILL.md` · `hackathon.md`

## Disclosure

A from-scratch v2 of an earlier concept ([SAGE-GitAgent](https://github.com/guglxni/SAGE-GitAgent)).
No code carried over — only design learnings. All code here was written within the neatHack window.

## License

MIT © 2026 Aaryan Guglani
