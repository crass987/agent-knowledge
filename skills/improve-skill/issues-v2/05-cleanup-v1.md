# Issue 05: Cleanup v1 & Archive

## Type
AFK — no human interaction needed.

## Blocked by
- Issue 03 (Quality Audit + Reporting)
- Issue 04 (Batch Mode, Flags & Recovery)

## What to build

Remove all v1 code that has been replaced by the v2 SKILL.md. Archive v1 artifacts for reference. Ensure a clean codebase with only v2 components.

### Delete v1 Python modules
- `lib/improvement_loop.py` → replaced by SKILL.md reasoning
- `lib/batch_orchestrator.py` → replaced by SKILL.md batch mode
- `lib/skill_runner.py` → replaced by native Agent tool
- `lib/reporter.py` → replaced by SKILL.md output

### Delete v1 test files
- `tests/test_skill_runner.py`
- `tests/test_improvement_loop.py`
- `tests/test_batch_orchestrator.py`
- `tests/test_reporter.py`
- `tests/integration-report.md`

### Archive v1 artifacts
- Rename `issues/` → `issues-v1/`
- Rename `PRD.md` → `PRD-v1.md`

### Final `lib/` structure
```
lib/
├── __init__.py
├── assertion_runner.py     # Kept — deterministic eval engine
└── eval_generator.py      # Kept — hybrid eval generator (v2)
```

### Final `tests/` structure
```
tests/
├── __init__.py
├── test_assertion_runner.py
├── test_eval_generator.py
├── fixture-evals.json      # Update to v2 schema
└── fixture-output.txt
```

## Acceptance criteria

- [ ] v1 Python modules deleted (improvement_loop, batch_orchestrator, skill_runner, reporter)
- [ ] v1 test files deleted (corresponding 4 test files + integration report)
- [ ] `issues/` renamed to `issues-v1/`
- [ ] `PRD.md` renamed to `PRD-v1.md`
- [ ] `lib/` contains only `__init__.py`, `assertion_runner.py`, `eval_generator.py`
- [ ] `tests/` contains only `__init__.py`, `test_assertion_runner.py`, `test_eval_generator.py`, fixtures
- [ ] All remaining tests pass (`pytest tests/`)
- [ ] AGENTS.md router table updated if improve-skill description changed
