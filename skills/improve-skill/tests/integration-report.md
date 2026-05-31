# improve-skill — Integration Test Report

**Date:** 2026-05-31
**Tester:** Automated (TDD pipeline)
**Status:** ✅ All AFK modules pass. HITL items documented.

---

## Test Results Summary

| Skill | Archetype | Assertions | Schema Valid | Notes |
|-------|-----------|-----------|-------------|-------|
| `tdd` | prompt ✅ | 3 | ✅ | Good coverage for simple skill |
| `video-knowledge-extraction` | file ✅ | 7 | ✅ | Russian rules extracted correctly |
| `code-review` | prompt ✅ | 0 | ✅ | No assertions — skill style mismatch |

---

## Per-Skill Findings

### 1. tdd (prompt-based, simple)

**Archetype detection:** ✅ Correct — `prompt`
**evals.json:** 3 assertions generated
- `a01` [not_contains] — "Never write production code except to make a failing test pass"
- `a02` [contains] — References "Write" (from "Write the simplest test")
- `a03` [contains] — References "Run" (from "Run all tests after each change")

**Sample scoring:** 1/3 on generic output, 3/3 on skill-appropriate output.

**Issues:**
- Assertion `a02` and `a03` are weak — they check for generic verbs ("Write", "Run") rather than skill-specific rules. A trivially matching output passes these.
- Missing assertions for: "Arrange-Act-Assert" structure, "RED → GREEN → REFACTOR" cycle, test simplicity rule.

### 2. video-knowledge-extraction (file-processing, complex)

**Archetype detection:** ✅ Correct — `file`
**evals.json:** 7 assertions generated
- Mix of `regex` (markdown headers) and `not_contains` (forbidden patterns)
- Russian negative imperatives correctly extracted ("не за темами", "не по темам")

**Sample scoring:** 7/7 on generic markdown output (all pass because checks are negative).

**Issues:**
- Some `not_contains` values are Russian sentence fragments ("за темами", "по темами") that may produce false positives/negatives.
- Duplicate assertion `a01` and `a03` both check markdown headers — deduplication in rule extraction missed this.
- No positive assertions (contains) for this skill — all checks are negative or structural.
- Missing assertions for: compression ratio (~1:6), chronological order test, visual knowledge test, deduplication check.

### 3. code-review (prompt-based, checklist style)

**Archetype detection:** ✅ Correct — `prompt`
**evals.json:** 0 assertions generated

**Root cause:** The code-review skill uses patterns not handled by v1 extraction:
- Checklist items (`- [ ] Tests cover...`) — not matched by bullet extraction
- Bold-numbered items (`1. **Correctness** — Does X?`) — extracted but questions aren't convertible
- Advisory style ("Be specific", "Ask questions") — doesn't match imperative patterns

**Impact:** This skill would need LLM-based assertion generation (v2) or manual `evals.json`.

---

## Module Test Results

| Module | Tests | Status |
|--------|-------|--------|
| assertion_runner | 27 | ✅ All pass |
| eval_generator | 23 | ✅ All pass |
| skill_runner | 14 | ✅ All pass |
| improvement_loop | 23 | ✅ All pass |
| batch_orchestrator | 15 | ✅ All pass |
| reporter | 15 | ✅ All pass |
| **Total** | **117** | **✅ All pass** |

---

## Architecture Assessment

### What works well
- **Assertion runner** is rock-solid: deterministic, fast, handles all 6 check types correctly
- **Archetype detection** is accurate for both English and Russian skills
- **Schema validation** catches all invalid evals.json structures
- **Skill discovery** correctly deduplicates and skips improve-skill itself
- **Reporter** produces clear, scannable phase-by-phase output

### Known limitations (v1)
1. **Rule extraction is heuristic-only** — misses checklist-style, question-style, and advisory rules
2. **No LLM-based assertion generation** — the eval generator uses regex patterns only
3. **Weak assertion quality** for some rules — checking for generic verbs instead of semantic content
4. **Duplicate assertions** not fully deduplicated (regex header check appeared twice for VKE)
5. **Skill runner depends on `claude` CLI** — won't work outside Claude Code without the CLI installed
6. **No progress persistence** — if the loop crashes mid-run, progress is lost

### Recommendations for v2
1. **LLM-based assertion generation** — use a sub-agent to analyze SKILL.md rules and generate higher-quality assertions
2. **Assertion deduplication** — merge identical check patterns before writing evals.json
3. **Multi-input benchmarks** — test against multiple transcripts/prompts per skill
4. **LLM-as-judge assertions** — add semantic checks (quality, coherence, completeness) alongside binary checks
5. **Checklist-style rule extraction** — handle `- [ ]` format and convert to `contains` assertions
6. **Progress checkpointing** — save intermediate results to survive crashes

---

## Files Created

```
improve-skill/
├── SKILL.md                          # Skill registration (Issue 07)
├── lib/
│   ├── __init__.py
│   ├── assertion_runner.py           # 6 check types, CLI smoke test
│   ├── eval_generator.py             # Archetype detection, rule extraction, EN+RU
│   ├── skill_runner.py               # File reading, prompt construction
│   ├── improvement_loop.py           # Karpathy cycle, git operations
│   ├── batch_orchestrator.py         # --all, named list, error isolation
│   └── reporter.py                   # Phase output, final report
└── tests/
    ├── __init__.py
    ├── test_assertion_runner.py      # 27 tests
    ├── test_eval_generator.py        # 23 tests
    ├── test_skill_runner.py          # 14 tests
    ├── test_improvement_loop.py      # 23 tests
    ├── test_batch_orchestrator.py    # 15 tests
    ├── test_reporter.py              # 15 tests
    ├── fixture-evals.json            # CLI smoke test fixture
    ├── fixture-output.txt            # CLI smoke test fixture
    └── integration-report.md         # This report
```
