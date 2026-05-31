# Issue 06: Reporting and persistence — report output + evals.json reuse

## Type
AFK — enhances the loop output and persistence behavior.

## Blocked by
- Issue 04 (Improvement Loop) — for report rendering
- Issue 02 (Eval Generator) — for evals.json reuse logic

## What to build

Two related capabilities: structured report generation and evals.json persistence across runs.

### Report generation

**Console output during run (phase-by-phase):**
- Setup phase: skill name, archetype detected, number of assertions, test input source
- Baseline phase: baseline score (N/M assertions pass), list of failing assertions
- Loop phase (per iteration): iteration number, target file, rule injected, score before → after, action (committed / reverted)
- Report phase: final summary

**Final report includes:**
- Skill name
- Baseline score → Final score
- Per-assertion pass/fail at baseline and final (so user can see exactly what improved)
- All git commits with change descriptions and commit hashes
- Stopping reason: perfect score / plateau / hard cap
- Total iterations, total time elapsed

### evals.json persistence

- On first run: generate evals.json and write to skill directory (next to SKILL.md)
- On re-run: if evals.json exists, reuse it (don't regenerate)
- `--regen` flag: force regeneration even if evals.json exists
- evals.json lives at `<skill-dir>/evals.json` — travels with the skill

End-to-end: run a skill twice — second run reuses evals.json and shows "Reusing existing evals.json" in console. Verify report includes per-assertion breakdown and git commit hashes.

## Acceptance criteria

- [ ] Console output shows 4 phases: setup, baseline, loop (per iteration), report
- [ ] Setup phase shows: skill name, archetype, assertion count, test input source
- [ ] Baseline phase shows: score (N/M), list of failing assertions
- [ ] Loop phase shows: iteration number, target file, score delta, action
- [ ] Final report shows: baseline → final score, per-assertion pass/fail comparison
- [ ] Final report lists all git commits with hashes and descriptions
- [ ] Final report shows stopping reason and total iterations
- [ ] evals.json persists to skill directory on first run
- [ ] Re-run detects existing evals.json and reuses it (skips Eval Generator)
- [ ] `--regen` flag forces evals.json regeneration
- [ ] End-to-end: run skill twice, second run reuses evals, report is accurate both times

## Notes for the agent

- The report format should be plain text (markdown-like) printed to stdout — no HTML, no file output needed.
- Per-assertion comparison table is the most valuable part for the user — make it clear and scannable.
- Git commit hashes come from `git log` on the improvement branch.
- Place reporting at `improve-skill/lib/reporter.{js/py}`.
- Persistence logic can live in the Eval Generator module (add a "check if exists" guard).
