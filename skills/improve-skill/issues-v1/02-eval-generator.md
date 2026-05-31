# Issue 02: Eval Generator — auto-generate evals.json from SKILL.md

## Type
AFK — can start immediately after Issue 01.

## Blocked by
- Issue 01 (Assertion Runner) — evals.json output must be consumable by the runner

## What to build

Build the module that reads a skill directory, extracts rules from `SKILL.md` (and reference `.md` files), converts extractable rules into binary code-based assertions, and writes `evals.json` to the skill directory.

**Archetype detection:** Classify skills into two archetypes based on the skill's description and content:

- **File-processing**: skill description mentions "file", "URL", "transcript", "video", "audio", "book", "document", or the skill has a decision tree with file input branches. Test input = `{"type": "file", "path": "<absolute path to shortest matching real file>"}`.
- **Prompt-based**: all other skills. Test input = `{"type": "prompt", "text": "<realistic prompt derived from skill description>"}`.

**Rule extraction:** Parse SKILL.md for imperative statements, constraints, format requirements. Convert only rules that can be expressed as binary code checks. Skip subjective rules (tone, "compelling", "clear") — log them as skipped.

**Test against real skills:**
- `video-knowledge-extraction` (file-processing archetype, complex)
- `tdd` (prompt-based archetype, simple)

End-to-end verification: run the generator on each skill → get a valid `evals.json` → feed it to the Assertion Runner with sample output → confirm the runner scores it without errors.

evals.json schema (full):

```json
{
  "version": 1,
  "skill": "skill-name",
  "generated_at": "ISO-8601",
  "test_input": {
    "type": "file | prompt",
    "path": "absolute path (for type=file)",
    "text": "prompt text (for type=prompt)"
  },
  "assertions": [
    {
      "id": "a01",
      "description": "human-readable what this checks",
      "source_rule": "the SKILL.md rule this was derived from",
      "type": "regex | not_regex | contains | not_contains | max_words | min_words",
      "check": "regex pattern (for regex/not_regex types)",
      "flags": "regex flags: mi, m, i, or empty",
      "value": "string or number (for contains/not_contains/max_words/min_words)"
    }
  ]
}
```

## Acceptance criteria

- [ ] Reads `SKILL.md` and all reference `.md` files from a given skill directory
- [ ] Detects archetype correctly: `video-knowledge-extraction` → file-processing, `tdd` → prompt-based
- [ ] For file-processing: sets `test_input.type = "file"` with path to the shortest matching real file from `/Users/CraSS/Documents/knowledge-base/`
- [ ] For prompt-based: sets `test_input.type = "prompt"` with realistic prompt text
- [ ] Converts extractable rules to binary assertions using the 6 check types
- [ ] Skips non-binary rules and logs what was skipped
- [ ] Each assertion has `source_rule` tracing back to the original SKILL.md rule
- [ ] Writes valid `evals.json` matching the schema to the skill directory
- [ ] End-to-end: generated evals.json for `video-knowledge-extraction` passes Assertion Runner validation
- [ ] End-to-end: generated evals.json for `tdd` passes Assertion Runner validation
- [ ] Assertion IDs are sequential (`a01`, `a02`, ...)

## Notes for the agent

- Skill directories: `/Users/CraSS/Documents/Code_projects/agent-knowledge/skills/` and `/Users/CraSS/.claude/skills/`
- Default test transcript for file-processing: `/Users/CraSS/Documents/knowledge-base/videos/5-claude-code-skills-every-day/transcript.txt`
- This module WILL use LLM calls (to extract rules and generate assertions). That's expected — it's the only module that calls an LLM besides the Skill Runner.
- Place at `improve-skill/lib/eval-generator.{js/py}`.
