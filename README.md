# Agent Knowledge

A single source of truth for AI agent knowledge — coding standards, workflow skills, product management conventions, and research methodologies.

Короткая инструкция по пользованию: **[USAGE.md](USAGE.md)**.

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
│   ├── competitive-analysis/
│   └── book-knowledge-extraction/
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
- **Tier 2** — `SKILL.md` instructions. The actual guidance. Keep whole for workflow skills; split only reference-type content.
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
- Keep `SKILL.md` self-contained. Move only truly optional content (templates, examples) to `references/`
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

## Harness: operational learning loop (P0)

The harness learns across sessions. Three local-only stores + a footer + a linter:

- `learnings/` — operational facts (patterns / pitfalls / preferences / operational), frontmatter entries. Separate from reflexive `memory/`. See `learnings/README.md`.
- `state/skill-runs.md` — local skill-run telemetry (skill / duration / outcome). Format in `state/README.md`; the data file is gitignored (local-only).
- `skills/_shared/learning-footer.md` — standard footer appended to operational skills; tells the agent to capture a learning + log the run.
- `AGENTS.md` tool-registry — capability → concrete tool. Skills reference capabilities, never hardcoded tool-names.
- `scripts/lint-portability.py` — CI gate. Rejects hardcoded `mcp__*` inside `SKILL.md`. Run: `python3 scripts/lint-portability.py skills`.

Rollout: footer is on 14 operational skills (all am-*, deploy-checklist, debugging, incident-response, book/video-knowledge-extraction, spec-writing). Skipped — no recurring operational facts: code-review, competitive-analysis, tdd, jbtd, improve-skill. **P1 shipped:** `decisions/` store + `am-decisions` skill (log/search/supersede) + OIAE mapping in `improve-skill`. **P2 shipped:** `am-prune` (stale+contradiction cleanup), selective `scripts/auto-retrieve.py` (≤3, never wholesale), `scripts/rotate-skill-runs.sh`; regression evals via `improve-skill`'s per-skill `evals.json`. See `docs/superpowers/specs/2026-06-18-harness-improvement-prd.md` and `USAGE.md`.

## License

MIT
