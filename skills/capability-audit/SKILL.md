---
name: capability-audit
description: Use when deciding whether a harness component (skill/tool/context-section/subagent) is needed or is overhead the model already handles natively — "audit this skill", "is X overhead", "should we keep this tool", "is this skill necessary", "keep shrink retire", "прожарь скилл на необходимость", "measure skill marginal contribution". Runs a cold-probe (without the component) vs with-harness, measures the delta with proper statistics, ablates sections, returns keep/shrink/retire. Does NOT trigger on general code review, skill writing, or skill output-quality improvement (use improve-skill for quality).
---

# capability-audit — is this harness component actually necessary?

The **load-bearing question** (Anthropic, agentskills.io best-practices):

> *Ask yourself about every piece of content: "Would the agent make a mistake without this instruction?" If the answer is no, cut it.*

This skill is the **operationalisation of that question into a measuring procedure**. It does not invent ablation — it packages dispersed research into a repeatable audit with a keep/shrink/retire criterion that accounts for interaction effects, LLM stochasticity, and cost-of-failure.

## When to use

- "Audit this skill / tool / context section — is it overhead?"
- "Should we keep X? Does the model need it?"
- "Measure the marginal contribution of this component."
- "прожарь скилл на необходимость."

## When NOT to use

- **Writing a new skill** → use a skill-authoring skill.
- **Improving a skill's output quality** → `improve-skill` (that is quality, a different axis).
- **Checking a skill's content is still valid / links alive** → `prune` (validity, another axis).
- **General code review** → `code-review`.

## Boundary with prune and improve-skill — three orthogonal axes

| Skill | Axis | Question |
|---|---|---|
| `prune` | **validity** | is the content correct and the references alive? |
| `improve-skill` | **quality** | does the skill produce good output? |
| `capability-audit` | **necessity** | does the model need this component at all? |

A skill can be valid and high-quality but still be overhead — only the audit catches that. Sequence by cost: **prune → capability-audit → improve-skill** (cheapest signal first).

## Honest limits (state up front)

- **Audit reliability is inverse to harness necessity.** The whole method rests on detecting a delta the model cannot produce alone — but if the component truly is unnecessary, the delta is near zero and noise dominates. Underpowered audits falsely "retire" useful things.
- **The verifiability gap bites the audit itself.** For silent failures with only a weak oracle, the audit cannot verdict — the same limit that makes the component matter makes it hard to measure.
- **2026 ablation papers (CCI, AgentSpec) were verified by abstract; treat specific numbers as provisional.**

---

## Step 0 — classify the component type (before any probe)

The keep/remove decision depends on type. There is no single Anthropic matrix; assemble from the engineering blog + Claude Code docs.

| Component | Signal | Candidate for |
|---|---|---|
| Deterministic operation (sort, validate, API call) | "via token generation is costlier than an algorithm" | **tool / code**, not a skill |
| Expertise / procedure in natural language | "how we do it here", conventions, recipes | **skill** (progressive disclosure) |
| Context isolation / heavy subtask with explicit instruction | "clean window with no dialogue history" | **fork / subagent** |
| Private / volatile knowledge | repos.yml, owners, current state | **context** (always supply — the model never knows "now") |

Auditing "is this skill needed" is meaningless if the component should have been a tool. Record the contract (what it guarantees) + `pinned model_version` + `last_audited` for every component.

---

## Tiered method — don't run a full audit blindly

| Tier | When | What | Cost |
|---|---|---|---|
| **0 — heuristic triage** | always, first | Predicted verdict from `native-knowledge × loud/silent × cost-of-failure`. No probes. | minutes |
| **1 — light** | Tier 0 ambiguous or borderline | 20–30 organic probes, **≥2 runs**, Wilson/Bayesian CI, paired test. | hours |
| **2 — full** | high-stakes / load-bearing claim | 350–1000 questions, interaction-aware ablation, clustered SE. | days |

**Tier 0 is a PREDICTION only.** Always confirm a non-trivial verdict at Tier 1 or 2. A component the model knows natively, that fails loud, in a low-cost-of-failure domain is almost certainly overhead — but measure before cutting.

