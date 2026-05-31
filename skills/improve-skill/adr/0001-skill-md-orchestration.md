# ADR 0001: SKILL.md orchestration over full Python pipeline

## Status

Accepted

## Context

v1 of improve-skill was implemented as 6 Python modules (`assertion_runner.py`, `eval_generator.py`, `skill_runner.py`, `improvement_loop.py`, `batch_orchestrator.py`, `reporter.py`) that orchestrate the entire improvement loop. Sub-agent execution was done via `subprocess.run(["claude", "--print", ...])`.

The tool runs inside Claude Code sessions. All reasoning (diagnosis, rule generation, file targeting) is LLM work. The Python modules were wrapping LLM reasoning in procedural code — writing templates for rule injection, hardcoding file priority, and shelling out to `claude --print` for skill execution.

## Decision

Split the architecture: Python only for deterministic evaluation, SKILL.md instructions for all reasoning and orchestration.

**Python (keep):**
- `assertion_runner.py` — deterministic eval engine (regex, contains, word count). Must be testable with pytest.
- `eval_generator.py` — hybrid eval generation (heuristic + LLM call). Writes evals.json.

**SKILL.md (new):**
- Improvement loop (diagnosis, rule generation, file targeting)
- Batch orchestration (multi-skill invocation)
- Skill execution (uses native Claude Code Agent tool instead of `claude --print`)
- Reporting (phase-by-phase console output)

**Delete:**
- `improvement_loop.py`, `batch_orchestrator.py`, `skill_runner.py`, `reporter.py`

## Rationale

### Why Python for eval engine

Assertion scoring must be deterministic — same input + same evals = same result, always. This is non-negotiable for the improvement loop to work (the keep/revert decision depends on reproducible scores). Python with pytest gives us this guarantee. A SKILL.md instruction that says "check if the output matches this regex" is inherently less reliable than code that literally runs `re.search()`.

### Why SKILL.md for reasoning

The improvement loop's core work is reasoning:
- "Why did assertion a04 fail?" → needs to read the output, understand the skill's intent, and identify the gap
- "Which file should I modify?" → needs to trace the failure to SKILL.md vs a template vs a checklist
- "What rule should I write?" → needs to understand the skill's language, style, and conventions
- "Where in the file should it go?" → needs to understand the file's section structure

Writing Python to orchestrate LLM reasoning is indirect: Python generates prompts, parses responses, handles edge cases. When the LLM is already the runtime environment (Claude Code), this indirection adds complexity without benefit. SKILL.md instructions execute directly as LLM reasoning — no prompt engineering layer, no response parsing, no error handling for malformed LLM output.

The native Agent tool is also strictly better than `claude --print`: it shares the session context, has access to all MCP tools, and doesn't require the `claude` CLI to be installed.

### Why not keep both

The four deleted modules would drift. They duplicate what SKILL.md does natively, and maintaining two orchestration paths (Python CLI + SKILL.md) doubles the surface area for bugs. The Python modules would become dead code that looks maintained but isn't.

## Consequences

### Positive
- LLM reasoning is first-class (native tool access, shared context, no subprocess overhead)
- Simpler codebase (2 Python files + 1 SKILL.md instead of 6 Python files + 1 SKILL.md)
- No dependency on `claude` CLI being installed
- Rule generation quality improves dramatically (LLM writes rules directly instead of templates)
- File targeting is intelligent (source_file tracing + LLM diagnosis instead of hardcoded priority)

### Negative
- Cannot run the improvement loop outside Claude Code (Python modules were CLI-runnable)
- No pytest coverage for the reasoning loop (only the eval engine is testable with pytest)
- SKILL.md instructions are less precise than Python code (the LLM may interpret them differently across sessions)
- Debugging the loop requires reading Claude Code conversation logs instead of Python stack traces

### Mitigations
- The `--dry-run` flag provides a preview mode for testing without side effects
- Deterministic eval engine catches most regressions before they're committed
- Git-based revert provides a safety net for any bad changes
- The assertion runner's 27 tests remain the highest-value test target

## Alternatives Considered

### Full Python (v1 approach)
Keeps CLI portability and pytest coverage. But wrapping LLM reasoning in Python adds complexity without improving reliability — the LLM calls are already non-deterministic, so pytest can only test the scaffolding, not the reasoning quality.

### Full SKILL.md (no Python at all)
Simplest architecture. But assertion scoring must be deterministic for the keep/revert decision to be reliable. LLM-based scoring introduces non-determinism into the loop's core mechanic, making it possible for the same change to be accepted in one run and reverted in the next.

### Hybrid with Python orchestrator + LLM sub-agents
Keep Python as the orchestrator but use Agent tool for LLM calls. This was the initial v2 proposal — it preserves pytest for orchestration logic while using native Agent for skill execution. Rejected because the orchestration logic (file targeting, stopping conditions, git operations) is trivially expressible in SKILL.md and doesn't benefit from Python's type safety.
