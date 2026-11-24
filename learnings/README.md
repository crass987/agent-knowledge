# Operational learnings

Durable facts that save time next session: command quirks, tool gotchas, project-specific conventions. This is the **operational** channel — distinct from `memory/` (reflexive: who the user is, what feedback they gave).

## Format

Each entry is a YAML frontmatter block followed by an optional body (one line or several). Append new entries at the bottom of the matching category file. Append-only; on contradiction, add a newer entry (latest wins) and mark the old one `status: superseded` + `superseded_by: <new-key>` (без замены — причина в теле записи). On enrichment (same fact, new detail), merge into the existing entry and bump `ts` — do not append a "clarification" entry next to it (`skills/ingest` routes and dedups at write time; `skills/prune` runs the periodic supersede pass — no auto-prune exists).

Optional frontmatter fields in practice: `status`/`superseded_by` (supersede), `skill: <name>` (fact tied to one skill), `tags: [...]`; bodies may be multi-line.

```yaml
---
type: operational          # pattern | pitfall | operational
key: short-kebab-key       # 2-5 words
insight: one sentence, fact not opinion
confidence: 1-10
source: observed           # observed | user-stated | extracted
files: []                  # optional, relevant paths
ts: 2026-06-18             # ISO date, bump on every edit
scope: harness             # harness | project | skill:<name> | product
status: superseded         # optional; с superseded_by: <key> или причиной в теле
---
<optional body>
```

## Categories
- `patterns.md` — repeatable ways that work
- `pitfalls.md` — things that bite
- `operational.md` — commands, tool quirks, environment facts
- Кластеры: Релизный конвейер AM — см. ключи release-notes-infra-by-code, release-notes-file-naming, draft-release-notes-future-release, release-notes-scope-vs-merged-dev, mon-jira-done-filter-and-transition-dates, mon-sprint-vs-fixversion
- Кластеры: Workflow-оркестрация — см. ключи workflow-verdicts-match-by-index, workflow-bulk-data-via-tmp-files, workflow-overlapping-edits-apply-order, chunk-slicing-drops-keys, cold-subagent-spec-grill

## Scope
- `scope: harness` → lives here (about the harness itself).
- `scope: skill:<name>` → fact tied to one skill of this repo (e.g. `skill:am-docs-audit`).
- `scope: project` → preferably lives with the project (its `AGENTS.md`) or in `memory/` — the practiced route is: supersede here, keep the fact there. A few project entries still live in these files — acceptable, do not multiply them.
- `scope: product` → product-level fact not tied to one project (rare).

## Gate (do not log)
Obvious facts, one-off transient errors, or anything already written in a skill.
