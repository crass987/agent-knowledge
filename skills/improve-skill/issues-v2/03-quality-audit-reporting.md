# Issue 03: Quality Audit + Reporting

## Type
AFK — no human interaction needed.

## Blocked by
- Issue 02 (Single-Skill Improvement MVP)

## What to build

Add Phase 4 (Quality Audit) and Phase 5 (Reporting) to the SKILL.md. After the improvement loop converges, an LLM-as-judge call evaluates the final skill output holistically, and a structured final report is displayed.

### Phase 4: Quality Audit

After the improvement loop stops, a separate LLM call evaluates the final skill output:
- **Quality dimensions**: completeness, specificity, accuracy, style consistency, non-banality
- **Rubric**: the LLM receives the skill's own quality criteria as the evaluation rubric
- **Output**: structured findings with specific issues and suggestions
- **Feedback loop**: recurring problems are converted to `status: "proposed"` assertions in evals.json for future runs. These don't affect the current run's score.

### Phase 5: Report

Final structured report displayed in console:
- Baseline → final score, per-assertion comparison table
- Git commit history with change descriptions
- Agent call count, LLM call count
- Stopping reason (all pass / plateau / cap)
- Audit recommendations (if any)
- Proposed assertions for next run (if any)

## Acceptance criteria

- [ ] Phase 4: LLM-as-judge call with quality dimensions and skill-specific rubric
- [ ] Phase 4: Structured findings output (issues + suggestions)
- [ ] Phase 4: Proposed assertions written to evals.json with `status: "proposed"` (not scored)
- [ ] Phase 5: Score comparison table (baseline vs final, per assertion)
- [ ] Phase 5: Git commit history with rule descriptions
- [ ] Phase 5: Call count display (agent calls, LLM calls, test inputs evaluated)
- [ ] Phase 5: Stopping reason displayed
- [ ] End-to-end: running improve-skill produces a complete report with audit
