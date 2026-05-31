# Issue 07: SKILL.md + skill registration — make it invocable as `/improve-skill`

## Type
HITL — requires human review of description wording and trigger behavior.

## Blocked by
- Issue 04 (Improvement Loop)
- Issue 05 (Batch Orchestrator)
- Issue 06 (Reporting)

## What to build

Write the `SKILL.md` for `improve-skill` itself — the YAML frontmatter + instructions that make it invocable as a Claude Code skill.

**SKILL.md must include:**
- `name`: `improve-skill`
- `description`: clear trigger description that fires when user says "improve this skill", "run improve-skill", "improve all skills"
- Instructions for the skill itself: how to parse args, which modules to call, what to output

**Registration:**
- Place `SKILL.md` at `/Users/CraSS/Documents/Code_projects/agent-knowledge/skills/improve-skill/SKILL.md`
- The skill is already discovered from the directory — no additional registration needed for Claude Code

**The description must trigger on:**
- `/improve-skill <skill-name>`
- `/improve-skill --all`
- `/improve-skill tdd debugging code-review`
- "improve the tdd skill"
- "auto-improve my skills"

But NOT on:
- General code improvement requests
- "improve this code"
- Skill writing/creation requests (that's `write-a-skill`)

## Acceptance criteria

- [ ] SKILL.md written with correct YAML frontmatter (name, description, trigger phrases)
- [ ] Description triggers on skill improvement requests but NOT on general code improvement
- [ ] Instructions reference the correct module paths from previous issues
- [ ] Skill is invocable as `/improve-skill` in Claude Code
- [ ] Human has reviewed and approved the description wording

## Notes for the agent

- This is HITL because the description wording directly affects whether the skill fires correctly. Poor descriptions = wrong triggers.
- Study existing skill descriptions in the skill directories for conventions.
- The SKILL.md instructions should be concise — they just orchestrate the modules, not reimplement them.
- Look at `write-a-skill/SKILL.md` or `tdd/SKILL.md` for style reference.
