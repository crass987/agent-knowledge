# Ablation — interaction-aware, not purely one-at-a-time

Simple sequential ablation (remove section A → measure → remove B → measure)
**lies**, and the literature quantifies by how much. This file is the procedure
and the evidence.

## Why one-at-a-time is not enough

The CCI study (arXiv:2605.05716, "More Is Not Always Better") ran a full
factorial ablation over 5 scaffolding components (planning, tools, memory,
self-reflection, retrieval). Findings load-bearing for this method:

- **56% submodularity violations.** A component's marginal contribution depends
  on which other components are already enabled. Greedy forward/backward
  selection is therefore unreliable — the "Δ≈0, cut it" signal from a
  one-at-a-time pass can vanish or reverse in a different configuration.
- **The "All-In" agent is consistently suboptimal.** On HotpotQA a single-tool
  agent beats the maximally-equipped agent by 32%. Defaulting to every component
  is a measurable loss.
- **Task-specific subset selection wins.** "maximally-equipped agent defaults
  should be replaced by task-specific subset selection via interaction-aware
  analysis."

Practitioner warning (pub.towardsai.net): naive ablation also lies because of
**self-healing bias** — the model compensates for a removed component by leaning
on the remaining ones, masking the removal's true cost.

## Two-level procedure

### Level 1 — cheap first pass (one-at-a-time)

Remove one section/component at a time, measure the delta vs the full harness.
Goal: **narrow the field** to removal candidates (Δ≈0) and to components that
claim to be load-bearing. This is screening, not a verdict.

### Level 2 — escalate to factorial on the load-bearing shortlist

For the **2–4 components** that (a) claim to be load-bearing or (b) whose
one-at-a-time delta is borderline, run a minimum **full-factorial** sweep over
their subset to catch interaction effects.

```
{A,B,C} full factorial = 2³ = 8 configs × N questions × ≥2 runs
```

Pragmatics:
- Reasonable for 2–4 components.
- Explodes past 5 — that is why Level 1 narrows first.
- For very large harnesses, consider Shapley-value attribution (arXiv:2502.00510,
  ShapleyFlow — the first game-theoretic framework for agentic component
  contribution) as a principled way to share credit across configs without the
  full 2^k blow-up.

## What to record

For each config: per-item pass/fail (not just the aggregate rate), the run count,
the pinned model_version. The heatmap of contribution = `(full harness) −
(config without component)` per item, clustered by probe category. Feed the
shortlist configs' per-item results through `paired_difference_test` and
`clustered_se` in `scripts/delta_stats.py`.

## Self-healing bias — how to spot it

If removing a component leaves the aggregate delta near zero but the **per-item
pattern shifts** (different items fail, compensated elsewhere), the model is
self-healing around the gap. Signals:
- the discordant-pair count is high but b_only ≈ c_only (movement in both
  directions);
- the failure mode changes category rather than disappearing.

When self-healing is suspected, the factorial escalation (Level 2) is mandatory,
not optional — only by removing the compensating component too does the real
cost surface.

## Citations

- arXiv:2605.05716 — CCI, "More Is Not Always Better: Cross-Component
  Interference in LLM Agent Scaffolding" (May 2026). 56% submodularity
  violations; All-In suboptimal. *(Verified by abstract; specific numbers
  provisional pending full-text.)*
- arXiv:2502.00510 — ShapleyFlow, game-theoretic component attribution.
- arXiv:2607.03691 — "Don't Blame the LLM": controlled longitudinal study
  fixing the model and varying only the scaffold. *(Verified by abstract.)*
- arXiv:2606.14674 — AgentSpec, modular specification for controlled component
  swap. *(Verified by abstract.)*
- https://pub.towardsai.net/your-llm-ablation-study-is-lying-to-you —
  self-healing bias, practitioner warning.
- https://www.anthropic.com/engineering/building-effective-agents — "start
  simple, add complexity only when demonstrably needed" (the philosophy this
  method operationalises; gives no operational test for "demonstrably").
