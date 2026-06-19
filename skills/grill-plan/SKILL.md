---
name: grill-plan
description: Interview the user relentlessly about a plan or design until reaching shared understanding — challenge it against documented decisions, the glossary, and the code; sharpen terminology; capture resolved decisions and terms inline into the harness stores. Use when the user wants "прожарь план", "grill my design", "прожарь меня", stress-test a plan before writing a PRD, or "решить с агентом что делать". Endpoint = shared understanding ready to spec.
---

# Grill a plan → shared understanding

## What this does

Relentless **one-question-at-a-time** interview about a plan or design. Walks every branch of the decision tree, resolving dependencies one by one. For each question, propose a **recommended answer** and wait for the user's call. Endpoint: shared understanding precise enough to write a PRD.

This is **NOT** a feature go/no-go evaluation (that's `am-grill-feature`). This assumes you're past "should we" and into "**what exactly, and does it fit what we already decided?**"

## Core rules

- **One question at a time.** Wait for an answer before the next. Don't batch.
- **Propose a recommended answer** for each question — don't ask open-ended without a steer.
- **Explore, don't ask, when the answer is in the repo.** If a question can be answered by reading code/docs/decisions — read it instead of asking the user.
- **Drive toward a PRD.** The endpoint is shared understanding crystallized into docs, ready to hand off to `am-write-specs` / `spec-writing`.

## Challenge against the existing model

- **Decisions.** Check every choice against `decisions/decisions.active.md` and the harness principles (e.g. the P1–P9 independence principles in `docs/superpowers/specs/2026-06-18-harness-improvement-prd.md`). If a plan contradicts a settled decision — surface it: *"We decided X (D-00xx); this plan assumes Y — reconcile?"*
- **Glossary.** When the user uses a term, check it against the project glossary. Astra product → the glossary in `PM.md`. Harness → `docs/glossary.md` (create lazily on the first resolved term). If a term conflicts or is fuzzy — sharpen it: *"you say 'account' — Customer or User? those are different things."*
- **Code/docs.** When the user states how something works — verify against the code. Contradiction → surface it.
- **Concrete scenarios.** Stress-test domain relationships with edge-case scenarios that force precise boundaries between concepts.

## Capture inline (don't batch)

As decisions and terms crystallize during the interview, capture them right away — into the user's **actual stores**, not a parallel system:

- **Resolved decision** (architecture / scope / tool choice; hard-to-reverse + surprising + real trade-off) → record via the `am-decisions` skill (`log` / `supersede`) into `decisions/decisions.active.md`. Offer sparingly — same bar as an ADR; skip trivial or one-way-obvious calls.
- **Resolved term** → the project glossary (Astra: `PM.md`; harness: `docs/glossary.md`). Glossary = terms only, no implementation detail.
- **Operational lesson** (would save 5+ min next time) → `learnings/` (see `learnings/README.md`).

**Do NOT write terms into `CONTEXT.md`.** In this harness `CONTEXT.md` is the **hot work channel**, not a glossary. (The upstream `grill-with-docs` assumed otherwise — this is the adaptation.)

## Where this sits in the chain

```
brainstorming / am-grill-feature  →  grill-plan  →  spec/PRD  →  writing-plans  →  executing-plans
   (decide if worth it)               (understand what)  (write it)    (plan)          (do)
```

- **Before (entry):** `brainstorming` (explore intent) or `am-grill-feature` (go/no-go on the idea). Don't grill-plan something you haven't decided to pursue.
- **This skill:** interview → shared understanding.
- **After (handoff):** write the spec as a **file** via `am-write-specs` (Astra product) or `spec-writing` (general). Then `writing-plans` → `executing-plans`.
- **`to-prd` is NOT this skill's handoff.** It publishes a *finished* PRD to the issue tracker (Jira). It sits further down — after the spec exists — and only if you want to track it in Jira.

Net: `grill-plan → am-write-specs / spec-writing → (optionally to-prd to publish)`.

## Endpoint

When the decision tree is resolved: summarize the **shared understanding** (decisions made, terms sharpened, open questions remaining) and hand off to **write the spec** — `am-write-specs` (Astra) or `spec-writing` (general). Do **not** jump to `to-prd` (it publishes to Jira — a separate, later step).

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — append it to `agent-knowledge/learnings/`, format in `learnings/README.md`. Gate: don't log obvious or transient facts. Then append one row to `agent-knowledge/state/skill-runs.md`.
