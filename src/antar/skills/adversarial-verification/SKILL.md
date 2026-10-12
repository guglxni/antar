---
name: adversarial-verification
description: Disprove a claimed code/literature gap before it ships. Use to gate any finding that cites an external source. Returns APPROVED / REJECTED / UNCERTAIN with a one-line reason.
---

# adversarial-verification skill (Verifier)

Segregation of duties: the agent that *proposes* a gap never *confirms* it.

1. Take the claim + cited paper id + abstract + code evidence.
2. Resolve the paper id (does it exist? does the abstract support the claim?).
3. Check the code evidence — is the technique genuinely absent/misused at the cited lines?
4. Verdict:
   - APPROVED — abstract supports the claim AND technique plausibly absent.
   - REJECTED — wrong paper id, unsupported claim, or technique clearly present.
   - UNCERTAIN — insufficient evidence either way.

Precision model: see MATH.md §4 (posterior precision of an APPROVED gap).
Rejected gaps are logged and excluded — "overturned, not hidden."
