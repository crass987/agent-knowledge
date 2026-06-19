---
name: decisions
description: Use when recording or recalling a settled decision — "what did we decide", "log decision", "supersede decision", "напиши решение", "что решили", "почему решили", "архитектурное решение". Triggers on architecture, scope, tool/vendor decisions and reversals.
---

# Manage decisions

Authoritative settled calls: architecture, scope, tool/vendor choice, reversals. Lives in `decisions/decisions.active.md`. Distinct from `learnings/` (operational facts) and `memory/` (reflexive facts).

**HARD GATE:** This skill manages decisions only — it does not implement code.

## Commands

Parse the user's input:

- `decisions` (no args) or `list` → show recent active decisions.
- `decisions search <query>` → filter decisions by keyword or id.
- `decisions log` → record a new active decision.
- `decisions supersede <id>` → reverse an existing decision.

## list / search

```bash
grep -nE '^id:|^title:|^status:|^rationale:' decisions/decisions.active.md
```

For search, filter the output by the query.

## log

Gather (via AskUserQuestion or prose):

1. `title` — one line.
2. `rationale` — why this call, 1-2 sentences.
3. `scope` — harness | project.
4. `supersedes` — ids it reverses (optional).

Compute the next `id` (max existing `D-NNNN` + 1). Append a frontmatter block to `decisions/decisions.active.md` with `status: active`, `decided: <today>`, `supersedes: [...]`, `superseded_by: []`.

## supersede

1. Find the entry by id.
2. Change its `status: superseded` and set `superseded_by: [<new-id>]`.
3. Append the new active decision with `supersedes: [<old-id>]` (run the `log` flow).
4. Never edit the old rationale in place.

## Rules

- One decision per block, frontmatter required.
- Append-only — reverse by superseding, not by rewriting history.
- If the thing is really an operational fact or a reflexive note, route to `learnings/` or `memory/` instead.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — append it to the matching file in `agent-knowledge/learnings/`, using the frontmatter format in `learnings/README.md`. Gate: don't log obvious or transient facts. Then append one row to `agent-knowledge/state/skill-runs.md`.
