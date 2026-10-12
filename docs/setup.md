# antar — integration setup

`antar` (Sanskrit अन्तर: *gap / difference*) — an agent that finds the gap between
an ML codebase and the current literature. neatHack submission. Uses **neatlogs**
(tracing), **Entire** (repo context + checkpoints), **cfo.ai** (business plan).

This file is the one-time setup for the three mandatory tools. Do them in order.

---

## 0. Prerequisites

```bash
# web check-in first — gates the LiteLLM key & AWS
open https://neatlogs.com/hackathon/check-in

# env
cp .env.example .env   # then fill in values below
```

## 1. neatlogs — tracing (Python SDK + MCP)

**SDK (already in this venv):** `neatlogs` is installed. Instrument once:

```python
import os, neatlogs
from openai import OpenAI

neatlogs.init(
    api_key=os.environ["NEATLOGS_API_KEY"],   # from neatlogs dashboard
    workflow_name=os.getenv("NEATLOGS_WORKFLOW", "antar-agent"),
)
client = neatlogs.wrap(OpenAI(...))            # every LLM call is now traced
```

Get `NEATLOGS_API_KEY` from your neatlogs dashboard → put in `.env`.
Or auto-instrument the whole project: `npx @neatlogs/wizard`.

**MCP (let your coding agent query its own traces):** server per
https://docs.neatlogs.com/integrations/mcp — add via your client's MCP settings.

## 2. Entire — repo context + checkpoints (CLI)

Binary installed to `~/.local/bin/entire` (v0.11.4, darwin/arm64).

```bash
# from this repo root — installs git hooks, captures every commit as a checkpoint
entire enable --yes --agent claude-code

# verify
entire status
entire checkpoint list

# semantic repo map (local, no network)
entire graph search "arxiv paper fetch"
entire graph impact --symbol <name>
```

Evidence for judges: `entire checkpoint list` output + `entire graph` snapshots.

## 3. cfo.ai — business plan (MCP)

**Account:** sign up at https://app.cfo.ai → **immediately cancel** in
Settings → Billing (won't be billed). neatHack team applies credits.

**Connect MCP** (Claude Code):
```bash
claude mcp add --transport http cfoai https://api.cfo.ai/mcp
# then: claude → /mcp → select cfoai → Authenticate (browser)
```

Then an agent can call `inspect_*` / `edit_*` tools to build the pricing /
cost / revenue / runway model. See https://docs.cfo.ai/agent-instructions.md.

## 4. LLM backend — LiteLLM BYOK

Precedence (first set wins): `OPENAI_API_KEY` → `GROQ_API_KEY` → `ANTHROPIC_API_KEY`
→ hackathon **LiteLLM** key (`LITELLM_API_KEY`, base `https://litellm.vision.aivar.app/v1`).
Override model for any backend with `ANTAR_MODEL`. Get the shared hackathon key at
https://neatlogs.com/hackathon/models after web check-in.
