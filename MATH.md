# antar — The Math Behind It

Numbers that drive the design: how we rank papers, how the verifier buys precision,
how we bound cost, and the unit economics that feed the cfo.ai plan.

---

## §1. Technique detection — confidence from AST evidence

Each detected technique gets a confidence from the strength of its AST matches.

For technique $t$ with matched evidence set $E_t$ (each $e \in E_t$ is a node match of
weight $w_e$ — direct `Call`=1.0, `Attribute`=0.6, `Name`=0.3):

$$
\text{conf}(t) = 1 - \prod_{e \in E_t} (1 - w_e)
$$

Multiple weak hints combine toward certainty; one strong call already ≈ 1.
A technique is reported if $\text{conf}(t) \ge \tau$ with $\tau = 0.5$.

*Rationale:* noisy-or — standard for combining independent weak evidence (Pearl 1988,
*Probabilistic Reasoning in Intelligent Systems*).

## §2. Query construction — expected hits

For technique $t$, build query terms from its canonical name + category synonyms
$S_t$. Query $q_t = \text{OR}(\text{terms})$. We cap `max_results = N` (default 8)
to bound downstream summarization cost linearly in $|T|$ techniques:

$$
\text{LLM calls}_{\text{hunt}} \le |T|,\qquad
\text{papers fetched} \le N \cdot |T|
$$

## §3. Paper relevance ranking

Score each candidate paper $p$ for technique $t$:

$$
\text{rel}(p,t) = \alpha \cdot \underbrace{\text{sim}(p.\text{title} \oplus p.\text{abstract},\, q_t)}_{\text{lexical overlap}}
+ \beta \cdot \underbrace{e^{-\lambda \, \Delta\text{days}}}_{\text{recency decay}}
$$

with $\alpha + \beta = 1$ (default $\alpha{=}0.7,\ \beta{=}0.3$), decay constant
$\lambda = \tfrac{\ln 2}{365}$ (half-life 1 year — "state of the art" moves fast).

Lexical overlap is TF-IDF cosine over term vectors (SageMaker-classic, no embeddings —
keeps it free + deterministic):

$$
\text{sim}(a,b) = \frac{a \cdot b}{\lVert a \rVert \, \lVert b \rVert}
$$

## §4. Verifier — precision vs recall trade

The SOD verifier is a gate that trades a little recall for a lot of precision.

Let the gap-identifier produce candidate gaps with base precision $p_0$ (fraction truly
valid). The verifier has sensitivity $s$ (true-positive rate) and specificity $c$
(true-negative rate). The **posterior precision** of an APPROVED gap is:

$$
P(\text{valid} \mid \text{APPROVED})
= \frac{s \, p_0}{s \, p_0 + (1 - c)(1 - p_0)}
$$

**Worked example.** $p_0 = 0.6$ (LLM proposes, 40% are shaky), verifier $s = 0.95$, $c = 0.9$:

$$
P(\text{valid}\mid\text{APPROVED}) = \frac{0.95 \cdot 0.6}{0.95\cdot 0.6 + 0.1 \cdot 0.4}
= \frac{0.57}{0.61} \approx 0.934
$$

Tuning $c \to 0.97$ (adversarial "try to disprove" prompt) lifts this to ≈0.98.
**This is why the verifier exists** — it's the mathematical difference between a
plausible-sounding report and a trustworthy one.

## §5. Cost & unit economics (feeds cfo.ai)

Per run, with $T$ techniques, $N$ papers/technique, $G$ candidate gaps:

$$
\text{cost} = \underbrace{T \cdot c_{\text{scan}}}_{\approx 0,\ \text{local AST}}
+ \underbrace{\sum_{\text{LLM calls}} (\text{tok}_{\text{in}} p_{\text{in}} + \text{tok}_{\text{out}} p_{\text{out}})}_{\text{from neatlogs traces}}
$$

LLM call count: $|T|$ (queries) $+ \sum N$ (summaries) $+ G$ (verify) $+ 1$ (compose).
Using **measured** token counts from neatlogs spans (not estimates) → cost/scan.

Gross margin for a pro tier at price $P$:

$$
\text{GM} = \frac{P - \text{cost}_{\text{scan}}}{P}
$$

Runway: $\text{runway} = \tfrac{\text{cash}}{\text{monthly net burn}}$ — modeled live in
cfo.ai with scenarios (base / growth / hiring). The loop: **neatlogs measures cost →
cfo.ai prices it.**

## §6. Reliability — probability a run completes

If each of $k$ tool calls succeeds independently with prob $r$, a naive pipeline
completes with $r^k$. With retry policy of $m$ attempts per call, per-call success rises to
$r' = 1 - (1-r)^m$, so pipeline success becomes:

$$
P_{\text{run}} = \bigl(1 - (1-r)^m\bigr)^k
$$

**Example.** $r = 0.9$, $k = 20$, $m = 3$: naive $0.9^{20} \approx 0.12$ (12%!).
With retries: $(1 - 0.1^3)^{20} = 0.999^{20} \approx 0.98$. **Retries are the difference
between a demo that fails live and one that doesn't.** This justifies the recovery loop.

## §8. Harness learning — test-time adaptation (arXiv:2609.35738)

The Coder's self-correction loop is the paper's inner meta-learning loop, used at inference
time (proposer & solver frozen). The adaptation objective over $T$ rounds:

$$
\max_{\theta}\ \mathbb{E}\bigl[ J(h_T; Q_{\text{eval}}) \bigr],
\qquad
J(h; Q) = \frac{1}{|Q|} \sum_{q \in Q} \text{score}(h, q)
$$

where $h_T$ is produced by the revision loop

$$
y_i \sim \pi_\theta(\cdot \mid x_t), \quad h'_i = \mathrm{Apply}(h_{t-1}, y_i), \quad
h_t = \mathrm{Select}\bigl(h_{t-1}, \{h'_i\}; Q_t^{\text{score}}\bigr).
$$

**antar's instantiation (inference-time only, no GRPO):** the input $x_t$ =
{fix_summary, current harness, execution report}; the proposer is the Coder (aider); the
grader is the Tester (`score = fraction of tests passing`, Eq. 3); **Select** retains a
revision iff `score` improves / passes. We sample $G{=}1$ candidate per round with a
revision budget $T \le 3$, and the execution report (paper App. E.2) — score + failing
traces + revision history — is fed back as $x_{t+1}$.

The paper's *training* contribution (GRPO with reward $r_i = J(h'_i; Q^{\text{score}}) + v_i$,
$v_i$ an edit-validity bonus, group-normalized advantage
$\hat{A}_i = (r_i - \bar r)/(\sigma_r + \delta)$) is **future work** for antar: it would let
the proposer learn a reusable revision policy across repos. We note this in LIMITATIONS and
cite it as the path to "continually learning agents."

## §7. arXiv politeness / rate limiting

Exponential backoff with jitter on transient failures, attempt $i$:

$$
\text{delay}_i = \min\!\bigl(\text{cap},\ b \cdot 2^{i}\bigr) + \text{Uniform}(0, j)
$$

base $b = 1$s, cap $= 30$s, jitter $j = 1$s (AWS "Architecture of the Internet"-style
decorrelated jitter). Honors `Retry-After` on 429.
