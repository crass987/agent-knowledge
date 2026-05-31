# PRD: improve-skill — Autonomous Skill Improvement Tool

## Problem Statement

A developer maintains 29+ custom Claude Code skills across two source directories. Each skill has a SKILL.md (instructions), optional reference files (templates, checklists), and optional scripts. Over time, skill output quality drifts: rules get ignored, templates become stale, and edge cases accumulate. Improving skills manually requires running the skill, inspecting output, editing SKILL.md, and re-running — a cycle that takes weeks across 29 skills. The core pain: **too many skills to maintain manually, no systematic way to verify or improve output quality at scale.**

## Solution

A Claude Code skill (`/improve-skill`) that autonomously improves other skills using a Karpathy-style loop: **change → test → keep or revert**. The tool auto-generates binary assertions from each skill's existing rules, runs the skill against a fixed test input, measures which assertions pass/fail, and iteratively injects clarifying rules into SKILL.md (and reference files when needed) until output quality reaches a perfect score or the loop converges.

The loop is fully autonomous after invocation. Git branching provides a safety net: every change is committed atomically, and the loop reverts (git reset) any change that degrades the score. The user wakes up to a report.

## User Stories

### Core Loop

1. As a skill maintainer, I want to run `/improve-skill video-knowledge-extraction` and have it autonomously improve the skill's output quality, so that I don't have to manually iterate on SKILL.md
2. As a skill maintainer, I want the tool to auto-generate evals.json from my skill's existing rules, so that I don't have to write test suites by hand
3. As a skill maintainer, I want the tool to use a real transcript file as test input, so that improvement is grounded in actual skill usage
4. As a skill maintainer, I want each iteration to make exactly one change to exactly one file, so that I can trace which change fixed which assertion
5. As a skill maintainer, I want the tool to git commit improvements and git revert regressions, so that the skill never degrades below its baseline
6. As a skill maintainer, I want a clear report showing baseline score → final score, all changes made, and git commit hashes, so that I can review what happened without re-reading the entire session

### Assertions

7. As a skill maintainer, I want assertions to be code-based (regex, word count, contains/not-contains), so that the evaluation is deterministic and reproducible
8. As a skill maintainer, I want the tool to skip rules that cannot be expressed as binary code checks, so that evals.json stays honest about what it can verify
9. As a skill maintainer, I want each assertion to track which SKILL.md rule it was derived from (source_rule), so that I can trace failures back to specific instructions

### Improvement Strategy

10. As a skill maintainer, I want the loop to prefer modifying SKILL.md first, so that changes are localized to the skill's primary instruction file
11. As a skill maintainer, I want the loop to fall back to modifying reference files (templates.md, quality-checklists.md) when SKILL.md changes alone don't improve the score, so that root causes in templates and checklists get fixed
12. As a skill maintainer, I want the loop to never touch scripts/ or executable files, so that code safety is maintained
13. As a skill maintainer, I want the loop to inject one new rule per iteration, so that each change is atomic and reversible

### Stopping Conditions

14. As a skill maintainer, I want the loop to stop when all assertions pass (perfect score), so that I know the skill is fully improved
15. As a skill maintainer, I want the loop to stop after 3 iterations without score improvement, so that it doesn't waste tokens on a plateau
16. As a skill maintainer, I want a hard cap of 10 iterations per skill, so that runaway loops are impossible
17. As a skill maintainer, I want to be able to interrupt the loop with Ctrl+C at any time, so that I retain manual control

### Batch Mode

18. As a skill maintainer, I want to run `/improve-skill --all` and have it improve all 29 skills sequentially, so that I can maintain my entire skill library in one overnight run
19. As a skill maintainer, I want to specify individual skills by name (`/improve-skill tdd debugging code-review`), so that I can target specific skills
20. As a skill maintainer, I want batch mode to create a single git branch (`improve/batch-YYYY-MM-DD`), so that all changes are reviewable in one PR
21. As a skill maintainer, I want single-skill mode to create its own branch (`improve/<skill-name>-YYYY-MM-DD`), so that I can review or discard per-skill
22. As a skill maintainer, I want git commits to follow the format `improve(<skill>): <change description> (score N→M)`, so that git log reads as an improvement history

