# PRD v2: improve-skill — Autonomous Skill Improvement Tool

## Status

Design complete. Supersedes `PRD.md` (v1).

## What changed from v1

v1 was fully implemented (6 Python modules, 117 tests) but never battle-tested with real LLM calls. Integration testing revealed three structural problems:

1. **Heuristic-only rule extraction** misses ~60% of rule styles (checklists, advisory, question-format, implicit conventions). Code-review skill got 0 assertions.
2. **Single-file targeting** with fixed priority (SKILL.md → templates → checklists) ignores the actual root cause. A failure traceable to `references/templates.md` gets a patch in SKILL.md instead.
3. **Template-based rule injection** produces vague rules ("Provide a more detailed response") that don't tell the skill *what* to change.

v2 addresses all three with: hybrid eval generation (heuristic + LLM), source-file tracing + LLM diagnosis, and LLM-driven rule generation with smart placement.

## Architecture

### Minimal Python + SKILL.md

Python handles only what must be deterministic code. SKILL.md handles all reasoning.

| Component | Technology | Why |
|-----------|-----------|-----|
| Assertion runner | Python (`assertion_runner.py`) | Deterministic eval engine — same input + evals = same result, always. Must be testable with pytest. |
| Eval generator | Python (`eval_generator.py`) | Hybrid: heuristic phase (regex-based, fast, free) + LLM phase (semantic gaps). Writes evals.json. |
| Improvement loop | SKILL.md instructions | Diagnosis, rule generation, file targeting — all LLM reasoning. Uses native Claude Code tools (Agent, Read, Write, Edit, Bash). |
| Batch orchestration | SKILL.md instructions | Multi-skill invocation, error isolation, branch management. |
| Reporting | SKILL.md output | Phase-by-phase console output, final report. |
| Quality audit | SKILL.md + Agent | LLM-as-judge evaluates final output holistically. |

### Deleted from v1

These modules are replaced by SKILL.md orchestration:

- `improvement_loop.py` → reasoning is now native LLM
- `batch_orchestrator.py` → SKILL.md handles multi-skill
- `skill_runner.py` → native Agent tool replaces `claude --print`
- `reporter.py` → SKILL.md prints phases directly

## Eval Generation (Hybrid)

### Phase 1: Heuristic extraction (unchanged from v1)

Deterministic regex-based extraction of structural rules:
- Numbered/bullet imperative rules
- Format requirements (headers, sections, markdown)
- Explicit "must" / "never" / "always" statements
- Word count / compression ratio rules
- Russian imperatives (не, должен, всегда, никогда, нельзя)

Output: binary assertions with `source_rule` and `source_file` fields.

### Phase 2: LLM semantic extraction (new in v2)

After heuristic phase, an LLM call analyzes the full skill content:
- Identifies rules the heuristics missed (checklists, advisory style, implicit conventions)
- Generates assertions for semantic quality (completeness, correctness, specificity)
- Each assertion carries `source_file` pointing to which file the rule came from
- Receives the heuristic assertions as context to avoid duplication
- Can generate `contains`/`not_contains`/`regex`/`min_words`/`max_words` assertions

### Assertion types

Same 6 binary types as v1: `regex`, `not_regex`, `contains`, `not_contains`, `max_words`, `min_words`.

No `llm_judge` type — LLM-as-judge is a separate phase, not an assertion type.

## evals.json Schema (v2)

```json
{
  "version": 2,
  "skill": "skill-name",
  "generated_at": "ISO-8601",
  "test_inputs": [
    {
      "type": "file | prompt",
      "path": "absolute path (for type=file)",
      "text": "prompt text (for type=prompt)",
      "label": "human-readable label for reporting"
    }
  ],
  "assertions": [
    {
      "id": "a01",
      "description": "human-readable what this checks",
      "source_rule": "the rule this was derived from",
      "source_file": "SKILL.md | references/templates.md | ...",
      "type": "regex | not_regex | contains | not_contains | max_words | min_words",
      "check": "regex pattern (for regex/not_regex types)",
      "flags": "regex flags: mi, m, i, or empty",
      "value": "string or number (for contains/not_contains/max_words/min_words)",
      "generator": "heuristic | llm"
    }
  ]
}
```

