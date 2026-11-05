---
name: prune
description: Use to clean up growing harness stores — "почисти learnings", "prune memory", "найди устаревшие записи", "conflicting entries", "почисти память". Detects stale references and contradictions across learnings/, decisions/, and optionally memory/. Triggers on governance and cleanup of harness knowledge.
---

# prune — keep the stores clean

## Overview

As `learnings/`, `decisions/`, and `memory/` grow, entries go stale (reference deleted
files) or contradict each other. This skill finds them and asks what to do. Pattern:
**mechanical signals first (`scripts/store_check.py`), judgment only on the flagged set.**

Three modes:
- **`check`** — run the script + semantic read, print the flagged report; change nothing.
- **`prune`** — apply fixes: mechanical in batch, semantic per finding; supersede, never delete.
- **`compact`** — explicitly requested; physically removes entries `status: superseded` for 30+ days. The only mode that deletes.

## When to Use

- Periodic cleanup ("почисти learnings", "prune the stores") — cadence: monthly, see `state/cadence.md`.
- After a refactor that deleted files referenced by learnings.
- When the stores feel noisy or contradictory.

## When NOT to Use

- Astra research-index staleness → `am-research-index` (separate store, separate skill).
- Improving a skill's output → `improve-skill`.
- Storing something new → `ingest` (dedup happens at write time, not at cleanup).

## Signals

**Mechanical** — run first, they define the flagged set:

```sh
python3 scripts/store_check.py --root <repo> [--memory <auto-memory-path>]
```

Owns: stale `files:` refs, duplicate keys, broken `[[links]]` (LINK-ROT), dangling
`superseded_by` (ORPHAN), index↔file sync, budgets (WARN), no-frontmatter, and memory
freshness fields — expired/ill-formed `stale_after`, broken `refs:` paths (WARN).
Age is INFO there — never a trigger by itself; change is (same rule as `am-research-index`).

**Semantic** — your judgment, on the flagged set plus a full-store read:

| Signal | Flag |
|---|---|
| Contradiction | two entries with opposing insight within one scope (keys may differ) |
| Near-duplicate | same fact stated twice in different words/keys |
| Off-format | entry deviates from the store's README format |

## `check` mode

Run the script, do the semantic read, print a report grouped ERROR/WARN/semantic.
In the WARN group, report freshness (`stale-after`) as its own sub-list with days
overdue — that's the fix-next column.
No files changed.

## `prune` mode

1. **Backup**: `cp -R learnings decisions state /tmp/prune-backup-$(date +%Y%m%d-%H%M)/`.
   Never rely on git alone — stores may be dirty.
2. Mechanical findings: propose one batch fix, single confirmation, apply.
3. Semantic findings: ask per finding via AskUserQuestion:
   - **A) Supersede** (default for contradictions) — old entry gets `status: superseded`,
     `superseded_by: <new-key>`; write the new entry (latest-wins). History stays readable.
   - **B) Enrich** — merge into the existing entry in place (overlap without
     contradiction), bump `ts`. No "clarification" entries next to originals.
   - **C) Keep** — no change.
4. Every edit bumps `ts` — that's the recency signal for the next run and the budget check.
5. Commit the stores afterward; if unrelated dirty files exist, commit only the store paths.

## Rules

- **Write scope:** only `learnings/`, `decisions/`, and (with `--memory`) the given memory
  path. Never touch skills, code, or other repos.
- **Never delete outside `compact`.** Supersede or enrich — history stays reconstructable.
- Flag uncertainty; don't auto-delete on judgment calls — ask.
- Age alone never flags.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — append it to `~/Documents/Code_projects/agent-knowledge/learnings/`, format in `learnings/README.md`. Gate: don't log obvious or transient facts. Then append one row to `~/Documents/Code_projects/agent-knowledge/state/skill-runs.md`.
