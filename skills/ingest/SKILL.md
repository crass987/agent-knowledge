---
name: ingest
description: Use when the user gives knowledge to store — "запиши", "сохрани", "занеси в базу", "remember this", "keep this fact", dropping a file, link, or note to file away, "куда это положить". Routes the item to the right store, dedups against existing entries, and reports placement in one line. Triggers on storing, filing, saving knowledge into the harness stores.
---

# ingest — one-line placement with dedup

## Overview

The user gives an item (fact, file, link, note) and must not have to know the taxonomy.
You route, dedup, validate, and answer in one line: *«положил X в Y»*. When in doubt
about meaning — state your assumption in one line and proceed; ask only if the item
itself is unclear.

## Routing

| Input | Destination |
|---|---|
| Operational fact / pattern / pitfall | `learnings/<category>.md` (format: `learnings/README.md`) |
| Settled decision with rationale | `decisions/` (via `decisions` skill if available) |
| Reflexive knowledge (who the user is, standing feedback) | user's memory store — never `learnings/` |
| Document/artifact for the product workspace | per repo boundary rules (PM/ artifacts, meta/ infra) — never this repo |
| Ephemeral working data | outside any repo (`/tmp`) |

If the item fits two destinations, pick the narrower one and say so in the report.

## Dedup rule (before any write)

Grep stores for the item's subject (synonyms, both languages). Then:

- **No overlap** → append a new entry.
- **Overlap, no contradiction** → *enrich the existing entry in place*: re-read the
  source artifact first (never rewrite from memory of the memory — retellings lose
  facts), merge the new detail into its `insight`/body, bump `ts`, keep `key`.
  Do NOT append a "clarification" entry next to it — that is a duplicate with extra steps.
- **Contradiction** → new entry, latest-wins, mark the old one `superseded_by: <new-key>`
  (or `status: superseded` where the format has it). Never rewrite the old insight's
  meaning in place.
- The existing entry's original meaning must stay reconstructable: put the source and
  date of the new detail in the body.

## Defaults

- Never `git commit` / push — leave the change uncommitted unless asked.
- Never write outside the routed destination. Skills, code, other repos are read-only here.
- Don't invent `files:` paths the user didn't give; don't log obvious or transient things.
- Time-bound facts written to memory ("лицензия до 13.10", "токен ≈24ч") carry
  `stale_after: YYYY-MM-DD` and `refs:` paths to source artifacts — `store_check.py`
  warns when they expire or rot (WARN, never blocks).
- After writing: if `scripts/store_check.py` exists, run it with `--quick` on the touched
  store; report failures instead of hand-fixing.

## Report

One line: what, where, and (only if non-obvious) the dedup call —
«Записал <key> в learnings/operational.md; обогатил существующую запись X вместо дубля».

## Common mistakes

- Appending a "supplementary" entry for a fact that enriches an existing one (dup).
- Silently resolving a doc-vs-practice conflict (e.g. `scope: project` placement) —
  follow practice, note the conflict in the report line.
- Committing; writing product artifacts into this repo; creating new store files.
