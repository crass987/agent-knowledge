# Decisions

Authoritative settled calls — architecture, scope, tool/vendor choice, or a reversal. Distinct from:

- `learnings/` — operational facts (quirks, commands, gotchas).
- `memory/` — reflexive facts about the user and project.

A decision is a **settled call with rationale**. Don't re-litigate it silently. If you reverse it, supersede it explicitly.

## Format

```yaml
---
id: D-0001                       # stable id, never reused
title: one line
status: active                   # active | superseded
decided: 2026-06-18              # ISO date
rationale: why this call, 1-2 sentences
supersedes: []                   # ids this decision reverses
superseded_by: []                # id that reversed this (when status: superseded)
scope: harness                   # harness | project
---
<optional: alternatives considered, constraints, links>
```

## Lifecycle

- **New decision** → append with a fresh `id`, `status: active`.
- **Reverse a decision** → append a new active decision; set `supersedes: [<old-id>]` on the new one and mark the old entry `status: superseded` + `superseded_by: [<new-id>]`.
- Never edit an old decision's rationale in place — supersede it, so history stays auditable.

## When to record

Architecture choices, scope decisions, tool/vendor picks, and reversals. Not turn-level or trivial choices.

## How to manage

Use the `decisions` skill (`log` / `search` / `supersede`), or edit `decisions.active.md` directly by hand following the format above.
