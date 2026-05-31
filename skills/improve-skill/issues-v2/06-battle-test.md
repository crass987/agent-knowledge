# Issue 06: Battle Test on Real Skills

## Type
HITL — human reviews the quality of improvements.

## Blocked by
- Issue 05 (Cleanup v1 & Archive)

## What to build

Validate improve-skill v2 by running it on 3 real skills with different characteristics. A human reviews the quality of injected rules and overall skill improvement.

### Test targets

1. **`code-review`** — short skill, no references/ directory. v1 produced 0 assertions. v2 should produce meaningful semantic assertions and inject rules that improve the skill's output.

2. **`video-knowledge-extraction`** — long skill with `references/` directory and `scripts/`. Tests multi-file targeting, source_file tracing, and the ability to improve skills with complex structure.

3. **`tdd`** — medium-length, highly structured skill with clear imperative rules. Tests whether the heuristic phase captures most rules and the LLM phase adds value on top.

### Human review criteria

For each skill, evaluate:
- Are injected rules meaningful and specific? (Not vague like "Provide better responses")
- Does the skill's output actually improve after rule injection?
- Are rules placed in the correct file and section?
- Is the improvement sustained across multiple test inputs?
- Does the quality audit catch real issues?

### Deliverables

- Updated evals.json for each tested skill (with any proposed assertions from quality audit)
- Notes on edge cases or bugs discovered
- SKILL.md adjustments based on findings (if any)

## Acceptance criteria

- [ ] `/improve-skill code-review` runs to completion with visible score improvement
- [ ] `/improve-skill video-knowledge-extraction` runs to completion with multi-file targeting
- [ ] `/improve-skill tdd` runs to completion with strong baseline assertions
- [ ] Human confirms injected rules are meaningful (not score-optimizing noise)
- [ ] Human confirms skill outputs improve after rule injection
- [ ] Quality audit produces actionable findings (not just "looks good")
- [ ] Any bugs discovered are documented or fixed
