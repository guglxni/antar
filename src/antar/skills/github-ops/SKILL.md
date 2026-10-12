---
name: github-ops
description: Open issues and pull requests for verified gaps. Use after the Planner produces an issue spec or the Coder+Tester finish a fix. Requires GITHUB_TOKEN and explicit mode/allow flags.
---

# github-ops skill (GitHub agent)

Opens issues and PRs via PyGithub. Never runs in report-only mode.

- **Issues:** `create_issue(repo, title, body, labels)` — one per APPROVED gap.
  Body includes technique, paper id/title, claim, verifier note, and file:line evidence.
  On failure → back off, then fall back to appending to `ISSUES.md` locally.
- **PRs (opt-in, capped):** only with `--mode pr --allow-pr`. Creates/pushes a feature
  branch `antar/<technique>`, then `create_pull(base, head, ...)` referencing the issue.
- **Guardrails:** `GITHUB_TOKEN` required; `--max-prs` bounds cost/scope; dry-run default.

All calls are traced as neatlogs TOOL spans (url, number, status).
