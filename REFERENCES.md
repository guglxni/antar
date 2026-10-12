# antar — References, Prior Art & Verified Repos

Every link verified live on 2026-10-12. Clone commands use `gh` (authenticated as @guglxni).

## Mandatory partner tooling (clone for reference / docs)

```bash
# Entire CLI — checkpoints + repo context (INSTALL FROM RELEASES, not source)
gh repo clone entireio/cli -- --depth 1            # https://github.com/entireio/cli
gh repo clone entireio/entire-graph -- --depth 1   # https://github.com/entireio/entire-graph

# LiteLLM — the OpenAI-compatible gateway the hackathon key fronts
gh repo clone BerriAI/litellm -- --depth 1         # https://github.com/BerriAI/litellm
```

> **Entire install (do NOT build from source):**
> ```bash
> gh release download --repo entireio/cli --pattern "entire_darwin_arm64.tar.gz" --clobber
> tar -xzf entire_darwin_arm64.tar.gz && install -m755 entire ~/.local/bin/entire
> entire --version   # 0.11.4
> entire enable --yes --agent claude-code   # in this repo
> ```

## Optional / reference

```bash
# Multi-agent orchestration patterns (judge Prateek Karnal's project — ideas only)
gh repo clone OrchestratorInc/agent-orchestrator -- --depth 1   # https://github.com/OrchestratorInc/agent-orchestrator

# MCP SDK — only if we build a cfo.ai MCP client ourselves
gh repo clone modelcontextprotocol/python-sdk -- --depth 1      # https://github.com/modelcontextprotocol/python-sdk

# Prior concept (design learnings + taxonomy source — NO code reused)
gh repo clone guglxni/SAGE-GitAgent -- --depth 1               # https://github.com/guglxni/SAGE-GitAgent
```

## APIs & services (no clone)

| Resource | URL | Use |
|---|---|---|
| arXiv API user manual | https://info.arxiv.org/help/api/user-manual.html | paper search (HTTP 200 verified) |
| neatlogs docs | https://docs.neatlogs.com/docs | tracing SDK + MCP |
| neatlogs wizard | `npx @neatlogs/wizard` | auto-instrument |
| Entire docs | https://docs.entire.io | CLI + checkpoints |
| cfo.ai docs | https://docs.cfo.ai | model + MCP |
| cfo.ai MCP | https://api.cfo.ai/mcp | business plan tools |
| cfo.ai agent-instructions | https://docs.cfo.ai/agent-instructions.md | agent setup prompt |
| Hackathon LiteLLM base | https://litellm.vision.aivar.app/v1 | model gateway |
| LiteLLM key | https://neatlogs.com/hackathon/models | after check-in |
| Web check-in | https://neatlogs.com/hackathon/check-in | gate for credits |
| Hackathon page | https://neatlogs.com/hackathon | rules |
| Build-companion skill | https://neatlogs.com/hackathon/skill | hackathon.md spec |

## Research grounding (the "inspired by" for MATH.md)

| Concept | Source |
|---|---|
| **Harness learning / test-time adaptation (§8)** | Zhang, Liu, Wang, Tajwar, Arora, Salakhutdinov, Khashabi, Song, Zanette 2026, *Harness Learning Enables Generalizable Test-Time Adaptation*, arXiv:2609.35738 |
| GRPO group-normalized advantage (§8) | Shao et al. 2024, *DeepSeekMath* |
| Meta-learning over programs (§8) | Finn et al. 2017 (MAML); Duan et al. 2016 (RL²) |
| Noisy-or evidence combination (§1) | Pearl 1988, *Probabilistic Reasoning in Intelligent Systems* |
| TF-IDF cosine similarity (§3) | Salton & Buckley 1988, *Term-weighting approaches in automatic text retrieval* |
| Exponential recency decay (§3) | standard time-decay relevance models |
| Verifier posterior precision (§4) | Bayes' theorem applied to a sensitivity/specificity gate |
| Retry reliability bound (§6) | $P=(1-(1-r)^m)^k$ — classic reliability engineering |
| Backoff w/ decorrelated jitter (§7) | AWS Architecture Blog, *Exponential Backoff And Jitter* |
| Segregation of Duties | standard control theory / security practice applied to agent outputs |
| Gap analysis grounding | retrieval-grounded generation (RAG) literature |

## Example target repos (for the demo run)

```bash
gh repo clone karpathy/minGPT -- --depth 1        # small, well-known, good fixture
gh repo clone karpathy/nanoGPT -- --depth 1       # alternate fixture
```