Changes from v1:
- `test_input` → `test_inputs` (array, supports multiple inputs)
- New field: `source_file` on each assertion (traces rule to originating file)
- New field: `generator` on each assertion ("heuristic" or "llm")
- `version` bumped to 2

## Multi-File Targeting

### Source-file tracing

When assertions are generated, each one carries a `source_file` field indicating which file in the skill directory the rule came from. The improvement loop uses this as the primary signal for file targeting.

### LLM diagnosis (fallback)

When `source_file` is ambiguous (rule appears in multiple files) or missing (LLM-generated assertion with no clear origin), the loop asks an LLM to diagnose the root cause. The LLM reads all skill files and the failing assertion, then returns which file should be modified.

### File priority

No fixed priority. The targeting decision is data-driven:
1. Primary: `source_file` from the failing assertion's evals.json entry
2. Fallback: LLM diagnosis when source_file is unclear
3. Last resort: SKILL.md (safest default)

## Improvement Loop

### Per-iteration flow

1. **Identify** first failing assertion (from aggregated score across all test_inputs)
2. **Target** the right file (source_file → LLM diagnosis → SKILL.md)
3. **Generate** rule + placement via LLM:
   - LLM analyzes the failing assertion, the skill output, and the target file
   - Returns: rule text (in the skill's language and style), target section, insertion position
4. **Inject** the rule via Edit tool (atomic, single-file change)
5. **Re-evaluate** by running the skill through Agent on all test_inputs, scoring with assertion_runner.py
6. **Decide**: improved → git commit | same/lower → git checkout -- <file> (revert)
7. **Check stopping**: perfect score | 3-iteration plateau | 10-iteration cap

### Rule injection format

Same marker format as v1 for traceability:

```
<!-- improve-skill: iteration N, assertion aXX -->
- <rule text in the skill's language and style>
<!-- /improve-skill -->
```

But placement is LLM-directed: the LLM specifies which section to target, not just "append to end."

### Git strategy

Unchanged from v1:
- Single skill: `improve/<skill-name>-YYYY-MM-DD`
- Batch: `improve/batch-YYYY-MM-DD`
- Commits: `improve(<skill>): <rule description> (score N→M)`
- Reverts: `git checkout -- <file>` (only the modified file)

## Quality Audit (new in v2)

After the improvement loop converges, a separate LLM call evaluates the final skill output holistically:

- **Quality dimensions**: completeness, specificity, accuracy, style consistency, non-banality
- **Rubric**: the LLM receives the skill's own quality criteria as the rubric
- **Output**: structured findings with specific issues and suggestions

### Feedback loop

Quality audit findings that identify recurring problems can be converted into new assertion suggestions. These are written to evals.json as proposed assertions (with `status: "proposed"`) for the next improvement run. They don't affect the current run's score.

## Safety

### Editable files

Only these file types may be modified:
- `*.md` files in the skill root directory and `references/` subdirectory
- `evals.json` in the skill directory

Forbidden:
- `scripts/*` and any executable files
- `*.py`, `*.js`, `*.sh` and any code files
- Files outside the skill directory
- Any file not explicitly targeted by the improvement loop

### --dry-run flag

Runs all phases (setup, baseline, diagnosis, rule generation) but does not:
- Execute any Edit/Write operations
- Create git commits
- Modify any files on disk

Output: full phase-by-phase display showing what *would* happen, including generated rules and target files.

## Crash Recovery

No checkpoint files. Recovery relies on:

- **Git history**: committed improvements survive crashes
- **evals.json**: assertions persist across runs
- **Re-run behavior**: on restart, read last N git commits to understand what was tried, re-score to get fresh baseline, continue loop

## Cost Awareness

After each iteration, display:
- Cumulative Agent calls
- Cumulative LLM calls (diagnosis, rule generation)
- Test inputs evaluated

No budget enforcement — the existing stopping conditions (10 cap + 3 plateau) bound worst case.

## Workflow Phases

```
/improve-skill <skill-name>

PHASE 1: SETUP
  ├── Parse args (skill name, --all, --regen, named list, --dry-run)
  ├── Discover skill directory (search both skill directories)
  ├── Create git branch: improve/<skill>-YYYY-MM-DD
  ├── Read all skill files (SKILL.md + references/*.md)
  ├── If evals.json exists and no --regen: skip generation
  └── Else: run eval engine
       ├── Heuristic phase: structural rules → binary assertions
       ├── LLM phase: semantic gaps → additional assertions
       ├── Each assertion gets source_file + source_rule
       └── Write evals.json to skill directory

PHASE 2: BASELINE
  ├── For each test_input in evals.json:
  │   └── Run skill via native Agent → capture output
  ├── Score all outputs via assertion_runner.py
  ├── Aggregate scores across all test_inputs
  └── Display: "Baseline: 15/40 passed, 25 failing"

PHASE 3: IMPROVEMENT LOOP (repeat up to 10×)
  ├── 3a. DIAGNOSE
  │   ├── Identify first failing assertion
  │   ├── Check source_file from evals.json
  │   ├── If source_file is clear: use it
  │   └── If not: LLM diagnoses across all skill files
  │
  ├── 3b. GENERATE RULE
  │   └── LLM analyzes failure + target file → returns rule text + placement
  │
  ├── 3c. INJECT
  │   └── Edit target file at LLM-specified placement
  │
  ├── 3d. RE-SCORE
  │   ├── Run skill via Agent on all test_inputs
  │   ├── Score via assertion_runner.py
  │   └── Compare with previous score
  │
  ├── 3e. DECIDE
  │   ├── If score improved: git commit (atomic)
  │   └── If score same/lower: git checkout -- <file> (revert)
  │
  └── 3f. STOP CHECK
       ├── All pass → stop (success)
       ├── 3 plateau → stop (plateau)
       └── 10 iterations → stop (cap)

PHASE 4: QUALITY AUDIT
  ├── LLM evaluates final output on semantic quality criteria
  ├── If issues found: generate new assertion suggestions
  └── Display audit findings

PHASE 5: REPORT
  ├── Baseline → final score, per-assertion comparison
  ├── Git commit history with change descriptions
  ├── Agent call count
  ├── Stopping reason
  └── Audit recommendations (if any)
```

## Invocation

```
/improve-skill <skill-name>           # Single skill
/improve-skill tdd debugging          # Named list
/improve-skill --all                  # All skills
/improve-skill --regen <skill-name>   # Force regenerate evals.json
/improve-skill --dry-run <skill-name> # Preview without changes
```

## File Structure (v2)

```
improve-skill/
├── SKILL.md                    # Skill instructions (the orchestrator)
├── PRD.md                      # v1 product requirements (archived)
├── PRD-v2.md                   # This document
├── adr/
│   └── 0001-skill-md-orchestration.md
├── lib/
│   ├── __init__.py
│   ├── assertion_runner.py     # Deterministic eval engine (kept from v1)
│   └── eval_generator.py      # Hybrid eval generator (rewritten for v2)
├── tests/
│   ├── test_assertion_runner.py
│   ├── test_eval_generator.py
│   ├── fixture-evals.json
│   └── fixture-output.txt
└── issues/                     # v1 issues (archived)
```

## Out of Scope for v2

- **Layer 1 (activation improvement)**: improving skill YAML descriptions for better trigger rates. Still Anthropic's territory.
- **Budget enforcement**: hard token limits that stop the loop. Display-only for v2.
- **CI/CD integration**: running outside a Claude Code session.
- **Modification of scripts/**: Python/shell scripts in skill directories remain out of scope.
- **Human-in-the-loop breakpoints**: the loop remains fully autonomous after invocation.

## Migration from v1

1. Keep `assertion_runner.py` as-is (27 tests, battle-tested)
2. Rewrite `eval_generator.py` for hybrid generation + v2 schema
3. Delete `improvement_loop.py`, `batch_orchestrator.py`, `skill_runner.py`, `reporter.py`
4. Write new `SKILL.md` with 5-phase workflow
5. Update tests: add hybrid eval generation tests, keep assertion runner tests
6. Archive v1 issues and PRD