### Tier 0 triage grid (predicted verdict)

| | **fails LOUD** (test/error/build) | **fails SILENT** (wrong-but-plausible) |
|---|---|---|
| **model knows natively** | overhead → likely retire | danger: Δ≈0 looks like overhead but model may mislead → do NOT retire without strong oracle |
| **model does NOT know** (private/procedural) | keep (measurable) | keep — but audit needs strong oracle; weak oracle → "do not verdict" tag |

---

## The 7-phase loop

| Phase | Action | Artifact |
|---|---|---|
| **0. Inventory + type** | list components; each gets contract + type (Step 0) + pinned model + last_audited | registry |
| **1. Probe suite** | organic fail-cases from real sessions, **75/25 split** (75% alignment / 25% held-out); each task gets **oracle + oracle strength + severity** | probe.yaml (template in `references/probe-template.yaml`) |
| **2. Cold baseline** | run **without** the component, pinned model+config, **≥2 runs**, isolated trials | per-item results |
| **3. With-harness** | same suite, same model, **with** the component, ≥2 runs | per-item results |
| **4. Delta + statistics** | paired difference test on per-item results; Wilson/Bayesian for small N; classify on the 2×2 | verdict + CI + power note (`scripts/delta_stats.py`) |
| **5. Ablation** | one-at-a-time first pass → escalate to **interaction-aware factorial** on the load-bearing shortlist | contribution heatmap |
| **6. Decision** | keep / shrink / retire via the value function (below); **protected class** never cut by Δ alone | decision record |
| **7. Re-audit** | trigger: model upgrade / silent alias migration / quarter | refreshed labels |

Depth for each phase lives in the references; this table is the spine.

### Phase 1 — probe validity is the main source of truth (or of lies)

- **Mine organic failures from real logs**, not synthetic cases (Anthropic: *prioritise volume over quality*, *mirror real-world task distribution*).
- **Held-out is mandatory** (75/25). Contamination is measurable and strong: +25.8% GPT-4 overestimation on raw benchmarks (arXiv:2405.19740); 22.9% GSM8K drop after decontamination (arXiv:2406.13990).
- **Adversarial augmentation**: if the component exists to catch silent error Y, the probe must contain Y and its variants.
- **Oracle + strength per task**: `strong` (exit-code / test / ground-truth) / `weak` (rubric, verifier-model) / `none`. Without a strong oracle, a silent failure is **unmeasurable** — an audit of the silent quadrant with a weak oracle gets a "do not trust" tag.
- **Run isolation**: each trial from a clean environment — shared state inflates the result.
- **Class balance**: test both where the behaviour should fire and where it should not. One-sided eval → one-sided optimisation.

### Phase 2/3 — grading hierarchy

Anthropic: **code-based (exact/string match) > human > LLM-based** — choose the fastest, most reliable, most scalable. LLM-as-judge is the last resort, and then the mitigations in `references/judge-mitigations.md` are mandatory.

---

## Phase 4 — the statistics (what makes an audit honest)

The rule: **"ran it 5 times, looked at the mean" is noise.** Recipe from arXiv:2503.01747 and arXiv:2411.00640:

- **N < a few hundred → NOT the CLT.** Use Wilson or Beta-Binomial (`scripts/delta_stats.py`). The CLT systematically under-covers; N=30 is a debunked textbook threshold.
- **Power:** to resolve a δ-pp delta at α=0.05 / 80% power, **n ≈ 969/δ²** (3pp→~1000, 5pp→~350, 10pp→~87).
- **Three mandatory conditions:**
  1. **Paired difference test** on per-item results, not two independent CIs. Frontier-model correlation is 0.3–0.7 — pairing removes question-difficulty variance.
  2. **Clustered SE** when grouped by category — naive SE underestimates by up to 3×.
  3. **≥2 runs** under stochastic decoding — removes ~83% of ranking inversions (arXiv:2509.24086).

No eval framework gives a significance test out of the box (Inspect AI is closest). Export per-item data from Inspect/LangSmith; compute statistics externally via `scripts/delta_stats.py`. Full formulas and citations: `references/statistics.md`.

