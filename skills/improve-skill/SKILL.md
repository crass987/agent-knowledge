---
name: improve-skill
description: Use when the user wants to improve a Claude Code skill's output quality — "improve the tdd skill", "improve-skill video-knowledge-extraction", "auto-improve my skills", "improve all skills", "run improve-skill on X". Triggers on skill improvement and skill quality requests. Does NOT trigger on general code improvement ("improve this code") or skill writing ("write a skill").
---

# improve-skill — Autonomous Skill Improvement

Improve a skill's output quality using a Karpathy-style loop: change → test → keep or revert.

## When to Use

- User says "improve the X skill" or "/improve-skill X"
- User says "improve all skills" or "/improve-skill --all"
- User says "auto-improve my skills"
- User wants to systematically verify or improve skill output quality

## When NOT to Use

- General code improvement requests ("improve this code", "refactor this function")
- Writing a new skill from scratch (that's `/write-a-skill`)
- Editing skill descriptions (that's Anthropic's Skill Creator)

## Invocation Modes

```
/improve-skill <skill-name>           # Single skill
/improve-skill tdd debugging          # Named list
/improve-skill --all                  # All skills
/improve-skill --regen <skill-name>   # Force regenerate evals.json
```

## Instructions

1. **Parse arguments** to determine mode (single, batch, all) using `lib/batch_orchestrator.py:parse_args()`

2. **Discover skills** (if --all) using `lib/batch_orchestrator.py:discover_skills()`

3. **For each skill**, run the improvement pipeline:
   - Generate or load `evals.json` → `lib/eval_generator.py`
   - Run skill, score output → `lib/skill_runner.py` + `lib/assertion_runner.py`
   - Loop: inject rule → re-run → score → commit or revert → `lib/improvement_loop.py`
   - Print phase-by-phase progress → `lib/reporter.py`

4. **Print final report** with per-assertion comparison and git commit history

5. **For batch mode**, aggregate results into a summary showing improved/unchanged/failed per skill

## Architecture

```
lib/
├── assertion_runner.py    # Pure eval engine: text + assertions → pass/fail
├── eval_generator.py      # SKILL.md → evals.json (auto-generate assertions)
├── skill_runner.py        # Execute skill, capture output
├── improvement_loop.py    # Karpathy cycle: change → test → keep/revert
├── batch_orchestrator.py  # Multi-skill orchestration (--all, named list)
└── reporter.py            # Phase output + final report
```

## Safety

- Every change is committed atomically to a git branch (`improve/<skill>-YYYY-MM-DD`)
- Regressions are automatically reverted (`git checkout -- <file>`)
- Scripts/ and executable files are never modified
- One change per iteration — fully traceable
- Hard cap of 10 iterations per skill

## Output

Console output follows 4 phases:
1. **SETUP** — skill name, archetype, assertions, test input
2. **BASELINE** — initial score, failing assertions
3. **LOOP** — per-iteration: target file, rule, score delta, action
4. **REPORT** — baseline→final, per-assertion comparison, git commits
