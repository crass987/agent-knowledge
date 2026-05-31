# Issue 04: Single-skill improvement loop — Karpathy cycle

## Type
AFK — requires all three foundation modules.

## Blocked by
- Issue 01 (Assertion Runner)
- Issue 02 (Eval Generator)
- Issue 03 (Skill Runner)

## What to build

Wire everything into the core autonomous improvement loop. This is the heart of the tool — the Karpathy-style "change → test → keep or revert" cycle.

**Loop flow per iteration:**

1. Identify the first failing assertion (from Assertion Runner result)
2. Select target file:
   - Iterations 1-2: always `SKILL.md`
   - Iterations 3+: fall back to reference files if SKILL.md changes plateau
   - Reference priority: `templates.md` → `quality-checklists.md` → other `.md` files (by most-mentioned in SKILL.md)
3. Inject one rule addressing the failure into the selected file
4. Run Skill Runner → capture output
5. Run Assertion Runner → get new score
6. If score improved: `git commit` (one file, one change, one commit)
   - Commit format: `improve(<skill>): <change description> (score N→M)`
7. If score same or lower: `git checkout -- <file>` to revert only that one file
8. Check stopping conditions:
   - **Perfect score**: all assertions pass → stop, report success
   - **Plateau**: 3 consecutive iterations with no score improvement → stop
   - **Hard cap**: 10 iterations max → stop

**Git strategy:**
- Before loop starts: `git checkout -b improve/<skill-name>-YYYY-MM-DD`
- Commits: one per iteration that improved score
- Reverts: `git checkout -- <file>` (only the modified file, preserving other improvements)

**Rule injection format:**
```
<!-- improve-skill: iteration N, assertion aXX -->
- <the new rule text>
<!-- /improve-skill -->
```

- In SKILL.md: append to an "Auto-Generated Quality Rules" section at the end (create section if needed)
- In reference files: append to relevant existing section, or new section if no match

**Safety constraints:**
- Never touch `scripts/` or executable files
- Exactly one change to exactly one file per iteration
- Loop is interruptible (Ctrl+C at any time)

End-to-end: run the full loop on one real skill (e.g., `tdd`) and observe:
- Baseline score is recorded
- Loop converges or hits stopping condition
- Git history shows atomic commits with correct format
- Final report shows baseline → final score

## Acceptance criteria

- [ ] Loop orchestrates: Eval Generator → Skill Runner → Assertion Runner → improvement → re-score
- [ ] Creates git branch `improve/<skill-name>-YYYY-MM-DD` before starting
- [ ] Each iteration modifies exactly one file with exactly one rule injection
- [ ] Rule injection uses the `<!-- improve-skill -->` marker format
- [ ] Improved score → git commit with format `improve(<skill>): <description> (score N→M)`
- [ ] No improvement → `git checkout -- <file>` reverts only the modified file
- [ ] Stops on perfect score (all assertions pass)
- [ ] Stops after 3 consecutive non-improving iterations
- [ ] Hard cap at 10 iterations
- [ ] Never modifies files in `scripts/`
- [ ] File selection: SKILL.md for iterations 1-2, references for 3+ (with correct priority)
- [ ] End-to-end: run on `tdd` skill — observe baseline, iterations, git commits, final score
- [ ] Tracks iteration history for the report (each iteration: target file, rule injected, score before/after)

## Notes for the agent

- This is the most complex module. It orchestrates all others.
- The "improvement" step (identifying what rule to inject) requires LLM reasoning — the loop itself calls an LLM to analyze the failing assertion and generate a candidate rule.
- Git operations must be resilient: check for dirty working tree before starting, handle merge conflicts (shouldn't happen on a fresh branch, but be defensive).
- Place at `improve-skill/lib/improvement-loop.{js/py}`.
- The loop should print phase-by-phase progress to console so the user can monitor if watching.
