---
name: traverse
description: Use for a periodic walk over the knowledge stores to surface connections, clusters, and drift — "пройдись по знаниям", "найди неожиданные связи", "traverse the stores", "что устарело в базе", periodic knowledge review (cadence: biweekly, state/cadence.md). Differs from prune (cleanup of flagged entries) — traverse is discovery: links, clusters, routers, cross-store facts.
---

# traverse — walk the graph, bring proposals

## Overview

A scheduled pass over the stores that produces a **proposal list**, not edits. The
value is the connections nobody wrote down: distant entries that collide, clusters
that deserve a header, routers that drifted from the skills directory. You walk and
propose; the owner disposes.

## The pass (fixed order)

1. `python3 scripts/store_check.py --memory <auto-memory-dir>` — the mechanical floor
   (`--memory` takes the memory **directory**, not MEMORY.md itself).
2. Read all of `learnings/`, `decisions/`, `memory/` (bodies, not just frontmatter).
3. **Router↔directory diff**: rows in `AGENTS.md` / `skills/_INDEX.md` vs actual
   `skills/` — dead rows, missing skills. This drift is mechanical and invisible to
   store_check; check it every pass.
4. Semantic sweep, looking for:
   - **Clusters** — ≥3 entries describing one pipeline/topic with no links between them;
   - **Cross-store facts** — the same fact living in learnings + memory (or in a skill
     AND a store, with no check on those prose references);
   - **Semantic near-dups** — same fact, different keys (key-match dedup misses these);
   - **Doc-vs-practice conflicts** — store README says X, every entry does Y;
   - **Buried TODOs** — a learning that is actually an undone task.

## The report (three circuits, in this order)

**1. Механика — «делаю одним коммитом по команде "делай"»**: dead router rows, missing
router rows, wrong filenames, stale ledgers. Each with absolute path. Factual, grep-
verifiable, no judgment.

**2. Развилки — вопросы владельцу**: semantic pairs (supersede / enrich / keep), facts
duplicated into skills (evict or keep), doc-vs-practice conflicts (fix doc or fix
practice). One line each, options named. Nothing applied without the answer.

**3. Связи — предложения, не переписывание**: propose `[[wikilinks]]` between cluster
members or a cluster header in the store README; list the members. Never rewrite entry
content to force a connection.

Close with files outside your write-scope (user's global CLAUDE.md, other repos) as
suggestions only — never edit them.

## Rules

- Write nothing during the pass — the report is the deliverable.
- After the owner disposes: mechanical fixes = one commit; semantic = through `prune`;
  links = small edit per cluster. Log the run in `state/skill-runs.md` and bump
  `traverse` in `state/cadence.md`.
- Quality over count: findings without a proposed resolution are noise.

## Common mistakes

- Rewriting entries to "improve" a cluster instead of proposing links.
- Skipping the router diff because store_check passed — they check different things.
- Reporting raw counts ("45 entries, 12 problems") instead of dispositions.
- Editing the user's global config because the finding is "obvious" — propose, don't touch.
