# improve-skill — Issue Backlog

PRD: `../PRD.md`

## Dependency Graph

```
01-assertion-runner ─────┬──→ 02-eval-generator ──┐
                         │                        ├──→ 04-improvement-loop ──→ 05-batch-orchestrator
                         └──→ 03-skill-runner ───┘│                        ──→ 06-reporting-persistence
                                                  │
                                                  └──→ 07-skill-registration ──→ 08-integration-test
```

## Issues

| # | Title | Type | Blocked by | Status |
|---|-------|------|------------|--------|
| 01 | [Assertion Runner](01-assertion-runner.md) | AFK | — | pending |
| 02 | [Eval Generator](02-eval-generator.md) | AFK | 01 | pending |
| 03 | [Skill Runner](03-skill-runner.md) | AFK | 01 | pending |
| 04 | [Improvement Loop](04-improvement-loop.md) | AFK | 01, 02, 03 | pending |
| 05 | [Batch Orchestrator](05-batch-orchestrator.md) | AFK | 04 | pending |
| 06 | [Reporting & Persistence](06-reporting-persistence.md) | AFK | 02, 04 | pending |
| 07 | [SKILL.md Registration](07-skill-registration.md) | HITL | 04, 05, 06 | pending |
| 08 | [Integration Test](08-integration-test.md) | HITL | 04, 05, 06 | pending |

## Where to start

**Issue 01** is unblocked — pick it up first.

After 01 is done, issues **02** and **03** can run in parallel (they're independent of each other).

Issue **04** is the merge point — it needs 01+02+03 complete.

## Conventions

- Each issue is a **vertical slice**: thin end-to-end path, not a horizontal layer
- AFK = fully autonomous, no human needed. HITL = needs human review at the end
- All modules go in `improve-skill/lib/`
- All tests go in `improve-skill/tests/`
- Follow the evals.json schema from PRD.md exactly
