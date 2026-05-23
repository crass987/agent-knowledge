# Agent Knowledge — Instructions for Claude Code

## Repository purpose

This repo contains reusable standards and skills for AI agents.
It lives at `~/Documents/Code_projects/agent-knowledge/`.

## Editing rules

- When editing skills or standards — edit files HERE, in this repo.
- When creating new skills — write them in `skills/<name>/SKILL.md`.
- When creating new standards — write them in `standards/<category>/<name>/SKILL.md`.
- When creating a new category — add a `_INDEX.md` in the category folder.
- After adding a new skill or standard — update `AGENTS.md` router table.

## Git workflow

- All commits go to THIS repo (`~/Documents/Code_projects/agent-knowledge/`).
- Do NOT commit agent knowledge files into other projects' repos.
- Symlinks in other projects point here — they should be in `.gitignore` of those projects.

## Symlinks

Skills are connected to Claude Code via symlinks:
- `~/.claude/skills/` → may contain symlinks pointing to skills in this repo
- Other agents can be connected similarly via `link.sh`

## File conventions

- Each SKILL.md starts with YAML frontmatter (name, description)
- Body is free-form Markdown instructions
- Keep SKILL.md under 500 lines; move details to `references/` subfolder
- _INDEX.md files contain trigger tables (file match patterns + keywords)
- Scripts go in `scripts/` subfolder within the skill directory
