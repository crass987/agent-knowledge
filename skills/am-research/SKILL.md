---
name: am-research
description: Use when asked about a feature in Astra Monitoring — "как работает X", "изучи фичу X", "расскажи про X", "research feature", "what is X". Triggers on feature investigation questions.
---

# Research a Feature

## Overview

Structured investigation of a feature in Astra Monitoring. Produces a comprehensive research summary with technical details, current status, and source references.

## When to Use

- User asks how a feature works or what it consists of
- User wants to understand a feature's current status
- User needs a feature overview before making decisions

## When NOT to Use

- Evaluating whether to build a new feature → use `am-grill-feature`
- Writing requirements for a feature → use `am-write-specs`
- Checking docs for inaccuracies → use `am-grill-docs`

## Process

### 0. Recall prior learnings

Before reading the PM context, surface what the harness already learned about this feature:

```bash
python3 "$HOME/.claude/skills/am-research/scripts/auto-retrieve.py" "<feature name>"
```

`scripts/` is a symlink to the repo-root `scripts/` (lives in `agent-knowledge`, deployed with the skill); Python's path resolution follows it back to the repo root, so `learnings/` is found regardless of the current working directory.

Returns at most **3** past operational lessons (patterns / pitfalls). If nothing matches, continue. This never loads the whole `learnings/` — only matched entries, to keep context clean.

### 1. Read PM context

Read `PM.md` from the Astra meta-repo root. Find the feature in the **Knowledge Map** table. Identify:
- Which services implement the feature
- Where requirements/specs are located
- Data flow connections

If the feature is NOT in the Knowledge Map — investigate from scratch using `AGENTS.md` and the data flow diagram.

### 2. Read service profiles

For each service identified, read `meta/repos/<service>.md`. Extract:
- Tech stack and key dependencies
- Project structure (key packages/modules)
- Cross-repo connections
- Build/test commands (for context on complexity)

### 3. Check requirements and specs

From the Knowledge Map paths, read:
- `analytics-hub/docs/requirements/REQ-*.md` — product requirements
- `analytics-hub/docs/specifications/SPEC-*/` — technical specifications
- `analytics-hub/improvements/` — backlog items related to the feature

### 4. Check Jira status

Using MCP Jira tools:
- Find the relevant epic (project MON)
- List stories and their statuses
- Note any blocked or in-progress items

### 5. Synthesize

Produce a structured summary:

```
## Feature: [name]

### What it does
[1-2 sentences]

### How it works
[Technical explanation with data flow]

### Services involved
- service-a: [role in this feature]
- service-b: [role in this feature]

### Current status
- Requirements: [draft/approved/none]
- Specs: [draft/approved/none]
- Jira: [epic status, X stories done / Y total]

### Open questions
- [anything unclear]

### Sources
- [list of files read with paths]
```

## Rules

- Always cite sources with file paths
- If a file doesn't exist or is empty, note it — don't skip
- If Jira lookup fails, note it and continue without
- Distinguish between "documented" and "actually implemented" when you can
- Flag anything that seems outdated or contradictory with [REVIEW]
- **Output location.** Save product output under `PM/` per the routing test in `PM/CLAUDE.md` (theme-specific → `PM/initiatives/<theme>/`; competitive → `PM/competitive/`; untethered one-off → `PM/sessions/`; disposable → `PM/tmp/`). Never write product artifacts into `meta/` — `meta/` is meta-repo infrastructure only.
- **Register the research.** After producing output under `PM/`, log it to `meta/research-index.md` via the `am-research-index` skill (`log` mode) — one entry keyed by the artifact path. This keeps the "did we already research X?" registry current. (Skip if the investigation produced no durable artifact, e.g. a pure conversational answer.)

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `~/Documents/Code_projects/agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `~/Documents/Code_projects/agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
