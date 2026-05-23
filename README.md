# Agent Knowledge

A single source of truth for AI agent knowledge — coding standards, workflow skills, product management conventions, and research methodologies.

## Structure

```
agent-knowledge/
├── AGENTS.md              # Root router — agents read this first
├── CLAUDE.md              # Instructions for Claude Code
├── link.sh                # Connect skills to agents via symlinks
├── standards/             # Detailed conventions, loaded by context match
│   ├── python/
│   ├── typescript/
│   ├── go/
│   ├── devops/
│   ├── product/
│   └── management/
├── skills/                # Repeatable processes, loaded on demand
│   ├── tdd/
│   ├── debugging/
│   ├── code-review/
│   ├── deploy-checklist/
│   ├── incident-response/
│   ├── spec-writing/
│   └── competitive-analysis/
└── templates/             # Reusable templates
```

## Architecture

Knowledge is organized in three layers:

| Layer | Purpose | When loaded |
|-------|---------|-------------|
| **AGENTS.md** | Root router with trigger tables | Always (first file read) |
| **Standards** | Detailed conventions by file type/keyword | When matching files are edited |
| **Skills** | Repeatable processes with scripts/references | When the task calls for it |

### Progressive Disclosure

- **Tier 1** — `_INDEX.md` catalogs (~50-100 tokens per entry). Agents scan these to decide what to load.
- **Tier 2** — `SKILL.md` instructions (up to 500 lines). The actual guidance.
- **Tier 3** — `references/` and `scripts/` subfolders. Loaded only when the skill references them.

## Setup

```bash
# Clone
git clone https://github.com/crass987/agent-knowledge.git ~/Documents/Code_projects/agent-knowledge
cd ~/Documents/Code_projects/agent-knowledge

# Connect to Claude Code
chmod +x link.sh
./link.sh

# Disconnect
./link.sh --unlink
```

## Adding new content

### New skill
1. Create `skills/<name>/SKILL.md` with YAML frontmatter
2. Add scripts to `skills/<name>/scripts/` if needed
3. Add references to `skills/<name>/references/` if needed
4. Update `AGENTS.md` router table

### New standard
1. Create `standards/<category>/<name>/SKILL.md`
2. Add or update `standards/<category>/_INDEX.md`
3. If new category — add entry in `AGENTS.md` standards table

### Conventions
- Each `SKILL.md` starts with YAML frontmatter (`name`, `description`)
- Keep `SKILL.md` under 500 lines; move details to `references/`
- `_INDEX.md` files contain trigger tables (file patterns + keywords)
- Scripts go in `scripts/` subfolder within the skill directory
- All edits and commits happen in THIS repo — never in project repos

## Connecting to projects

In a project's `.gitignore`, add:
```
.claude/skills
```

To make `AGENTS.md` available in a project:
```bash
ln -s ~/Documents/Code_projects/agent-knowledge/AGENTS.md <project-root>/AGENTS.md
```

## License

MIT
