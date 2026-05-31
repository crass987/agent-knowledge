# Issue 02: Single-Skill Improvement MVP

## Type
AFK — can start immediately after issue 01 completes.

## Blocked by
- Issue 01 (Hybrid Eval Engine v2)

## What to build

Write the new `SKILL.md` that orchestrates the complete improve-skill v2 workflow for a **single skill**. This is the tracer bullet — the thinnest path that delivers the full value: evaluate a skill, find weaknesses, generate rules, inject them, and commit improvements.

The SKILL.md implements phases 1–3 of the PRD-v2 workflow:
- **Phase 1 (Setup)**: Parse args (skill name), discover skill directory, create git branch, read all skill files, run eval generator if evals.json doesn't exist.
- **Phase 2 (Baseline)**: Execute the skill via native Agent tool on all test_inputs, score outputs via `assertion_runner.py`, display aggregated baseline score.
- **Phase 3 (Improvement Loop)**: Iterate up to 10 times — diagnose first failing assertion, target the right file (source_file from evals.json → LLM diagnosis fallback), generate rule via LLM, inject via Edit tool, re-score, commit or revert, check stopping conditions.

### What's in scope
- `/improve-skill <skill-name>` invocation (single skill only)
- Source-file targeting: primary from evals.json, fallback LLM diagnosis, last resort SKILL.md
- Rule injection with `<!-- improve-skill: iteration N, assertion aXX -->` markers
- Git: branch `improve/<skill>-YYYY-MM-DD`, atomic commits, `git checkout -- <file>` reverts
- Stopping: all pass, 3-iteration plateau, 10-iteration cap
- Cost awareness: display cumulative agent/LLM call counts per iteration

### What's NOT in scope
- `--all` batch mode (issue 04)
- `--dry-run` flag (issue 04)
- `--regen` flag (issue 04)
- Named list invocation (issue 04)
- Quality audit phase 4 (issue 03)
- Structured final report phase 5 (issue 03)
- Crash recovery (issue 04)

## Acceptance criteria

- [ ] SKILL.md frontmatter with name, description, trigger phrases
- [ ] Phase 1: arg parsing, skill directory discovery, git branch creation, eval generation
- [ ] Phase 2: Agent tool execution on each test_input, assertion_runner.py scoring, baseline display
- [ ] Phase 3a: Diagnose — identify first failing assertion, resolve target file via source_file / LLM diagnosis
- [ ] Phase 3b: Generate — LLM returns rule text, target section, insertion position
- [ ] Phase 3c: Inject — Edit tool with marker format, atomic single-file change
- [ ] Phase 3d: Re-score — re-run skill via Agent on all test_inputs, score, compare
- [ ] Phase 3e: Decide — commit if improved, revert if same/lower
- [ ] Phase 3f: Stop check — all pass / 3 plateau / 10 cap
- [ ] End-to-end: `/improve-skill code-review` runs through all phases and produces git commits
- [ ] Safety: only `*.md` files and `evals.json` are edited, never `*.py` or `*.sh`

## Notes for the agent

- This is the biggest issue. The SKILL.md should be self-contained — all reasoning instructions live here, not in Python.
- Use native Claude Code tools: Agent (skill execution), Read (file reading), Edit (rule injection), Bash (git operations, assertion_runner.py execution).
- The Agent tool call for skill execution should pass the test_input as the prompt or file to process.
- assertion_runner.py is invoked via Bash: `python lib/assertion_runner.py <evals_path> <output_path>`.
- Rule generation prompt should include: the failing assertion, the skill output snippet, the target file content. Ask the LLM to return: rule text (in skill's language/style), target section name, insertion position (before/after specific heading).
