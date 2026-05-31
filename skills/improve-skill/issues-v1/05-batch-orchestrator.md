# Issue 05: Batch orchestrator — `--all` and multi-skill invocation

## Type
AFK — extends the single-skill loop to handle multiple skills.

## Blocked by
- Issue 04 (Single-skill improvement loop)

## What to build

Build the orchestrator that handles running the improvement loop across multiple skills.

**Invocation modes:**

1. **Single skill**: `/improve-skill video-knowledge-extraction`
   - Creates branch: `improve/<skill-name>-YYYY-MM-DD`
   - Runs the single-skill loop

2. **Named list**: `/improve-skill tdd debugging code-review`
   - Creates branch: `improve/batch-YYYY-MM-DD`
   - Runs skills sequentially (not parallel — each skill already uses sub-agents)
   - Aggregates individual reports into batch summary

3. **All skills**: `/improve-skill --all`
   - Discovers all skills in both directories: `/Users/CraSS/Documents/Code_projects/agent-knowledge/skills/` and `/Users/CraSS/.claude/skills/`
   - Creates branch: `improve/batch-YYYY-MM-DD`
   - Runs all skills sequentially
   - Aggregates reports

**Error handling:**
- One skill failure doesn't stop the batch — log the error, continue to next skill
- Batch summary includes: skills improved, skills unchanged, skills failed

**Skill discovery for `--all`:**
- Scan both skill directories
- Skip `improve-skill` itself (don't improve the improver)
- Skip skills without a `SKILL.md` file
- Deduplicate (same skill name in both directories)

End-to-end: run on 2-3 skills with `--batch` or named list mode, verify independent git commits per skill and aggregated batch report.

## Acceptance criteria

- [ ] Handles single-skill invocation: creates per-skill branch, runs loop
- [ ] Handles named list invocation: creates batch branch, runs skills sequentially
- [ ] Handles `--all` invocation: discovers all skills in both directories, deduplicates, skips self
- [ ] Sequential execution (no parallel) — each skill gets full context window
- [ ] Per-skill error isolation: one failure doesn't stop the batch
- [ ] Git branch naming: single = `improve/<skill>-YYYY-MM-DD`, batch = `improve/batch-YYYY-MM-DD`
- [ ] Batch summary includes: per-skill results (improved/unchanged/failed), total time, total iterations
- [ ] Skill discovery scans both directories correctly
- [ ] End-to-end: run on 2 skills, verify git history has commits for each, report aggregates correctly

## Notes for the agent

- This is the entry point that the SKILL.md will invoke.
- The orchestrator itself doesn't implement the loop — it delegates to the improvement loop module from Issue 04.
- Place at `improve-skill/lib/batch-orchestrator.{js/py}`.
- Consider how to pass arguments: the skill will be invoked via `/improve-skill <args>` — parse args to determine mode.
