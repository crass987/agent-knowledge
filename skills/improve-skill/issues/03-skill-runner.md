# Issue 03: Skill Runner — execute skill against test input and capture output

## Type
AFK — can start immediately after Issue 01 (independent of Issue 02).

## Blocked by
- Issue 01 (Assertion Runner) — needed to verify captured output is scorable

## What to build

Build the module that reads a skill's files, constructs a sub-agent prompt, sends the test input, and captures raw text output.

**Flow:**
1. Read `SKILL.md` from the skill directory
2. Read all reference `.md` files from `references/` subdirectory (if exists)
3. Construct a sub-agent prompt: skill instructions as system context, test input as user message
4. Execute the sub-agent call (using Claude Code's agent/subagent mechanism)
5. Capture the raw text output (the sub-agent's final response)
6. Return the output string

**Test input handling:**
- `type = "file"`: read file contents from `test_input.path`, send as user message with context ("Process the following content according to the skill instructions:\n\n<content>")
- `type = "prompt"`: send `test_input.text` directly as user message

End-to-end verification: run `tdd` skill with a simple prompt test input → capture output → score with Assertion Runner → confirm non-zero result.

## Acceptance criteria

- [ ] Reads `SKILL.md` and all reference `.md` files from the skill directory
- [ ] Constructs a sub-agent prompt that includes the full skill instructions as context
- [ ] Handles both test input types: `file` (reads file, wraps in prompt) and `prompt` (sends directly)
- [ ] Captures and returns the sub-agent's raw text output as a string
- [ ] Returns output that is scorable by the Assertion Runner (plain text, no control characters)
- [ ] End-to-end: run `tdd` skill with prompt input, capture output, score with Assertion Runner — gets a valid result
- [ ] Handles missing `references/` directory gracefully (skill with only SKILL.md)
- [ ] Does NOT modify any files — read-only operation

## Notes for the agent

- This is a thin wrapper around a sub-agent call. The complexity is in prompt construction, not in the call itself.
- Sub-agent execution uses the Claude Code Agent tool or equivalent mechanism.
- The skill directory may contain `scripts/` — do NOT read or execute scripts. Only read `.md` files.
- Place at `improve-skill/lib/skill-runner.{js/py}`.
- Skills can be large (SKILL.md + multiple references). Ensure the entire skill context fits within the sub-agent's context window.