### Re-runs and Persistence

23. As a skill maintainer, I want evals.json to persist between runs, so that benchmarks are comparable across sessions
24. As a skill maintainer, I want the tool to reuse existing evals.json on re-run, so that I don't lose eval refinement from previous improvement cycles
25. As a skill maintainer, I want a `--regen` flag to force regeneration of evals.json, so that I can refresh evals when the skill's rules change intentionally
26. As a skill maintainer, I want evals.json to live next to SKILL.md in the skill directory, so that it travels with the skill

### Reporting

27. As a skill maintainer, I want a phase-by-phase console output (setup → baseline → loop → report), so that I can monitor progress if I'm watching
28. As a skill maintainer, I want the final report to show per-assertion pass/fail at baseline and final, so that I can see exactly what improved
29. As a skill maintainer, I want the final report to list all git commits with change descriptions, so that I can review the diff in my IDE

## Implementation Decisions

### Module Architecture

Five deep modules, each with a clear interface:

**1. Eval Generator**
- Reads SKILL.md (and reference .md files) from a skill directory
- Extracts rules stated in the skill (imperatives, constraints, format requirements)
- Converts extractable rules into binary code-based assertions
- Detects skill archetype (file-processing vs prompt-based) from the skill's description and decision tree
- For file-processing skills: sets `test_input.type = "file"` with a path to the shortest matching real file from the knowledge base
- For prompt-based skills: sets `test_input.type = "prompt"` with a realistic prompt derived from the skill's description
- Skips rules that cannot be expressed as binary code checks (subjective quality, tone, "compelling")
- Writes evals.json to the skill directory

**2. Assertion Runner**
- Takes raw skill output (string) and evals.json
- Supports check types: `regex`, `not_regex`, `contains`, `not_contains`, `max_words`, `min_words`
- Returns structured result: `{total, passed: [{id, description}], failed: [{id, description, actual}]}`]
- Deterministic: same output + same evals = same result, always

**3. Skill Runner**
- Reads skill files (SKILL.md + all reference .md files) from the skill directory
- Constructs a sub-agent prompt that includes the skill's instructions as system context
- Sends the test input (file contents or prompt text) as the user message
- Captures the sub-agent's raw text output
- Returns the output string for assertion evaluation

**4. Improvement Loop**
- Core Karpathy cycle orchestrator
- Receives: skill directory, evals.json, baseline score
- Per iteration:
  1. Identify the first failing assertion
  2. Select target file: SKILL.md first (iterations 1-2), then reference files if SKILL.md changes plateau (iteration 3+)
  3. Inject one rule addressing the failure into the selected file
  4. Run skill + assertions → get new score
  5. If score improved: git commit (one file, one change, one commit)
  6. If score same or lower: git checkout to revert that one file
  7. Check stopping conditions: perfect score / 3 non-improving iterations / 10 max iterations
- Tracks iteration history for the report
- File selection priority for references: templates.md → quality-checklists.md → other .md files (by most-mentioned in SKILL.md)

