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
| 02 | [Single-Skill Improvement MVP](02-single-skill-mvp.md) | AFK | 01 | ✅ done |
| 03 | [Quality Audit + Reporting](03-quality-audit-reporting.md) | AFK | 02 | ✅ done |
| 04 | [Batch Mode, Flags & Recovery](04-batch-mode-flags.md) | AFK | 02 | ✅ done |
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

### ✅ Issue 02: Single-Skill Improvement MVP — DONE

**What was done:**

1. **SKILL.md v2 rewritten**: Complete self-contained orchestrator with 4 phases
   - Phase 1 (Setup): arg parsing, skill dir discovery, git branch, eval generation
   - Phase 2 (Baseline): Agent tool execution per test_input, assertion_runner.py scoring, aggregated display
   - Phase 3 (Improvement Loop): 6 sub-steps (3a–3f) — diagnose, generate rule via Agent, inject via Edit, re-score, decide (commit/revert), stop check
   - Phase 4 (Report): baseline→final comparison, per-assertion status, git log, cost tracking

2. **Architecture**: SKILL.md handles all reasoning natively. Python tools called via Bash CLI:
   - `eval_generator.py <skill_dir>` → evals JSON to stdout
   - `assertion_runner.py --evals <path> --output <path>` → JSON result + exit code

3. **Safety constraints**: only `*.md` + `evals.json` editable, never `*.py`/`*.sh`/`scripts/`, one file per iteration, git revert on regression, 10-iteration cap, 3-iteration plateau detection

4. **37 integration tests** added (`test_skill_md_v2.py`):
   - Structural completeness (20 tests): all phases, sub-steps, sections present
   - V1 deprecation check (4 tests): no references to deleted modules
   - CLI interface validation (5 tests): eval_generator and assertion_runner CLIs work as documented
   - End-to-end pipeline (3 tests): generate evals → sample output → score
   - Safety constraints (5 tests): forbidden edits, iteration caps, atomic commits

5. **Total test count: 113** (27 assertion_runner + 49 eval_generator + 37 SKILL.md v2)

**Acceptance criteria: 10/11 done, 1 needs HITL:**
- ✅ SKILL.md frontmatter with name, description, trigger phrases
- ✅ Phase 1: arg parsing, skill directory discovery, git branch creation, eval generation
- ✅ Phase 2: Agent tool execution on each test_input, assertion_runner.py scoring, baseline display
- ✅ Phase 3a: Diagnose — identify first failing assertion, resolve target file via source_file
- ✅ Phase 3b: Generate — LLM returns rule text, target section, insertion position
- ✅ Phase 3c: Inject — Edit tool with marker format, atomic single-file change
- ✅ Phase 3d: Re-score — re-run skill via Agent on all test_inputs, score, compare
- ✅ Phase 3e: Decide — commit if improved, revert if same/lower
- ✅ Phase 3f: Stop check — all pass / 3 plateau / 10 cap
- ⏳ End-to-end: `/improve-skill code-review` — needs HITL (real Agent execution, issue 06)
- ✅ Safety: only `*.md` files and `evals.json` are edited, never `*.py` or `*.sh`

### Remaining issues

- **05**: Delete v1 Python modules, archive old issues/PRD
- **06**: Human validation on 3 real skills

### ✅ Issue 03: Quality Audit + Reporting — DONE (parallel with 04)

Commit: merged into `2253372` on `main`

**What was done (parallel agent in worktree):**

1. **Phase 4: Quality Audit** (new, inserted between Phase 3 and old Phase 4)
   - Step 4a: Agent call with 5 quality dimensions (completeness, specificity, accuracy, style consistency, non-banality)
   - Step 4b: Parse structured findings (per-dimension scores + issues + suggestions)
   - Step 4c: Convert recurring problems to proposed assertions stored in `proposed_assertions` array

2. **Phase 5: Report** (renumbered from Phase 4, enhanced)
   - 5a: Per-assertion comparison table with ✅/❌ icons
   - 5b: Git commit history
   - 5c: Agent + LLM call counts
   - 5d: Stopping reason
   - 5e: Summary table
   - 5f: Audit recommendations from Phase 4
   - 5g: Proposed assertions for next run

3. **Phase numbering validation** — TestPhaseNumbering class ensures exactly 5 phases in order

4. **20 new tests** (TestQualityAudit: 8, TestEnhancedReport: 8, TestPhaseNumbering: 4)

### ✅ Issue 04: Batch Mode, Flags & Recovery — DONE (parallel with 03)

Commit: merged into `2253372` on `main`

**What was done (parallel agent in worktree):**

1. **Batch mode**: `--all` discovers all skills in both directories, named lists (`/improve-skill tdd debugging`), error isolation, per-skill git branches
2. **--regen flag**: deletes existing evals.json before regenerating
3. **--dry-run flag**: runs all phases but skips Edit/Write and git operations; displays what would happen
4. **Crash recovery**: git-based — reads git log on restart, re-scores for fresh baseline, continues from last state
5. **Cost tracking**: per-iteration cumulative display of agent calls, LLM calls, test inputs evaluated

6. **18 new tests** (TestBatchMode: 5, TestCLIFlags: 5, TestCrashRecovery: 5, TestCostTracking: 3)

### Combined test counts after integration

| Test file | Tests |
|-----------|-------|
| test_assertion_runner.py | 27 |
| test_eval_generator.py | 49 |
| test_skill_md_v2.py | 75 (11 classes) |
| **Total** | **151** |

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
