# improve-skill v2 — Issue Backlog

PRD: `../PRD-v2.md`
Architecture decision: `../adr/0001-skill-md-orchestration.md`

## Dependency Graph

```
01-hybrid-eval-engine ✅
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
| 01 | [Hybrid Eval Engine v2](01-hybrid-eval-engine.md) | AFK | — | ✅ done |
| 02 | [Single-Skill Improvement MVP](02-single-skill-mvp.md) | AFK | 01 | pending |
| 03 | [Quality Audit + Reporting](03-quality-audit-reporting.md) | AFK | 02 | pending |
| 04 | [Batch Mode, Flags & Recovery](04-batch-mode-flags.md) | AFK | 02 | pending |
| 05 | [Cleanup v1 & Archive](05-cleanup-v1.md) | AFK | 03, 04 | pending |
| 06 | [Battle Test on Real Skills](06-battle-test.md) | HITL | 05 | pending |

## Progress

### ✅ Issue 01: Hybrid Eval Engine v2 — DONE

Commit: `268d0b0` on `main`

**What was done (TDD, 6 cycles, 76 tests):**

1. **v2 schema**: `version: 2`, `test_inputs` (array) instead of `test_input` (singular), `label` on each input
2. **source_file tracing**: `_read_files_with_sources()` reads SKILL.md + references/*.md individually; each assertion carries which file its rule came from
3. **generator field**: all heuristic assertions get `generator: "heuristic"`, LLM assertions get `generator: "llm"`
4. **Multiple test inputs**: prompt skills get 2 prompts (basic + detailed), file skills get 1-2 files (varied by size)
5. **Assertion deduplication**: by exact `(type, check, value)` key; keeps assertion with longer description
6. **LLM phase seam**: `_run_llm_extraction()` stub returns `[]`; mockable in tests. SKILL.md (Slice 02) handles the real LLM call
7. **`validate_evals_schema()`**: updated for v2 — checks `test_inputs` array, `source_file`, `generator`, `label`
8. **`fixture-evals.json`**: updated to v2 schema
9. **Dead code removed**: `_read_reference_files()` deleted (replaced by `_read_files_with_sources`)

**E2E verification:**
- `video-knowledge-extraction`: 27 assertions from 6 files (SKILL.md + 5 references), correct source_file tracing
- `tdd`: 3 assertions, 2 test inputs, schema valid
- `code-review`: 0 heuristic assertions (same as v1) — LLM phase will fix this in Slice 02

**Test counts:** 49 eval_generator + 27 assertion_runner = **76 tests passing**

**Acceptance criteria: 9/11 done, 2 deferred to Slice 02:**
- ⏳ "code-review LLM assertions" — requires real LLM call (Slice 02)
- ⏳ "tdd assertions stronger than v1" — LLM phase will add more

### ⏳ Issue 02: Single-Skill Improvement MVP — NEXT

This is the tracer bullet. Write the new SKILL.md with phases 1-3:
- Phase 1 (Setup): parse args, discover skill dir, create git branch, run eval generator
- Phase 2 (Baseline): execute skill via Agent tool on all test_inputs, score via assertion_runner.py
- Phase 3 (Improvement Loop): diagnose → generate rule → inject → re-score → commit/revert → stop check

See `02-single-skill-mvp.md` for full spec.

### Remaining issues

- **03**: Quality audit (LLM-as-judge) + final reporting
- **04**: Batch mode (`--all`), flags (`--dry-run`, `--regen`), crash recovery
- **05**: Delete v1 Python modules, archive old issues/PRD
- **06**: Human validation on 3 real skills

## Conventions

- AFK = fully autonomous, no human needed. HITL = needs human review.
- Python modules go in `lib/`
- Tests go in `tests/`
- The SKILL.md IS the orchestrator — all reasoning lives there
- Follow the evals.json v2 schema from PRD-v2.md exactly

## Key files to understand before continuing

- `lib/eval_generator.py` — v2 hybrid eval engine (just rewritten)
- `lib/assertion_runner.py` — unchanged from v1, v2-compatible
- `tests/test_eval_generator.py` — 49 tests, 7 test classes covering v2
- `PRD-v2.md` — full product requirements, especially the workflow phases section
- `adr/0001-skill-md-orchestration.md` — why SKILL.md handles reasoning, not Python
