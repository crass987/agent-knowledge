---
name: am-release-notes
description: Use when generating Astra Monitoring **release notes** for a release — «напиши релиз-нотс», «релиз-заметки», «release notes for vX», «changelog релиза», «что нового в релизе». Pulls completed issues from Jira fixVersion and produces the **three files** (dev / changelog / marketing) in analytics-hub, with infostyle-critic on marketing.
---

# AM Release Notes

Generate **release notes** for an Astra Monitoring release (format `v.X.Y.0`). Output
is the **three files** — dev, changelog, marketing — in
`analytics-hub/internal_docs/docs/release-notes/`, dated by release date (`YYYY-MM-DD-…`).
Source data: Jira project **MON**, `fixVersion`.

Leading words: **release notes**, **три файла** (dev / changelog / marketing).

## When to use

- A release is shipping → write its release notes.
- «напиши релиз-нотс/релиз-заметки для vX», «release notes for X», «changelog релиза», «что нового в релизе».

## When NOT to use

- Editing one existing file, no Jira pull → edit it directly + `infostyle`.
- Publishing to Confluence → `am-md-to-confluence`.
- Public changelog in the `docs` repo (`docs/source/changelog.md`) → that is a **manual copy** of the changelog section, see step 7.

## Source of truth

- **Process:** this skill is authoritative. The legacy `analytics-hub/internal_docs/docs/release-notes/HOWTO-generate.md` keeps the epic→section table but has **stale paths** (`docs/release-notes/` → actually `internal_docs/docs/release-notes/`) and a board-id step you no longer need (`fixVersion` replaces it).
- **Templates:** the latest `YYYY-MM-DD-*` files in the same folder — read the previous release as your structural model.
- **Feature context:** `Astra/PM.md` (Knowledge Map, Glossary) for flagship descriptions.

## Process

### 1. Identify the version

`mcp__jira__list_project_versions(project_key="MON")` → pick `v.X.Y.0`. Confirm with the user which version, and the **release date** (for the filename); if unknown, use a placeholder date and flag it.

Gotcha — **version duplicates.** MON carries errant twin versions without the `v.` prefix (e.g. `1.5.0` alongside `v.1.5.0`). Use the **`v.`-prefixed** one.

**Done when:** version id known; it is the `v.`-prefixed `v.X.Y.0` for the release actually shipping; filename date agreed (or placeholder + flag).

### 2. Pull completed issues to a file

```
mcp__jira__search_issues(
  jql='fixVersion = "v.X.Y.0" AND statusCategory = Done ORDER BY updated DESC',
  max_results=200,
  fields=["summary","status","issuetype","labels","components","customfield_10300"])
```

Gotcha — **the result is huge** (~1.5 KB/issue; 150 issues ≈ 250 KB). The tool auto-saves it to a file when it overflows. **Reduce it with jq before any of it enters your context** — never read the raw file whole. Work from the saved path with the jq recipes in `reference.md`.

Gotcha — **Cancelled lives inside `statusCategory = Done`** in this Jira. Drop every issue with `status.name == "Cancelled"`. They did not ship.

**Done when:** Done issues are on disk; Cancelled excluded; you know the shipping count (`total` minus cancelled).

### 3. Aggregate, resolve epics, group, pick flagships

From the saved file (jq recipes in `reference.md`): count by status / issuetype / epic, then resolve epic names with `mcp__jira__batch_get_issues` on the unique epic keys. Group issues by epic + summary.

Identify the **flagships** (the marketing «Ключевые возможности»): the epics with the most issues + product judgment (a new section, a platform-wide capability, a brand-new tool). Cross-check flagship candidates against `Astra/PM.md`.

**Done when:** every shipping issue belongs to a named group; 3–5 flagships named; Testing epic (`MON-3485`) identified and quarantined (dev-file only).

### 4. Write the three files

Full templates + the epic→section map are in `reference.md`. Short form:

- **`YYYY-MM-DD-release-notes-dev.md`** — `Added / Changed / Fixed / Security / Testing / Known Issues / Breaking Changes`. **Every shipping issue appears, with a Jira link, exactly once.** Includes Testing and infra.
- **`YYYY-MM-DD-changelog.md`** — `# Изменения` → `## X.Y.Z` → `Новые возможности / Изменения / Bug fixes / Исправления безопасности`. **No Jira links.** Exclude Testing epic, infra-internal, research. Style mirrors `docs/source/changelog.md` (NOT Keep a Changelog).
- **`YYYY-MM-DD-release-notes-marketing.md`** — `Что нового / Ключевые возможности / Улучшения / Безопасность / Исправления / Итоги`. User value, telegraph density. Written in infostyle (basis: `_shared/infostyle-core.md`).

Gotcha — **user-facing naming.** Write **«Сервис авторизации»**, not «DEX». **amctl is a CLI** (not «управление по API») that an AI agent can drive (`-f json`, separate amctl skill exists). Adjust other internal tech names to product names likewise.

Gotcha — **don't accent raw features.** A half-baked capability (e.g. a first-pass audit log) goes in «Улучшения» as a modest line, not in «Ключевые возможности».

**Done when:** three files written with the per-file rules above satisfied.

### 5. Verify the dev file (mandatory)

Every shipping issue key must appear **exactly once** in the dev file. Run the key-coverage check in `reference.md` (jq extract vs. expected keys): missing, extra, and duplicate (count ≠ 2 = prefix + URL) lists must all be empty.

**Done when:** key-coverage check passes — no missing, no extra, no duplicates.

### 6. infostyle-critic on marketing (mandatory gate)

Dispatch a fresh `infostyle-critic` subagent on the marketing file. Apply its fixes, re-run until it returns **ЖИВОЙ** (a Stop hook in the harness blocks delivery otherwise). The dev and changelog files are reference-grade — no critic needed.

**Done when:** critic verdict ЖИВОЙ on the current marketing text (or the user explicitly accepts НА ГРАНИ).

### 7. Commit + push (analytics-hub dev only)

```
git -C <analytics-hub> pull --ff-only origin dev
git -C <analytics-hub> add internal_docs/docs/release-notes/YYYY-MM-DD-*.md   # only your files
git -C <analytics-hub> commit -m "Add release notes vX.Y.Z (changelog, dev, marketing)" -m "Co-Authored-By: AI"
git -C <analytics-hub> push origin dev
```

Push **only to analytics-hub `dev`**. The public `docs/source/changelog.md` (separate `docs` repo) is updated by hand — copy the `## X.Y.Z` section across if the user asks.

**Done when:** commit pushed to `origin/dev`; local shows no ahead/behind.

## Rules

- Russian throughout the three files.
- Push only to analytics-hub `dev`; never commit skills or release notes into the Astra meta-repo root.
- Security: state exactly what Jira shows. Dependency CVEs usually travel via infra/CI **without MON tickets** — if the dep-vuln list is missing, say so honestly («список закрывших зависимостей выложим отдельно») rather than invent.
- Confirm the release date with the user before pushing (it lands in the filename and the dev-file header).

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — a Jira quirk, a version-naming gotcha, a project-specific fact — append it to the matching file in `~/Documents/Code_projects/agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `~/Documents/Code_projects/agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
