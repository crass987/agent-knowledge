# Repo Profiles Refresh Instructions

Follow these steps in order.

## Step 1: Sync repos and collect facts

```bash
./sync-repos.sh --force
./meta/scripts/collect-repo-facts.sh
```

`sync-repos.sh --force` brings all repos to server state (correct branch, latest commits).
After completion, a facts report will be at `meta/reports/facts-YYYY-MM-DD.md` (today's date).

## Step 2: Read the report and fix profiles

Read the generated facts report. For each repo listed, compare the collected facts against `meta/repos/<name>.md`. Fix mismatches in these sections:
- **Commands** — new/removed Makefile targets or npm scripts
- **Tech Stack** — changed dependencies (go.mod, package.json, pyproject.toml)
- **Project Structure** — new/removed directories and packages
- **Cross-Repo Context** — new dependencies between services

Priority focus:
1. Repos with HIGH drift (>50 commits since last refresh) — check project structure first
2. Repos with MEDIUM drift (10-50 commits) — check for package renames, new dirs
3. Repos with LOW drift (<10 commits) — usually just version bumps, quick scan

Flag uncertain changes with `[REVIEW]` — do not guess.

## Step 3: Commit and push to meta-repo

All changes go to the meta-repo only:
- Commit updated profile files in `meta/repos/`
- Commit any updated meta docs
- Push to main

## Step 4: Write summary report

Write a summary to `meta/reports/refresh-summary-YYYY-MM-DD.md` with three sections:
- **Changes Applied** — table of what was fixed
- **Cross-Reference Updates** — changes to other meta/ docs
- **Needs Review** — items flagged with [REVIEW] that need human eyes

## Rules

**CRITICAL: You MUST ONLY modify documentation files in the meta-repo (meta/repos/*.md, files under meta/reports/, AGENTS.md). NEVER modify any files in the service repositories. This is a read-only operation on all service code — your write scope is strictly limited to .md files in the meta-repo.**
