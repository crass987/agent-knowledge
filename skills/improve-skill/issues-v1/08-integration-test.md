# Issue 08: End-to-end integration test on 3 real skills

## Type
HITL — requires human observation and validation of results.

## Blocked by
- Issue 04 (Improvement Loop)
- Issue 05 (Batch Orchestrator)
- Issue 06 (Reporting)

## What to build

Run the full `improve-skill` tool end-to-end on 3 diverse real skills and validate that everything works correctly:

1. **`video-knowledge-extraction`** — file-processing archetype, complex skill with references
2. **`tdd`** — prompt-based archetype, simple skill with only SKILL.md
3. **`code-review`** — multi-reference archetype, medium complexity

**For each skill, verify:**

- evals.json generation: correct archetype, valid schema, assertions trace back to real rules
- Baseline scoring: score is calculated, failing assertions identified
- Improvement loop: iterations run, rules injected correctly, scores tracked
- Git history: branch created, commits have correct format, reverts happen when expected
- Report: phase output is clear, per-assertion comparison is accurate, commit hashes are real
- Stopping condition: loop stops for the right reason (perfect score / plateau / hard cap)

**What the human validates:**
- Are the generated assertions reasonable? Do they test real quality rules?
- Did the injected rules make sense? Are they written in the skill's style?
- Did the score actually improve for meaningful reasons, not trivial ones?
- Is the report clear enough to understand without re-reading the session?

**Document findings:** Write a test report at `improve-skill/tests/integration-report.md` with:
- Per-skill results (evals count, baseline score, final score, iterations, stopping reason)
- Issues found (bugs, edge cases, quality concerns)
- Recommendations for v2

## Acceptance criteria

- [ ] All 3 skills run end-to-end without errors
- [ ] `video-knowledge-extraction` correctly detected as file-processing archetype
- [ ] `tdd` correctly detected as prompt-based archetype
- [ ] evals.json for each skill has ≥ 5 assertions (reasonable coverage)
- [ ] At least one skill shows measurable score improvement
- [ ] Git history on each improvement branch shows atomic commits
- [ ] Report output is human-readable and accurate
- [ ] Integration test report written at `improve-skill/tests/integration-report.md`
- [ ] Human has reviewed results and confirmed quality

## Notes for the agent

- This is the final validation gate. Do NOT skip — this is where real bugs surface.
- Run skills one at a time, not batch. Inspect each result before moving to the next.
- If a skill fails, document the failure but continue to the next — the goal is coverage, not perfection.
- Pay attention to token usage — each skill run may consume significant tokens. If approaching limits, note it in the report.
