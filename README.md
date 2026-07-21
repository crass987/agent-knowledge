# Agent Knowledge

A single source of truth for AI agent knowledge — coding standards, workflow skills, product management conventions, and research methodologies.

Короткая инструкция по пользованию: **[USAGE.md](USAGE.md)**.

## Structure

```
agent-knowledge/
├── AGENTS.md              # Root router: Standards + Skills (by track) + Tool registry
├── USAGE.md               # Как пользоваться харнессом (RU)
├── CLAUDE.md              # Instructions for Claude Code
├── link.sh                # Deploy skills into agents via symlinks
├── skills/                # Skills, grouped by track (see skills/_INDEX.md)
├── standards/             # Coding conventions by language/domain (python, ts, go, devops, product, management)
├── learnings/             # Operational-knowledge store (patterns / pitfalls / preferences / operational)
├── decisions/             # Settled-calls store (decisions.active.md + supersede)
├── state/                 # Local runtime telemetry (skill-runs.md; data gitignored)
├── scripts/               # Harness tooling: lint-portability, auto-retrieve, rotate-skill-runs
├── tests/                 # pytest for the harness scripts
├── docs/                  # Specs, plans, grills (harness-improvement docs)
└── templates/             # Reusable templates
```

**Skills are grouped by track** (the Discovery–Delivery split):

- **Discovery** — what to build (research / evaluate / spec): `am-research`, `am-research-index`, `am-grill-feature`, `am-grill-docs`, `am-pain-mining`, `am-write-specs`, `jtbd`, `grill-plan`, `book/video-knowledge-extraction`.
- **Delivery** — how to build (code): `tdd`, `debugging`, `code-review`.
- **Knowledge-Meta** — the harness knowledge layer: `improve-skill`, `decisions`, `prune`.

Full router with triggers: `AGENTS.md` and `skills/_INDEX.md`.

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

## Harness knowledge layer

The harness learns across sessions. Three local-only stores + a footer + a linter:

- `learnings/` — operational facts (patterns / pitfalls / preferences / operational), frontmatter entries. Separate from reflexive `memory/`. See `learnings/README.md`.
- `state/skill-runs.md` — local skill-run telemetry (skill / duration / outcome). Format in `state/README.md`; the data file is gitignored (local-only).
- `skills/_shared/learning-footer.md` — standard footer appended to operational skills; tells the agent to capture a learning + log the run.
- `AGENTS.md` tool-registry — capability → concrete tool. Skills reference capabilities, never hardcoded tool-names.
- `scripts/lint-portability.py` — CI gate. Rejects hardcoded `mcp__*` inside `SKILL.md`. Run: `python3 scripts/lint-portability.py skills`.

Rollout: footer is on 11 operational skills (all am-*, debugging, book/video-knowledge-extraction). Skipped — no recurring operational facts: code-review, tdd, jtbd, improve-skill. (Removed as generic overhead 2026-07-21: competitive-analysis, spec-writing, deploy-checklist, incident-response.) **P1 shipped:** `decisions/` store + `decisions` skill (log/search/supersede) + OIAE mapping in `improve-skill`. **P2 shipped:** `prune` (stale+contradiction cleanup), selective `scripts/auto-retrieve.py` (≤3, never wholesale), `scripts/rotate-skill-runs.sh`; regression evals via `improve-skill`'s per-skill `evals.json`. See `docs/superpowers/specs/2026-06-18-harness-improvement-prd.md` and `USAGE.md`.

## License

MIT
