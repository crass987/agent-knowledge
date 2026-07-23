---
name: am-research-index
description: Use in the Astra Monitoring meta-repo to log finished research into meta/research-index.md ("зарегистрируй исследование", "log research") or to check research staleness + coverage ("проверь research index", "check research index", "что из исследований устарело"). Maintains the registry of what has already been investigated. Astra-specific.
---

# Research Index — log & check

## Overview

Maintains `meta/research-index.md` — the registry of human-investigative research (JTBD, competitive, pentest, SSO/RBAC, C2 validation, deep-research, etc.). Two modes:

- **`log`** — register or update one entry when a piece of research completes (auto-invoked by `am-research`; also usable manually).
- **`check`** — sweep every entry for staleness and coverage gaps; emit `meta/reports/research-staleness-YYYY-MM-DD.md`.

Astra-specific by contract: writes only `meta/research-index.md` and `meta/reports/research-staleness-*.md`; reads `PM/`, `meta/archive/`, `meta/reports/`; queries project MON via `mcp__jira__*`. Do NOT use outside the Astra meta-repo.

## When to Use

- `log` — you just finished research and produced an artifact under `PM/` or `meta/archive/`.
- `check` — periodic sweep, run standalone ("проверь research index") or as a step in `update-all`.

## When NOT to Use

- Machine-derived reports (`facts-*`, `refresh-summary-*`, `c2-drift-*`, `update-summary-*`) are NOT research — never index them.
- Searching repo code — use `ripgrep` / `Explore` / LSP.
- Anything outside the Astra meta-repo.

## Index entry format

`meta/research-index.md` is a flat bullet list; each entry is one dense line:

    - [STATUS] **Title** — #theme — <1-line conclusion, not the question> · 📄 path/to/artifact.md · 📅 YYYY-MM-DD · 🔗 MON-1234, v1.4, [[memory-name]]

- STATUS: `✅` active · `⚠️[REVIEW]` stale (needs eyes) · `🗄️→<title>` superseded (points to the newer entry).
- #theme: `#product` `#security` `#competitive` `#architecture` `#infra` `#process`.
- The file opens with a **legend** explaining STATUS / #theme / icons once, so bullets stay dense.

## `log` mode

1. Identify the artifact path(s) just produced. The **primary path is the dedup key**.
2. Decide title, `#theme`, the one-line **conclusion** (the finding, not the question), today's date, and refs (JTBD scenario / Jira key / shipped version / `[[memory-name]]`).
3. Open `meta/research-index.md`:
   - An entry with the same primary 📄 path exists → update its finding / date / refs / status (status → `✅`, unless you know it is superseded → `🗄️→<newer>`).
   - No match → append a new entry after the legend, keeping rough date order.
4. Multiple artifacts from one investigation → **one** entry with several 📄 paths.
5. Save. Commit **only** `meta/research-index.md` to the Astra meta-repo.

Never create a second entry for a path that already has one.

## `check` mode

For each entry, gather mechanical signals first (batchable), then apply judgment only to the flagged set. Then emit `meta/reports/research-staleness-YYYY-MM-DD.md`.

**Signals:**

| Signal | How | Result |
|---|---|---|
| **Source drift** | `git log -1 --format=%ci -- <artifact path>`; commit date newer than the entry's 📅 | `⚠️[REVIEW]` — re-read; finding may have moved |
| **Shipped refs** | the **jira** capability (`AGENTS.md` tool-registry) per 🔗 Jira key (Done/Closed/Released); or version ref shipped in `infra-releases` | `⚠️[REVIEW]` — reframe "future work" → "shipped" |
| **Supersession** (judgment) | a newer entry covers the same topic better | `🗄️→<newer title>` |
| **Age** | 📅 vs today | tiebreaker only — never flags alone |

Update STATUS inline in `meta/research-index.md` for confirmed stale/superseded entries.

**Coverage check:** list artifacts in `PM/strategy/`, `PM/initiatives/*/`, `PM/competitive/`, `PM/sessions/`, `meta/archive/`, and research-grade items in `meta/reports/` (e.g. `c2-validation-*`) whose path appears in **no** entry → report under "Unindexed research".

**Report layout** (mirrors `refresh-summary`'s *Needs Review*):

    # Research Staleness — YYYY-MM-DD

    ## Stale ([REVIEW])
    | Entry | Signal | Suggested action |
    |---|---|---|

    ## Superseded
    - <old> → 🗄️ <new>

    ## Unindexed research
    - path/to/artifact.md — not in index; consider logging

    ## Up to date
    - N entries, no signals.

Commit the report (and any STATUS updates) to the Astra meta-repo.

## Rules

- **Write scope:** only `meta/research-index.md` and `meta/reports/research-staleness-*.md`. Read-only on `PM/`, `meta/archive/`, sub-repos. Never edit `agent-knowledge` at runtime.
- **Age is never** a staleness trigger on its own — change is.
- Do **not** index machine-derived reports.
- Flag uncertainty with `[REVIEW]`; do not guess supersession.
- Cite the artifact path in every entry.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `~/Documents/Code_projects/agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `~/Documents/Code_projects/agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
