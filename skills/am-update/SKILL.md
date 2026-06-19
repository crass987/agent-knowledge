---
name: am-update
description: Use in the Astra Monitoring meta-repo to run the full artifact refresh after repos change — "am-update", "update artifacts", "обнови артефакты", "refresh profiles and C2". Orchestrates sync → facts → refresh profiles → c2-audit → c2-fix (auto-fix C2 drift) → review-queue reconcile → summary. Supersedes the manual meta/prompts/update-all.md flow. Astra-specific.
---

# am-update — Artifact Update Loop

## Overview

Single typed entry point for the periodic full refresh of Astra Monitoring artifacts: repo profiles (`meta/repos/*.md`), the C2 architecture doc, and reports. Chains existing scripts/prompts as fixed stages and emits one status line per stage into the summary.

Replaces hand-following `meta/prompts/update-all.md`. The engine is unchanged — this skill only packages it into predictable stages and closes two gaps the old flow left open: C2 drift was report-only (now auto-fixed for code-wins), and the human-review tail never closed (now tracked in a persistent review queue).

## When to Use

- After repos changed and profiles / C2 may be stale — run `/am-update`.
- Periodic refresh; trigger is manual (you decide cadence).

## When NOT to Use

- Researching a single feature → use `am-research`.
- One-off profile touch-up → edit `meta/repos/<svc>.md` directly.
- Anything outside the Astra meta-repo.

## Stages

Read each prompt file at the point it is needed — do not read all upfront.

**Stage 0 — prep.** `./sync-repos.sh --force` then `./meta/scripts/collect-repo-facts.sh` → `meta/reports/facts-YYYY-MM-DD.md` (includes Profile Connections + per-repo drift status).
*Status → summary:* `Stage 0 — prep: facts at meta/reports/facts-<date>.md`.

**Stage 1 — refresh profiles.** Follow `meta/prompts/refresh-agents.md` from Step 2 onward. Drift-aware: skip repos with `"none"` drift after a quick check; full review for `"N commits since..."`. Update `meta/repos/*.md`. Commit.
*Status:* `Stage 1 — profiles refreshed: N updated, M unchanged`.

**Stage 2 — C2 audit.** Follow `meta/prompts/c2-audit.md` in full, using fresh profiles as evidence. Per-service subagents (≤5 parallel, clean context). Produces `meta/reports/c2-drift-YYYY-MM-DD.md` (report-only).
*Status:* `Stage 2 — c2-audit: ✅N ⚠️N ❓N 👻N (HIGH: N)`.

**Stage 3 — C2 fix.** Follow `meta/prompts/c2-fix.md`. Classify each confirmed drift: code-wins → maker proposes C2 edit, separate checker verifies against code, commit on APPROVE; product-decision → append to review queue. Produces `meta/reports/c2-fix-summary-YYYY-MM-DD.md` and edits `analytics-hub/master_docs/Архитектура/C2-контейнеры.md`.
*Status:* `Stage 3 — c2-fix: N auto-fixed, M queued, K rejected-by-checker`.

**Stage 4 — review-queue reconcile.** Read `meta/reports/review-queue.md` by grepping `- [open` (never wholesale). Collect new `[REVIEW]` items from Stage 1. New → append `[open]`; items resolved this run → mark `[resolved]`/`[superseded]` with date; remaining `[open]` → re-surface in the summary.
*Status:* `Stage 4 — review-queue: N open, M resolved this run`.

**Stage 5 — summary.** Write `meta/reports/update-summary-YYYY-MM-DD.md` (existing format) + append **C2 Fix Results** (Stage 3) and **Review queue (open)** (Stage 4). Commit profiles + C2 + reports + queue.

**(Optional)** Run `am-research-index` in `check` mode; fold `⚠️[REVIEW]` + unindexed items into the summary's Review queue. Skip if registry unchanged.

## Rules

- **maker≠checker** on Stage 3 (P9): the agent proposing a C2 edit never verifies it.
- **Selective reads:** review-queue via grep by status; never dump the whole store.
- **Write scope:** `meta/repos/*.md`, `meta/reports/*`, `meta/reports/review-queue.md`, and the doc `analytics-hub/master_docs/Архитектура/C2-контейнеры.md`. Code repos are read-only.
- Each stage emits exactly one status line into the summary — that is the transparency contract.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson (a command quirk, a tool gotcha, a project-specific fact) that would save 5+ minutes next time — append it to the matching file in `agent-knowledge/learnings/` using the frontmatter format in `learnings/README.md`. Gate: do not log obvious/transient facts.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, duration (s), outcome (success/fail/abort), branch, note. Both stores are local-only.
