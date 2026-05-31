# Issue 01: Assertion Runner — deterministic eval engine

## Type
AFK — can start immediately, no human interaction needed.

## Blocked by
None — can start immediately.

## What to build

Build the assertion evaluation module: a pure function that takes raw text output (string) and an `evals.json` object, then returns a structured pass/fail result.

The module must support exactly these check types:

- `regex` — output must match the regex pattern
- `not_regex` — output must NOT match the regex pattern
- `contains` — output must contain the given substring
- `not_contains` — output must NOT contain the given substring
- `max_words` — output word count must be ≤ value
- `min_words` — output word count must be ≥ value

Return shape:

```json
{
  "total": 10,
  "passed": [{"id": "a01", "description": "..."}],
  "failed": [{"id": "a02", "description": "...", "actual": "what was found instead"}]
}
```

Contract: **deterministic** — same input + same evals = same result, always. No LLM calls, no randomness, no I/O beyond reading evals.json from disk.

Write this as a standalone module (Node.js or Python — match the project's convention). Include a CLI smoke test that loads a hand-crafted evals fixture and a sample output, runs all assertions, and prints the structured result.

## Acceptance criteria

- [ ] Module implements all 6 check types (`regex`, `not_regex`, `contains`, `not_contains`, `max_words`, `min_words`)
- [ ] Supports regex flags (`m`, `i`, `mi`, empty) for `regex` and `not_regex` types
- [ ] Returns structured result with `total`, `passed[]`, `failed[]`
- [ ] Each `failed` entry includes `actual` — a short description of what was found instead
- [ ] Deterministic: running the same input 100× produces identical results
- [ ] Handles edge cases: empty output string, assertions with special regex characters, assertions with no flags
- [ ] CLI smoke test passes: `node run-assertions.js --evals fixture-evals.json --output fixture-output.txt` exits 0 and prints structured JSON
- [ ] No external dependencies beyond stdlib (no LLM calls, no network)

## Notes for the agent

- This is the **highest-value test target** in the entire system — the rest of the pipeline depends on it being correct.
- Start by defining the evals.json schema subset this module cares about (the `assertions[]` array). Full schema is in PRD.md under "evals.json Schema".
- Place the module at `improve-skill/lib/assertion-runner.{js/py}` (or equivalent).
- Place the CLI smoke test and fixtures at `improve-skill/tests/`.
