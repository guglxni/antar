# antar — Design Document

## 1. Design principles

1. **Evidence over eloquence.** Every claim in `GAPS.md` carries a verifiable paper ID
   and a code location. If it can't be verified, it ships as `UNCERTAIN`, not hidden.
2. **Advisory, never destructive.** antar reads code; it never edits the target repo.
3. **The loop is the product.** plan→act→verify→recover→iterate is the explicit runtime,
   not an emergent property.
4. **Observability is a feature, not a debug tool.** Traces are user-facing output.
5. **Cheap by default, BYOK by choice.** haiku default; bring any key.

## 2. Data model

```python
@dataclass
class Technique:        # one detected technique
    name: str           # e.g. "adamw", "cosine_annealing", "gradient_clipping"
    category: str       # optimizer | scheduler | regularizer | architecture | ...
    evidence: list[str] # ["trainer.py:58", ...]
    confidence: float   # 0..1 from AST heuristic

@dataclass
class Paper:            # one arXiv candidate
    arxiv_id: str       # "2310.01848"
    title: str
    abstract: str
    published: date
    relevance: float    # see MATH.md §3

@dataclass
class Gap:              # a claimed gap (pre-verification)
    technique: str
    paper: Paper
    severity: str       # critical | improvement | experimental
    claim: str          # what's missing & why it matters
    verdict: str = ""   # APPROVED | REJECTED | UNCERTAIN  (set by verifier)
    reason: str = ""
```

## 3. Stage contracts

### scan (AST)
- Parse each `.py` with `ast.parse`. Walk the tree.
- Match against `knowledge/ml-techniques-taxonomy.md` patterns:
  - `Call` nodes: `torch.optim.AdamW`, `SGD`, `clip_grad_norm_`, ...
  - `Attribute`/`Name` heuristics for schedulers, mixed precision, etc.
- Emit `Technique` list w/ evidence. Confidence from match strength.

### hunt (arXiv)
- Build queries from technique names + category terms.
- `https://export.arxiv.org/api/query?search_query=...&max_results=N&sortBy=relevance`
- Parse Atom; rank by relevance score (MATH.md §3). Batch + backoff.

### verify (SOD sub-agent)
- One LLM call per candidate `Gap`. Prompt includes claim + abstract + code evidence.
- Strict output schema → verdict + reason. Rejected ⇒ excluded.

### report
- Render markdown deterministically from approved data. LaTeX `\cite`-ready bib.

## 4. State & checkpointing

```python
@dataclass
class RunState:
    repo: str
    techniques: list[Technique]
    papers: dict[str, list[Paper]]
    gaps: list[Gap]
    stage: str            # pipeline cursor for resume
    tokens_used: int
    cost_usd: float
```
`state.save()` / `state.load()` after every stage → resume mid-pipeline on failure.
Entire captures the *development* history; `RunState` captures the *run* history.

## 5. BYOK LLM client (llm.py)

Precedence: `OPENAI_API_KEY` → `GROQ_API_KEY` → `ANTHROPIC_API_KEY` → LiteLLM
(`LITELLM_API_KEY`, base `https://litellm.vision.aivar.app/v1`). One OpenAI-compatible
client; `neatlogs.wrap()` traces all uniformly. `ANTAR_MODEL` overrides the model.

## 6. Error taxonomy → recovery (see ARCHITECTURE.md §5)

`ToolError{kind: transient|rate_limit|parse|empty}` → policy:
transient→backoff×3; rate_limit→honor Retry-After; parse→skip+continue; empty→re-prompt×2→UNCERTAIN.

## 7. Prompts

- **Summarize:** engineering summary + minimal code sketch. Constrained to abstract facts.
- **Gap-identify:** given techniques + verified papers, propose gaps w/ severity + claim.
- **Verify:** adversarial — "try to disprove this gap." APPROVED only if it survives.

## 8. Output format

`GAPS.md`:
```
### 🔴 Missing Gradient Clipping
Paper: [2310.01848] Gradient Clipping Revisited
File:  trainer.py:78-95
Impact: instability on long sequences without clip_grad_norm_
Fix:    2 lines before optimizer.step() — Low complexity
Verdict: APPROVED (verifier: abstract confirms claim; technique absent at cited lines)
```
