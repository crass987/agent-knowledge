# Issue 04: Batch Mode, Flags & Recovery

## Type
AFK — no human interaction needed.

## Blocked by
- Issue 02 (Single-Skill Improvement MVP)

## What to build

Expand the SKILL.md to support batch invocation, CLI flags, and crash recovery.

### Batch mode (`--all` and named lists)
- `--all`: discover all skills in both skill directories, run improvement on each
- Named list: `/improve-skill tdd debugging` — run on specific skills
- Error isolation: if one skill fails, continue with others. Report which failed.
- Per-skill git branches (not one shared branch for batch)

### Flags
- `--regen`: force regeneration of evals.json even if it already exists
- `--dry-run`: run all phases (setup, baseline, diagnosis, rule generation) but do NOT execute any Edit/Write operations, create git commits, or modify files. Display what *would* happen.

### Crash recovery
- On restart: read last N git commits to understand what was tried
- Re-score to get fresh baseline
- Continue loop from where it left off
- No checkpoint files — recovery is git-based

### Cost awareness
- After each iteration: display cumulative agent calls, LLM calls, test inputs evaluated
- No budget enforcement — stopping conditions (10 cap + 3 plateau) bound worst case

## Acceptance criteria

- [ ] `--all` discovers and processes all skills in both directories
- [ ] Named list (`/improve-skill tdd debugging`) processes specified skills
- [ ] Error isolation: one skill failure doesn't stop the batch
- [ ] `--regen` forces eval regeneration, overwriting existing evals.json
- [ ] `--dry-run` shows full phase output without any file modifications
- [ ] `--dry-run` displays generated rules and target files without injecting
- [ ] Crash recovery: re-read git history on restart, re-score baseline, continue
- [ ] Cost display after each iteration (agent calls, LLM calls, inputs evaluated)
- [ ] Per-skill git branches in batch mode
