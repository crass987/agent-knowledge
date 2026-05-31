# Issue 01: Eval Engine v2 — hybrid generation + v2 schema

## Type
AFK — can start immediately, no human interaction needed.

## Blocked by
None.

## What to build

Rewrite `eval_generator.py` to support hybrid eval generation (heuristic + LLM) and the v2 evals.json schema. Verify `assertion_runner.py` works with the new schema without changes.

### 1. v2 schema support

Update the generator to output the v2 schema:

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
      "label": "human-readable label"
    }
  ],
  "assertions": [
    {
      "id": "a01",
      "description": "...",
      "source_rule": "...",
      "source_file": "SKILL.md | references/templates.md | ...",
      "type": "regex | not_regex | contains | not_contains | max_words | min_words",
      "check": "...",
      "flags": "...",
      "value": "...",
      "generator": "heuristic | llm"
    }
  ]
}
```

Key changes from v1:
- `test_input` → `test_inputs` (array, supports multiple inputs)
- New field: `source_file` on each assertion
- New field: `generator` on each assertion ("heuristic" or "llm")
- `version` bumped to 2
- Each test_input gets a `label` for reporting

### 2. Source-file tracing

When the heuristic phase extracts a rule from a specific file (SKILL.md, references/templates.md, etc.), the generated assertion must carry `source_file` pointing to that file. The generator reads files individually (not concatenated) to maintain this trace.

### 3. Multiple test inputs

Instead of a single `test_input`, the generator produces a `test_inputs` array:
- For file-processing skills: find 2-3 real files from the knowledge base (varying sizes/types)
- For prompt-based skills: generate 2-3 prompts varying in specificity (basic, detailed, edge-case)

### 4. Hybrid generation

**Phase 1: Heuristic** (existing v1 logic, with source_file tracing added)
- Keep all existing regex-based rule extraction patterns
- Each extracted rule now tracks which file it came from
- Output: assertions with `generator: "heuristic"`

**Phase 2: LLM semantic extraction** (new)
- After heuristic phase, make one LLM call with:
  - All skill files (SKILL.md + references/*.md)
  - The heuristic assertions already generated (to avoid duplication)
  - Prompt: "Identify quality rules in this skill that the existing assertions miss. Generate binary assertions for each. For each assertion, specify which file the rule comes from."
- Parse LLM response into structured assertions
- Each assertion gets `source_file` from the LLM's response
- Output: assertions with `generator: "llm"`

### 5. Assertion deduplication

After both phases, deduplicate assertions by normalized check pattern:
- Two assertions with identical `type` + `check`/`value` → keep the one with more specific `description`
- Log any duplicates removed

### 6. Verify assertion_runner.py compatibility

The assertion runner should work with v2 evals.json without code changes — the new fields (`source_file`, `generator`, `label`) are on the assertion/test_input objects but the runner only reads `type`, `check`, `flags`, `value`. Verify this with existing tests.

## Acceptance criteria

- [ ] eval_generator.py outputs valid v2 schema (test_inputs array, source_file, generator fields)
- [ ] Heuristic phase tracks source_file for each extracted rule
- [ ] LLM phase generates semantic assertions with source_file tracing
- [ ] Multiple test inputs generated (2-3 per skill)
- [ ] Assertion deduplication merges identical check patterns
- [ ] `validate_evals_schema()` updated for v2 schema (test_inputs array, new required fields)
- [ ] assertion_runner.py passes all existing tests with v2 evals.json fixtures
- [ ] End-to-end: generate evals for `video-knowledge-extraction` → verify source_file points to correct files
- [ ] End-to-end: generate evals for `code-review` → verify LLM phase produces assertions (v1 produced 0)
- [ ] End-to-end: generate evals for `tdd` → verify assertions are stronger than v1's 3 weak checks
- [ ] All existing assertion_runner tests still pass

## Notes for the agent

- This issue is the foundation for v2. Everything else depends on the eval engine producing quality assertions.
- The LLM call in phase 2 should be structured: ask the LLM to return a JSON array of assertions, not free text.
- For source_file tracing in the heuristic phase, the generator must track which file each rule was found in during extraction. This means reading files individually instead of concatenating them first.
- The existing 23 eval_generator tests should be updated to cover v2 schema output.
- The LLM phase can use `claude --print` or Agent tool for the semantic extraction call.