**5. Batch Orchestrator**
- Handles `--all` mode and multi-skill invocation
- Creates the git branch (batch or per-skill)
- Iterates through skills sequentially (not parallel — each skill already uses sub-agents)
- Delegates to Eval Generator (if no evals.json) → Skill Runner → Assertion Runner → Improvement Loop per skill
- Aggregates individual reports into a batch summary
- Handles per-skill errors gracefully (one skill failure doesn't stop the batch)

### evals.json Schema

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

### Skill Archetype Detection

The Eval Generator classifies skills into archetypes based on the skill's description and content:

- **File-processing**: skill description mentions "file", "URL", "transcript", "video", "audio", "book", "document", or the skill has a decision tree with file input branches. Test input = path to real file.
- **Prompt-based**: all other skills. Test input = generated prompt text.

### Improvement Loop — Rule Injection Format

When injecting a rule into SKILL.md or a reference file, the loop appends to the appropriate section (or creates a new one):

- In SKILL.md: appended to an "Auto-Generated Quality Rules" section at the end
- In reference files: appended to the relevant existing section, or a new section if no match

Each injected rule includes a comment marking it as auto-generated:

```
<!-- improve-skill: iteration 3, assertion a04 -->
- Never use placeholder text like [SUMMARY] or [TODO].
<!-- /improve-skill -->
```

This makes auto-generated rules discoverable and removable.

### Git Strategy

- **Single skill**: `git checkout -b improve/<skill-name>-YYYY-MM-DD` before the loop
- **Batch**: `git checkout -b improve/batch-YYYY-MM-DD` before iterating
- **Commits**: `improve(<skill>): <rule description> (score N→M)` — one per iteration
- **Revert**: `git checkout -- <file>` to revert only the modified file, preserving other improvements

## Testing Decisions

### What makes a good test

- Test external behavior, not implementation details
- The Assertion Runner is the highest-value test target: given known input and known evals, the result must be deterministic
- The Eval Generator should be tested against real skills with known rules
- The Improvement Loop is harder to unit test (depends on sub-agents) — test with mocked skill runners

### Modules to test

**Assertion Runner** (highest priority):
- Test each check type: regex match, regex no-match, contains, not_contains, max_words, min_words
- Test edge cases: empty output, assertions with flags, assertions with special regex characters
- Test score calculation: all pass, all fail, mixed
- Test that the runner is deterministic (same input → same output, run 100 times)

**Eval Generator** (medium priority):
- Test against `video-knowledge-extraction` (complex, file-processing archetype)
- Test against `tdd` (simple, prompt-based archetype)
- Verify archetype detection correctness
- Verify that non-binary rules are skipped
- Verify evals.json output matches schema

**Skill Runner** (low priority — thin wrapper around sub-agent):
- Test that it correctly reads skill files and constructs the prompt
- Mock the sub-agent call and verify prompt construction

### Prior art

- The assertion check types (regex, word count) are similar to test patterns in the `tdd` skill
- The evals.json schema is inspired by Anthropic's Skill Creator eval format, simplified for code-only assertions

## Out of Scope

- **Layer 1 (activation improvement)**: improving skill YAML descriptions for better trigger rates. This is handled by Anthropic's built-in Skill Creator. May be added in v2.
- **LLM-as-judge assertions**: semantic checks that require LLM evaluation. Only code-based binary checks in v1.
- **Modification of scripts/**: Python scripts in skill directories are out of scope. They require a different QA process.
- **Human-in-the-loop breakpoints**: the loop is fully autonomous after invocation. No confirmation prompts during execution.
- **Multi-input benchmarks**: v1 uses a single fixed test input per skill. Multiple test inputs per skill is a v2 feature.
- **CI/CD integration**: running the improvement loop in CI is out of scope. It runs inside a Claude Code session.
- **Cost optimization**: the loop uses sub-agents within the Claude Code session. Token cost tracking and budget limits are not in v1.

## Further Notes

### Initial test transcript

The initial test input for file-processing skills is:
`/Users/CraSS/Documents/knowledge-base/videos/5-claude-code-skills-every-day/transcript.txt`

This will be expanded to a larger test corpus in future iterations.

### Relationship to Anthropic Skill Creator

The Anthropic Skill Creator already has a Layer 1 loop (description improvement) and an eval dashboard (manual QA). This tool complements it by adding Layer 2 (automated output quality improvement via binary assertions). The two systems do not conflict — Anthropic's tool improves *whether the skill fires*, this tool improves *what the skill produces*.

### Karpathy auto-research pattern

The improvement loop follows Andrej Karpathy's auto-research architecture:
1. `experiment.py` → the skill being tested (SKILL.md + references)
2. `eval_bpb` → the assertion score (pass rate out of total)
3. `program.py` → the improvement loop itself (change one thing, measure, keep or revert)

The key adaptation: instead of training a model, we're editing text instructions. The invariant is the same: atomic changes, binary metrics, git-based versioning.

### Risk: assertion quality

Auto-generated assertions can only be as good as the rules documented in SKILL.md. Skills with implicit rules (undocumented conventions) will have incomplete evals. This is acceptable for v1 because: (a) the improvement loop itself surfaces missing rules through assertion failures, and (b) users can manually add assertions to evals.json after auto-generation.
