---
name: code-review
description: Code review process and checklist
---

# Code Review Skill

## When to use

- Reviewing pull requests.
- Providing feedback on someone else's code.

## Review priorities (in order)

1. **Correctness** — Does the code do what it's supposed to? Any bugs?
2. **Security** — Any injection, auth, or data exposure risks?
3. **Performance** — N+1 queries, unnecessary allocations, missing indices?
4. **Readability** — Can a new team member understand this in 6 months?
5. **Design** — Does it fit the architecture? Are boundaries clean?
6. **Style** — Formatting, naming, conventions (automate with linters).

## Giving feedback

- Be specific: point to the line and explain the issue.
- Distinguish blocking issues (must fix) from suggestions (nice to have).
- Ask questions instead of making demands: "What happens if X is null?" > "Check for null."
- Acknowledge what's done well, not just what needs change.

## Receiving feedback

- Assume good intent. Don't take it personally.
- Ask for clarification if a comment is unclear.
- Push back with reasoning if you disagree — but stay open.
- Respond to every comment, even if just "Done" or "Good catch."

## Checklist

- [ ] Tests cover the new/changed behavior
- [ ] Edge cases handled (null, empty, error states)
- [ ] No hardcoded secrets or sensitive data
- [ ] Public APIs have documentation
- [ ] Breaking changes are flagged in the PR description
