# improve-skill v2 — Issue Backlog

PRD: `../PRD-v2.md`
Architecture decision: `../adr/0001-skill-md-orchestration.md`

## Dependency Graph

```
01-hybrid-eval-engine
  └─→ 02-single-skill-mvp  ←── TRACER BULLET
         ├─→ 03-quality-audit-reporting
         └─→ 04-batch-mode-flags
                ├─────┘
                └─→ 05-cleanup-v1
                       └─→ 06-battle-test
```

## Issues

| # | Title | Type | Blocked by | Status |
|---|-------|------|------------|--------|
| 01 | [Hybrid Eval Engine v2](01-hybrid-eval-engine.md) | AFK | — | pending |
| 02 | [Single-Skill Improvement MVP](02-single-skill-mvp.md) | AFK | 01 | pending |
| 03 | [Quality Audit + Reporting](03-quality-audit-reporting.md) | AFK | 02 | pending |
| 04 | [Batch Mode, Flags & Recovery](04-batch-mode-flags.md) | AFK | 02 | pending |
| 05 | [Cleanup v1 & Archive](05-cleanup-v1.md) | AFK | 03, 04 | pending |
| 06 | [Battle Test on Real Skills](06-battle-test.md) | HITL | 05 | pending |

## Where to start

**Issue 01** is unblocked — rewrite `eval_generator.py` for hybrid generation + v2 schema.

**Issue 02** is the tracer bullet — write the SKILL.md that orchestrates the 5-phase workflow for a single skill. This is the heart of v2.

**Issue 03** adds the quality audit (LLM-as-judge) and structured reporting.

**Issue 04** adds batch mode (`--all`), flags (`--dry-run`, `--regen`), and crash recovery.

**Issue 05** cleans up v1 code after all v2 features are working.

**Issue 06** is human validation on 3 real skills.

## Conventions

- AFK = fully autonomous, no human needed. HITL = needs human review.
- Python modules go in `lib/`
- Tests go in `tests/`
- The SKILL.md IS the orchestrator — all reasoning lives there
- Follow the evals.json v2 schema from PRD-v2.md exactly
