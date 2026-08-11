# am-docs-add — reference

Operational bundle for shipping a docs change. Single internal source for the commands and
the project-specific gotchas. The **values** (baseline counts, hosts, quirks) live in
`memory:` — point to them, do not restate, so they do not rot in two places.

## Branch + commit + MR + merge

- Branch `MON-XXXX` — **lowercase, no slash** (`memory:feedback-push-rules.md`); never
  `main` / `dev`.
- Commit: `docs(<scope>): <RU description> (MON-XXXX)` — match the repo's `git log`
  convention; end the message with `Co-Authored-By: AI`.
- MR `MON-XXXX → dev`, **merge-commit** style (not squash / rebase — matches repo history);
  remove the source branch on merge.
- MR via the GitLab API or `glab mr create` / `glab mr merge`. `source_branch` is
  **immutable** — renaming a branch means a new MR.
- The push token is already in the `docs/` remote URL; `glab` is authed for
  `gitlab.astra-monitoring.astralinux.ru`.
- Wrong branch-name recovery: the commit survives `git branch -D` →
  `git branch <new> <sha>`, push, the old MR auto-closes.

## Ticket (`/jtbd`)

- **Summary** names the *work* (what changes), not a benefit — `/jtbd` Ремесло 2. Not AJTBD
  canon (that is for product strategy).
- **Description, two layers** (`memory:feedback-jira-description-two-layers.md`):
  - top — JTBD job-phrase «Когда… я хочу… чтобы…» (first person) + a plain-language essence,
    infostyle;
  - bottom — `{color:#888}_Техконтекст: …_{color}` (gray italic): `file:line`, fields in
    `{{}}`, MON-links. **No `{panel}`.** Preserve the author's caveats / ⚠ / «НЕ X» verbatim
    (`memory:feedback-jtbd-preserve-ticket-caveats.md`).
- **Wiki markup, not Markdown** (`memory:feedback-jira-wiki-markup.md`).
- **MCP only** — `mcp__jira__*`; never extract creds or do raw REST
  (`memory:feedback-jira-mcp-only.md`).

## Jira comment (team format)

Three parts:

1. Header: `Смержено в dev: [MR !N|<mr-url>] (merge commit {*}<hash>{*}). <one line: what & why>.`
2. Table `||Файл||Что изменилось||Ссылка (dev-сайт)||` — rows
   `|{{docs: source/<path>}}|<change>|[<Title>|<dev-url>]|`.
3. Footer: a dev-stand link + a note that it rebuilds after the `dev` pipeline.

Dev-stand URL via `memory:ref-docs-dev-site.md` (host `docs-docs-dev.…sslip.io`, double
`docs-`, path `/dev/<page-path>.html`). Build the link for the page from step 1.

## Sprint + status + verify-after-mutate

- Add to the active sprint; set status **«На ревью»**.
- **Re-query after every Jira mutation.** `add_to_sprint` silently fails / times out even for
  a single issue (`memory:ref-jira-add-to-sprint-batching.md`); transitions and links can fail
  the same way. Confirm with JQL `key = MON-XXXX AND sprint in openSprints()` and a status
  re-fetch. MON statuses: «На ревью» = in-progress; Ready = ready-to-dev (not "done"); To
  Release / Finished = done (`memory:ref-mon-jira-workflow.md`).

## Sphinx render (detail)

- Build: `cd docs && ./.venv/bin/python -m sphinx -b html source build` (the `sphinx-build`
  shebang is stale after the repo move — invoke via `python -m sphinx`).
- Baseline method in `memory:ref-am-docs-build.md` — compare ERROR/WARNING **counts** via a
  diff; do not chase the absolute number (~95 transition errors on `# H1\n---` are expected).
- Serve: `./.venv/bin/sphinx-autobuild source build/html --host 0.0.0.0 --port 8000`.
- venv setup if missing: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

## Pitfalls (pointers, not restatements)

| rule | memory |
|---|---|
| branch no-slash, lowercase, never main/dev | `feedback-push-rules.md` |
| Jira text = wiki markup, not Markdown | `feedback-jira-wiki-markup.md` |
| two-layer ticket description | `feedback-jira-description-two-layers.md` |
| clickable links in committed md `[MON-X](url)`; absolute path to `.md` in chat | `feedback-clickable-links.md`, `feedback-full-path-to-md.md` |
| infostyle-critic agent-type gate (Stop-hook) | `feedback-infostyle-read-not-grep.md` |
| Russian prose for docs/ (not for `meta/repos/*.md` profiles) | `feedback-docs-in-russian.md`, `feedback-russian-all-structural.md` |
| confirm features, don't refute; user = ground truth | `feedback-confirm-features-not-refute.md`, `feedback-evidence-before-assertion.md` |
| add_to_sprint silently fails | `ref-jira-add-to-sprint-batching.md` |
| Sphinx baseline ~112 ERROR is normal | `ref-am-docs-build.md` |
| dev-stand URL pattern | `ref-docs-dev-site.md` |
