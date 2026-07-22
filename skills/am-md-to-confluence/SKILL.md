---
name: am-md-to-confluence
description: Use when publishing a Markdown document to Confluence as a mirror (with optional live Jira-macro sections by label) — «опубликуй в confluence», «md → confluence», «confluence page», «живые задачи из Jira на странице». The .md in git stays canonical; Confluence is the mirror + execution-view.
---

# Markdown → Confluence (Astra Monitoring)

## Overview

Publish a `.md` doc to Confluence (Astra Monitoring space) as a **mirror** — the `.md` in git is canonical, the Confluence page is the published view. Optionally embed **live Jira task lists** (Jira-issue macros by label) so the page doubles as an execution-view: tasks pull live from Jira, and relabeling an issue updates the page automatically.

## When to Use

- Publish a `.md` artifact to Confluence for the team — «опубликуй в confluence».
- Build an execution-view: a roadmap/theme page with live Jira task lists grouped by label.

## When NOT to Use

- Quick note → edit Confluence directly.
- Just need a polished PDF (no live Jira links) → `am-md-to-pdf`.

## How to Run

**0. Source of truth.** The `.md` in git is canonical; the Confluence page is a mirror. State this on the page (footer: *«Источник: `<path>.md` в git; эта страница — зеркало»*). Re-publish on `.md` change.

**1. Target space.** Use **`MNTR`**. Do **not** use `PS` — it is read-only for the integration (`create_page` fails with *«Could not create content with type page»*). Parent for internal AM pages: **Internal Folder** — get its id first:
`confluence_get_page(space_key="MNTR", title="Internal Folder")` → `parent_id` (e.g. `190158847`).

**2. Content + format.**
- **Simple doc (no live Jira lists):** `content_format="markdown"`, content via `content` (inline) or `content_file`.
  ⚠ `content_file` must be **inside the workspace** (e.g. `PM/tmp/`), not `/tmp` — a path-traversal guard rejects outside-workspace paths.
- **Live Jira task lists, or reliable list/table rendering:** `content_format="storage"` (XHTML). Jira-issue macro:
```
<ac:structured-macro ac:name="jira" ac:schema-version="1">
<ac:parameter ac:name="server">Jira - Astra Linux</ac:parameter>
<ac:parameter ac:name="columnIds">issuekey,summary,issuetype,status,priority,assignee</ac:parameter>
<ac:parameter ac:name="columns">key,summary,type,status,priority</ac:parameter>
<ac:parameter ac:name="maximumIssues">100</ac:parameter>
<ac:parameter ac:name="jqlQuery">project = MON AND labels = <label> AND statusCategory != Done ORDER BY priority DESC, key</ac:parameter>
<ac:parameter ac:name="serverId">d19f6132-65dc-37bb-94ca-4be05d9bb688</ac:parameter>
</ac:structured-macro>
```
  `serverId` is **required** — without it the macro won't resolve. Verify/copy the exact `serverId` + macro shape from an existing macro page: `confluence_get_page(space_key="MNTR", title="AM 1.6", convert_to_markdown=false)`.

**3. Create / update.**
- New: `confluence_create_page(space_key="MNTR", parent_id=<id>, title=..., content_file=<workspace path>, content_format="storage"|"markdown")`.
- Existing: `confluence_update_page(page_id=..., title=..., content_file=..., content_format=..., version_comment=...)`.

**4. Live Jira lists by label (optional, execution-view).** Tag MON issues with one label per theme — `bulk_update_issues(issue_keys=[...], labels_add=["roadmap-<job>"])` — then one Jira macro per theme with `labels = roadmap-<job>` pulls them live. Classify with subagents on a temp TSV for volume (see *Volume classification* below).

## Verify

`confluence_get_page(page_id=..., convert_to_markdown=true)` — confirms tables/text arrived. **Jira macros render live only in the browser view** (the markdown roundtrip shows the raw JQL, not the list) — eyeball the page URL to confirm the macros resolved.

## Volume classification (tag many issues by label)

For hundreds of issues: pull all to a temp TSV (`search_issues(auto_paginate=true, fields=[summary,status,issuetype,labels])` → `jq` to `PM/tmp/<name>.tsv` = `key\tstatus\ttype\tlabels\tsummary`), split into chunks, dispatch parallel subagents to classify each row into one label, merge the JSON, then `bulk_update_issues` per label.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Create fails «Could not create content with type page» | Space is read-only (e.g. `PS`) → use `MNTR`. |
| `content_file` → «path traversal / resolves outside workspace» | Write inside the workspace (e.g. `PM/tmp/`), not `/tmp`. |
| Markdown bullets flatten, bold+italic merge | Use `content_format="storage"` (XHTML) with proper `<ul><li>`, `<strong>`, `<em>`. |
| Jira macro shows error / blank | Missing `serverId` — copy it from an existing macro page (AM 1.6). |
| `bulk_update_issues` 400 on some issues | Epic issue-type can't be bulk-labeled (Jira field config) — label the children; epics are containers, macros pull children fine. |
| Confluence drifts from `.md` | `.md` is canonical — re-publish on change; note the source path on the page. |
