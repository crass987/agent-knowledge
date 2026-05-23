---
name: spec-writing
description: Writing feature specifications and PRDs
---

# Spec Writing Skill

## When to use

- Designing a new feature or significant change.
- Writing a PRD, RFC, or requirements document.

## Spec structure

```markdown
# [Feature Name]

## Problem
What problem exists for whom? Why does it matter now?

## Proposal
What are we building? One paragraph summary.

## User stories
- As a [role], I want to [action], so that [benefit].

## Requirements
### Must have
- [Requirement with acceptance criteria]

### Nice to have
- [Requirement with acceptance criteria]

## Technical design
- Architecture: [diagram or description]
- Data model: [new tables/schemas]
- API changes: [endpoints, breaking changes]
- Security considerations: [auth, data access]

## Success metrics
- [Metric] improves from [X] to [Y] by [date].

## Open questions
- [Question that needs resolution before implementation]
```

## Writing guidelines

- Specific > vague. "Reduce p95 latency from 3s to 500ms" > "Make it faster."
- Scope tightly. One spec = one feature. Split if it describes multiple independent changes.
- Include what's out of scope. Explicit non-goals prevent scope creep.
- Get feedback early. Share the draft before it's perfect.

## Review checklist

- [ ] Problem statement is clear and supported by data
- [ ] Success metrics are measurable
- [ ] Technical design reviewed by engineering
- [ ] Edge cases and error states addressed
- [ ] Open questions have owners and deadlines

## References

See `references/` for spec templates and example PRDs.
