# Harness Improvement — P1 (decisions store + OIAE improve-skill) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add an authoritative decisions store with supersede semantics; upgrade `improve-skill` with the OIAE self-improvement loop (maker≠checker).

**Architecture:** `decisions.active.md` = settled calls + rationale + supersede (distinct from `learnings/` = operational facts, `memory/` = reflexive facts). `improve-skill` gains an additive OIAE procedure: **O**bserve (read `state/skill-runs.md` telemetry) → **I**nspect (on failure clusters) → **A**mend (maker proposes a minimal `SKILL.md` diff) → **E**valuate (checker, different model/session, against regression evals) → **rollback** if it didn't help.

**Tech Stack:** Markdown (stores/skill), Python + pytest (checks), git.

**Scope guard:** Additive to `improve-skill` — do not remove or restructure its existing content. The pre-existing failing test `test_issues_v1_archived` is user WIP (an `issues/` → `issues-v1/` rename in progress): **DO NOT TOUCH.**

**Branch:** `main` (user preference). Commit per task; push once at the end.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `decisions/README.md` | Format, lifecycle, supersede, diff vs learnings/memory | Create |
| `decisions/decisions.active.md` | The decisions store (seed + format) | Create |
| `skills/am-decisions/SKILL.md` | log / search / supersede decisions (mirrors `am-research-index`) | Create |
| `AGENTS.md` | Router row for `am-decisions` | Modify |
| `skills/improve-skill/SKILL.md` | Additive `## OIAE self-improvement` procedure | Modify |
| `USAGE.md` | Decisions section | Modify |

---

## Task 1: decisions store

**Files:** Create `decisions/README.md`, `decisions/decisions.active.md`

- [ ] Write `decisions/README.md` (format with `id/title/status/decided/rationale/supersedes/scope`; lifecycle: new=active, reverse=supersede with `supersedes`+`superseded_by`; never edit rationale in place; diff vs learnings/memory).
- [ ] Write `decisions/decisions.active.md` (one-line header + commented seed example using the A+C independence decision).
- [ ] Verify: `ls decisions/`.
- [ ] Commit: `feat(decisions): add decisions.active store + format spec`.

## Task 2: am-decisions skill

**Files:** Create `skills/am-decisions/SKILL.md`; Modify `AGENTS.md`

- [ ] Write `skills/am-decisions/SKILL.md` — frontmatter (`name`, `description` with triggers: "what did we decide", "log decision", "supersede decision", "напиши решение"); commands: `log` (append active decision), `search` (grep by keyword/id), `supersede` (new active + mark old). Tool-agnostic (capability phrasing).
- [ ] Add AGENTS.md router row: `decision, что решили, напиши решение, supersede → skills/am-decisions/SKILL.md`.
- [ ] Verify linter clean on the new skill: `python3 scripts/lint-portability.py skills/am-decisions`.
- [ ] Commit: `feat(am-decisions): add decisions log/search/supersede skill`.

## Task 3: OIAE procedure in improve-skill (additive)

**Files:** Modify `skills/improve-skill/SKILL.md`

- [ ] Read `skills/improve-skill/SKILL.md` end-to-end.
- [ ] Append (do not edit existing sections) a `## OIAE self-improvement procedure` section: Observe (read `state/skill-runs.md` for failures/slowness) → Inspect (when failures cluster, read the SKILL.md + transcript) → Amend (maker: propose a minimal diff, one change) → Evaluate (checker: a **different** model or fresh session runs regression evals; did it help? regressions?) → rollback (`git revert`) if not. State the maker≠checker rule explicitly.
- [ ] Verify linter clean: `python3 scripts/lint-portability.py skills/improve-skill`.
- [ ] Commit: `feat(improve-skill): add OIAE self-improvement procedure (maker≠checker)`.

## Task 4: USAGE + README

**Files:** Modify `USAGE.md`, `README.md`

- [ ] Add a `## Решения` section to `USAGE.md`: what `decisions.active` is, how to log/supersede, diff from learnings.
- [ ] Add `decisions/` row to the README "Что где лежит"-style pointer (or the P1 mention).
- [ ] Commit: `docs: document decisions store (P1)`.

## Task 5: linter + tests + push

- [ ] `python3 scripts/lint-portability.py skills` → expect 0 findings.
- [ ] `python3 -m pytest -q` → expect 178 pass (the 1 pre-existing improve-skill fail remains — user WIP, out of scope).
- [ ] `git push origin main`.
- [ ] Report P1 complete.

---

## Self-review notes

- **Spec coverage (PRD §8 P1):** `decisions.active` ✅ T1+T2; OIAE-upgrade improve-skill ✅ T3; docs ✅ T4.
- **Scope guard honored:** improve-skill change is additive; pre-existing failing test untouched.
- **Type consistency:** decision `id` format `D-NNNN`, `status: active|superseded`, `supersedes`/`superseded_by` used consistently across README, store, and am-decisions skill.

## Subsequent plan (P2)

`auto-prune` skill (stale/contradiction over `memory/`+`learnings`+`decisions`, generalizing `am-research-index`); regression-eval seed per skill; optional decay.
