---
name: debugging
description: Systematic debugging workflow
---

# Debugging Skill

## When to use

- Investigating errors, crashes, or unexpected behavior.
- Tracing the root cause of a reported bug.

## Workflow

```
1. REPRODUCE — Confirm the issue with a minimal, reliable reproduction.
2. OBSERVE   — Gather data: logs, stack traces, error messages, state.
3. HYPOTHESIZE — Form a specific, testable hypothesis about the cause.
4. TEST      — Verify or refute the hypothesis with the smallest change.
5. FIX       — Apply the fix with a test that prevents regression.
6. VERIFY    — Confirm the fix resolves the issue without side effects.
```

## Techniques

- **Bisect**: Use `git bisect` to find the commit that introduced the bug.
- **Logging**: Add strategic log statements at boundaries, not every line.
- **Rubber duck**: Explain the code flow step by step. Often reveals the issue.
- **Diff**: Compare working vs. broken state. What changed?
- **Minimal reproduction**: Strip away everything that isn't necessary to trigger the bug.

## Common pitfalls

- Changing multiple things at once — you won't know which fix worked.
- Assuming the cause without evidence — follow the data.
- Fixing symptoms instead of root causes — ask "why" at least 3 times.
- Skipping the regression test — if it happened once, it can happen again.

## After fixing

- Write a test that reproduces the original bug (should fail without the fix).
- Document the root cause in the commit message.
- If the fix is a workaround, create a follow-up ticket for the proper solution.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
