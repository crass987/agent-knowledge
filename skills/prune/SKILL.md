---
name: prune
description: Use to clean up growing harness stores — "почисти learnings", "prune memory", "найди устаревшие записи", "conflicting entries", "почисти память". Detects stale references and contradictions across learnings/, decisions/, and optionally memory/. Triggers on governance and cleanup of harness knowledge.
---

# prune — keep the stores clean

## Overview

As `learnings/`, `decisions/`, and `memory/` grow, entries go stale (reference deleted files) or contradict each other (same key, different insight). This skill finds them and asks what to do. The pattern mirrors `am-research-index` `check`: **mechanical signals first, judgment only on the flagged set.**

Two modes:
- **`check`** — scan and report flagged entries; change nothing.
- **`prune`** — scan, then for each flagged entry ask remove / keep / update; apply.

Append-only: updates are new entries (latest wins), never in-place rewrites of history.

## When to Use

- Periodic cleanup ("почисти learnings", "prune the stores").
- After a refactor that deleted files referenced by learnings.
- When the stores feel noisy or contradictory.

## When NOT to Use

- Astra research-index staleness → `am-research-index` (separate store, separate skill).
- Improving a skill's output → `improve-skill`.

## Stores & scope

| Store | Path | Default |
|---|---|---|
| learnings | `learnings/*.md` | scanned |
| decisions | `decisions/decisions.active.md` | scanned |
| memory | `--memory <path>` | opt-in (you curate reflexive memory by hand) |

## Signals

| Signal | How detected | Flag |
|---|---|---|
| **Stale ref** | an entry's `files: [path]` where `path` no longer exists (`test -e`) | STALE |
| **Contradiction** | two learnings share a `key` with opposing `insight`; or two active decisions overlap in scope with conflicting `rationale` | CONFLICT |
| **Orphan supersede** | a decision is `status: superseded` but missing `superseded_by` | ORPHAN |
| **Age** | entry date | tiebreaker only — never flags alone |

Age is never a trigger on its own — change is (same rule as `am-research-index`).

## `check` mode

1. Scan the stores; collect signals (batchable — pure file/parse checks).
2. Print a report:

```
STALE:    learnings/operational.md: <key> — references deleted <path>
CONFLICT: learnings/pitfalls.md: <key> — "<insight A>" vs "<insight B>"
ORPHAN:   decisions.active.md: D-0003 — superseded, no superseded_by
```

No files changed.

## `prune` mode

For each flagged entry, ask via AskUserQuestion:
- A) Remove (delete the entry)
- B) Keep (no change)
- C) Update (dictate the new insight — appended as a new entry, latest-wins)

Apply the choices. For conflicts, removing the older entry is the usual resolution. Commit the stores afterward.

## Rules

- **Write scope:** only `learnings/`, `decisions/`, and (with `--memory`) the given memory path. Never touch skills, code, or the Astra meta-repo.
- **Append-only for updates** — never rewrite an old entry's insight in place; supersede it.
- Flag uncertainty; don't auto-delete on judgment calls — ask.
- Age alone never flags.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — append it to `agent-knowledge/learnings/`, format in `learnings/README.md`. Gate: don't log obvious or transient facts. Then append one row to `agent-knowledge/state/skill-runs.md`.
