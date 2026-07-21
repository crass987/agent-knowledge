# LLM-as-judge — bias catalogue and the default mitigation set

When code-based or human grading is impossible, an LLM judge is the last resort.
It is **systematically biased** (Zheng et al., NeurIPS 2023, arXiv:2306.05685;
Panickssery et al., NeurIPS 2024, arXiv:2404.13076). The mitigations below are
mandatory, not optional, whenever Phase 2/3 of the audit uses one.

## The biases

### Position bias
Pairwise comparison without swapping the answer order is inconsistent: GPT-4
holds the same verdict only **65%** of the time across orderings; Claude-v1
**23.8%**. The effect vanishes when models differ greatly in quality and is
almost absent on math/coding — it bites most exactly where the audit cares
(tight calls).

### Verbosity bias
A "repetitive list" attack fails Claude-v1 / GPT-3.5 in **91.3%** of cases; the
longer, more verbose answer wins regardless of correctness. GPT-4 resists
better (8.7% failure).

### Self-preference
Panickssery et al. (arXiv:2404.13076): "LLM Evaluators Recognize and Favor Their
Own Generations." Linear correlation between self-recognition and
self-preference. The mechanism is perplexity (Wataoka et al., arXiv:2410.21819):
models prefer text that is statistically "familiar," even when it is not their
own output. A judge from the same family as the component's model is suspect.

### Anchoring on the answer being graded
On math, GPT-4 judging LLaMA-vs-Vicuna fails 14/20 by default, dropping to 6/20
with CoT and 3/20 with a reference answer. The judge catches the answer's error
and is anchored by it.

### Honest agreement ceiling
GPT-4 vs human agreement ≈ **85%**, human-vs-human ≈ 81%. On close-quality
("tight") responses, agreement falls to **~70%**. The judge is least reliable
exactly where the audit needs it most: distinguishing a real but small
improvement from noise.

## Default mitigation set (apply all that fit)

1. **Position-swapping** — pairwise verdict counts only if the same answer wins
   in both orderings.
2. **Reference-guided judging** — supply a gold/reference answer; the most
   powerful single mitigation for reasoning tasks (14/20 → 3/20 math failures).
3. **Chain-of-thought before the grade** — require the judge to reason, then
   emit the score (OpenAI `cot_classify`; Anthropic recommendation).
4. **Cross-model judge** — use a judge from a different model family than the
   component's model, to dodge self-preference.
5. **Few-shot calibration** — show the judge labelled examples spanning the
   quality range.
6. **Multi-judge consensus + human calibration** — disagreement between judges is
   itself a signal to escalate to a human.

## Where a judge verdict is not allowed

In a high-cost-of-failure domain (critical infrastructure, compliance), a
**silent-quadrant probe with only a weak oracle** is not verdicted by a judge —
only by ground-truth or a human. Tag such audit cells "judge-not-trusted" and
surface them to a human reviewer. This is a structural limit, not a style
preference: the judge agrees with humans ~85% overall but ~70% on tight calls,
so a Δ of a few percent is inside its noise.

## Catalogue

Ye et al. (ICLR 2025, arXiv:2410.02736) catalogues 12 judge-bias types; the four
above are the ones that most distort a capability audit.

## Citations

- arXiv:2306.05685 — Zheng et al., MT-Bench / Chatbot Arena (NeurIPS 2023).
  Position, verbosity, self-enhancement bias; mitigations.
- arXiv:2404.13076 — Panickssery et al., self-preference (NeurIPS 2024).
- arXiv:2410.21819 — Wataoka et al., self-preference = perplexity.
- arXiv:2410.02736 — Ye et al., 12-bias catalogue (ICLR 2025).
