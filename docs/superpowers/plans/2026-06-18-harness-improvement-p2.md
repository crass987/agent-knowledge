# Harness Improvement — P2 (governance: auto-prune + selective retrieve + regression evals) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Keep the growing stores healthy and the agent's context clean as the harness accumulates data: auto-prune stale/conflicting entries, rotate the fastest-growing log, add **selective** auto-retrieve (never wholesale), and seed regression evals per skill.

**Architecture:** `auto-prune` generalizes `am-research-index`'s prune mode to `memory/` + `learnings/` + `decisions/` (stale-reference + contradiction detection, append-only latest-wins, human approval on conflicts). Auto-retrieve runs at skill start and greps **≤3** relevant learnings by keyword/key — never the whole file. Regression evals are a minimal, deterministic seed per am-* skill (Anthropic eval-the-harness).

**Tech Stack:** Markdown + Bash (prune/rotate/retrieve helpers), Python + pytest (evals, prune logic), git.

**Load-bearing rule (user-confirmed, do NOT violate):** never wholesale-load any store into context. Auto-retrieve returns at most 3 entries. If a store is large, retrieve stays selective — the agent greps, never reads the whole file.

**Scope guard:** `am-research-index` is actively used — generalize its prune logic without breaking its existing research-index behavior. Additive where possible.

**Branch:** `main` (user preference). Commit per task; push at the end.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `skills/am-prune/SKILL.md` | stale + contradiction detection over memory/learnings/decisions | Create |
| `scripts/auto-retrieve.sh` | skill-start helper: grep ≤3 relevant learnings by keyword | Create |
| `scripts/rotate-skill-runs.sh` | keep last N rows of `state/skill-runs.md` | Create |
| `skills/am-research/SKILL.md` (footer) | call auto-retrieve at start (pilot) | Modify |
| `evals/` | regression-eval seed per am-* skill | Create |
| `AGENTS.md` | router row for `am-prune` | Modify |
| `USAGE.md` | governance section (prune/rotate/retrieve) | Modify |

---

## Task 1: auto-prune skill

- [ ] Read `skills/am-research-index/SKILL.md` (its `prune` mode) to reuse the stale/contradiction pattern.
- [ ] Create `skills/am-prune/SKILL.md`: scans `memory/`, `learnings/`, `decisions/`; flags (a) entries whose `files:` reference deleted paths (stale), (b) same `key`/`id` with opposing `insight`/`rationale` (contradiction); presents flagged set via AskUserQuestion (remove / keep / update); append-only, latest-wins. Tool-agnostic.
- [ ] Add AGENTS.md router row: `prune, чистка памяти, устаревшие, конфликты → skills/am-prune/SKILL.md`.
- [ ] Linter clean; commit `feat(am-prune): add stale+contradiction prune skill`.

## Task 2: selective auto-retrieve

- [ ] Create `scripts/auto-retrieve.sh <query>`: greps `learnings/*.md` for the query (keyword/key), prints **≤3** best matches as short frontmatter blocks. Hard cap = 3. Never cats a whole file.
- [ ] Wire into the pilot: add to `am-research` footer a "before starting, run auto-retrieve with the feature name" line. Keep it best-effort.
- [ ] Commit `feat(scripts): add selective auto-retrieve (≤3 entries, never wholesale)`.

## Task 3: rotate the fastest-growing log

- [ ] Create `scripts/rotate-skill-runs.sh [N=500]`: keeps the header + last N data rows of `state/skill-runs.md`, archives the tail to `state/skill-runs.archive-<date>.md` (gitignored).
- [ ] Commit `feat(scripts): add skill-runs rotation`.

## Task 4: regression-eval seed

- [ ] Create `evals/` with one minimal deterministic eval file per am-* skill (a few assertions each — output shape, required sections). Start tiny (Anthropic: 20-50 tasks is plenty; we do ~3-5/skill).
- [ ] Commit `feat(evals): seed regression evals for am-* skills`.

## Task 5: USAGE + tests + push

- [ ] Add a `## Поддержка (governance)` section to `USAGE.md`: prune (`am-prune`), rotation, selective retrieve — and restate "stores are never loaded wholesale."
- [ ] `python3 scripts/lint-portability.py skills` → 0 findings.
- [ ] `python3 -m pytest -q` → no new failures (pre-existing `improve-skill` fail remains).
- [ ] `git push origin main`. Report P2 complete.

---

## Self-review notes

- **Spec coverage (PRD §8 P2):** auto-prune ✅ T1; selective auto-retrieve (the missing P0/P1 piece) ✅ T2; regression evals ✅ T4; decay = deferred (optional, low value now).
- **Guardrail honored:** auto-retrieve hard-capped at 3; rotation bounds the fastest grower; prune bounds the rest.
- **Scope guard:** am-research-index generalized, not broken.