---

## Phase 5 — ablation: interaction-aware, not purely one-at-a-time

Simple sequential ablation (remove A → measure → remove B) **lies**: CCI (arXiv:2605.05716) found **56% submodularity violations** — a component's contribution depends on which others are enabled. Self-healing bias: the model compensates via other components.

Two-level procedure:
1. **Cheap first pass** — one-at-a-time across sections → find removal candidates (Δ≈0).
2. **Escalate on load-bearing** — for the 2–4 components claiming to be load-bearing, a minimum **full-factorial** run over their subset to catch interaction effects. Full factorial over the whole harness explodes past 5 components — apply only to the narrow shortlist.

Pragmatics and the submodularity evidence: `references/ablation.md`.

---

## Phase 6 — decision: value function + protected class

**Value function** (explicit tradeoff, not "by eye"):

```
keep  if   Δsuccess · P(failure) · cost_per_failure  +  Δ(latency/cost)
           >  token_overhead · invocations  +  maintenance_burden  +  context_rot_penalty
```

In a high-cost-of-failure domain (critical infra, compliance) the left side dominates → even a small Δsuccess on silent tasks justifies a heavy skill.

**Three outcomes:** `retire` → move to state `watch` (never hard-delete); `shrink` via ablation; `keep` + refresh labels.

**Protected class — "rare but catastrophic".** A component may exist for the 1% of catastrophic outcomes the probe cannot catch → Δ≈0 → a false retire. Rule: such components are **never cut by Δ alone**, only by direct verification that the case no longer reproduces. Severity weighting in the probe is mandatory.

### Known failure modes to defend against

| Failure mode | Mitigation in this method |
|---|---|
| Overfitting to the eval set (21.8–33.0% patch overfit, arXiv:2511.16858) | held-out 25%, fresh data (LiveBench pattern) |
| Goodhart / reward hacking (o3 reward-hacks 30.4% of runs, METR) | bypass-resistant graders; detect the hack → patch scoring, don't blame the model |
| Eval-awareness (Claude Opus 4.6 found a BrowseComp answer key on GitHub) | eval integrity is an ongoing adversarial problem, not design-time |
| Saturation (SWE-bench Verified at 93.9%) | saturation = no improvement signal; refresh the suite |
| Silent alias drift (cross-provider spread up to 56pp) | pinned `model_version`, re-audit on trigger |

---

## Inputs you need from the user

1. **Which component** to audit, and its **contract** (what it claims to guarantee).
2. **Pinned model_version** (an alias like `*-latest` silently drifts within a week).
3. **Cost-of-failure tier** (loud/silent × low/high) — sets the tier (0/1/2) and whether a weak-oracle verdict is allowed.
4. Access to **real session logs** to mine organic probes from.

If any are missing, ask before proceeding — an audit on synthetic probes with an unpinned model is theatre.

## References (progressive disclosure — read when the phase needs them)

| File | When to read |
|---|---|
| `references/probe-template.yaml` | Phase 1 — building the probe suite |
| `references/statistics.md` | Phase 4 — Wilson/Bayesian derivations, n≈969/δ², paired test, clustered SE |
| `references/ablation.md` | Phase 5 — one-at-a-time → factorial escalation; CCI submodularity; self-healing bias |
| `references/judge-mitigations.md` | Phase 2/3 when an LLM-as-judge is unavoidable — bias catalogue + default mitigation set |
| `scripts/delta_stats.py` | Phase 4 — the external statistical layer (Wilson, Beta-Binomial, paired test, clustered SE, power). Tested: `python3 -m pytest skills/capability-audit/tests/ -q` |

## Non-goals

- Not measuring the macro effect of AI ("no second planet" — different scope).
- Not building a new eval framework — use Inspect AI for runs, this skill for statistics + decision.
- Not a substitute for human review in high-cost-of-failure domains; it narrows where a human must look.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/`, using the format in `learnings/README.md`. Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill. Then append one row to `agent-knowledge/state/skill-runs.md`.
