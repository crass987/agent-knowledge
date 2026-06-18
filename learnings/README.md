# Operational learnings

Durable facts that save time next session: command quirks, tool gotchas, project-specific conventions. This is the **operational** channel — distinct from `memory/` (reflexive: who the user is, what feedback they gave).

## Format

Each entry is a YAML frontmatter block followed by an optional one-line body. Append new entries at the bottom of the matching category file. Append-only; on contradiction, add a newer entry (latest wins) — `auto-prune` (P2) will surface conflicts.

```yaml
---
type: operational          # pattern | pitfall | preference | operational
key: short-kebab-key       # 2-5 words
insight: one sentence, fact not opinion
confidence: 1-10
source: observed           # observed | user-stated | extracted
files: []                  # optional, relevant paths
ts: 2026-06-18             # ISO date
scope: harness             # harness | project
---
<optional one-line elaboration>
```

## Categories
- `patterns.md` — repeatable ways that work
- `pitfalls.md` — things that bite
- `preferences.md` — settled taste calls
- `operational.md` — commands, tool quirks, environment facts

## Scope
- `scope: harness` → lives here (about the harness itself).
- `scope: project` → lives with that project (a section in its `AGENTS.md`), not here.

## Gate (do not log)
Obvious facts, one-off transient errors, or anything already written in a skill.
