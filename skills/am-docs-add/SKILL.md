---
name: am-docs-add
description: Add to or change the Astra Monitoring **public** Sphinx docs (repo `docs/`) — every claim **grounded** (traced to `code:line` or a live probe) before it is written, then rendered, MR'd, and published with a team-format Jira comment. Triggers: «добавь в доку», «опиши X в публичке», «обнови доку», «add install docs for X», «update public docs». Audit-for-accuracy → `am-grill-docs`; analytics-hub specs → `am-write-specs`; Confluence → `am-md-to-confluence`.
---

# am-docs-add — grounded authoring into the public docs site

Write new or changed content into the public Sphinx site (`docs/`). One discipline carries
the skill: **every sentence is a *claim* that must be *grounded* — traced to a source
(`code:line`, a live probe, a config) — before it is written.** An ungrounded sentence is
invalid, and the claim you are surest about is the one to re-trace. A code comment is not a
source; the code is.

Two payloads share one pipeline:

- **ADD** — a new scenario/section/page (e.g. a new install method).
- **FIX** — correct a stale claim (a renamed flag, a changed URL, a wrong matrix cell). For
  FIX, the consistency sweep *is* the job, not a nice-to-have.

## Scope gate (run first)

Target = the public Sphinx repo `docs/` only. If the work is:

- auditing accuracy without editing → `am-grill-docs`;
- analytics-hub REQ/SPEC or internal markdown → `am-write-specs`;
- publishing markdown to Confluence → `am-md-to-confluence`; to PDF → `am-md-to-pdf`.

…stop here and route out.

## Steps

### 1. Mode + canonical page
ADD → find the **owning** page and attach to it (install → `agent/install/`); do **not**
create a new file when a canonical one exists. FIX → list every page that restates the stale
claim.
*Done when:* one owning page is named (ADD) / every restating page is listed (FIX).

### 2. Ground the claims — research (delegate)
Dispatch **`am-research`** on the topic; its source-cited output is your evidence budget. Do
not begin prose until grounded facts return.
*Conditional cross-check:* fan out parallel verify agents **only when** sources disagree, a
probe surprised you, or you corrected an assumption (mechanics →
`superpowers:dispatching-parallel-agents`). A one-grep fact gets no sub-agent — that is
context tax.

### 3. Trace each claim to its source
Classify every claim and trace it:

| type | trace how |
|---|---|
| `code:line` | read the code — definition **and** call site — not a nearby comment. The line must be on the repo's `dev` branch (`repos.yml`); if it lives only on a feature branch → **block** the docs, file a ticket, do not ship as truth |
| `live-probe` (URL / endpoint) | `curl -sI`; if a probe **surprises** you → trace the **root cause before writing** (a doc of a symptom rots on day one). Document reality, not aspiration; if the probe reveals a real defect → file a follow-up ticket alongside the docs MR |
| `config-file:line` / `doc-cross-ref` | open it |

*Done when:* every claim has a cited source; none rests on a comment or an assumption.

### 4. Structural surfaces
Enumerate every surface that references the category: **tab · list · matrix · toctree ·
cross-link · counter**. Plan one edit per surface. The matrix is forgotten most often — it
lives far from the edited page.
*Done when:* each surface has an edit planned; none forgotten.

### 5. Consistency sweep (exhaustive) — delegate
For each enumeration / count / capability the change affects, `grep -rIn` the **numerals +
synonyms + ordinals** (`«Пять»`, `5`, `пять`, `N способов`, `во-первых…`); record every hit in
a table `{file | line | matches-new? | action}`. Delegate "find every page disagreeing with
the new truth" to **`am-grill-docs`** scoped to the section.
*Done when:* the table has **zero un-actioned rows**.

### 6. Write in house style (genre-branched)
- **Prose pages** → write, run **`infostyle`**, accept via the **`infostyle-critic`
  agent-type** (the global Stop-hook blocks delivery without the critic). Stance: confirm the
  feature, don't refute it.
- **Reference / template pages** (exporter metric tables, config yaml, CLI flag lists) →
  structural template, **not** infostyle — compression harms reference.

Checkable invariants:
- same tab-set nesting (`::::::{tab-set}` / `:::::{tab-item}`), frontmatter (`notoc: true`
  for exporters);
- **unique headings** — `autosectionlabel` is global, so each new heading appears exactly once
  across `docs/source/` (`grep -rc '^## <heading>' docs/source/`); generic headings collide
  and silently break cross-refs;
- toctree entry exists — `grep -rIn '<new-slug>' docs/source/**/index.md` ≥ 1, or the page is
  an orphan Sphinx will not error on;
- **Russian prose** (house style); identifiers / paths / flags / YAML keys stay English.

*Done when:* all four checks pass and the critic verdict is not МЁРТВЫЙ.

### 7. Render-check (mechanical gate)
`cd docs && ./.venv/bin/python -m sphinx -b html source build 2>new.log` (invoke via
`python -m sphinx` — the `sphinx-build` shebang is stale after the repo move).
- Pass = **0 NEW** `ERROR` / `WARNING` lines vs the baseline — method in
  `memory:ref-am-docs-build.md` (do **not** restate the number; the ~95 transition errors on
  the `# H1\n---` house pattern are expected).
- Then grep the built HTML: tabs render as `sd-tab-label`, no `undefined label` /
  `cross-reference target` in the log, images present. Build-green ≠ content-present.

*Done when:* 0 new diagnostics AND signature strings present in `build/html/<page>.html`.

### 8. Serve for human read
`./.venv/bin/sphinx-autobuild source build/html --host 0.0.0.0 --port 8000` (the Makefile
assumes Docker — use the venv path when Docker is unavailable). Hand the user the URL + which
tab / section.

### 9. Ship — ticket → branch → MR → merge → comment → sprint → status → cleanup
The full command bundle is in **`reference.md`** (single internal source). Two rules stay
**inline** because their failure is silent and severe:

- **branch = `MON-XXXX`, lowercase, NO SLASH** — the branch becomes a Docker tag in CI and a
  slash breaks the build. Why in `memory:feedback-push-rules.md`.
- **Jira text is wiki markup, not Markdown** (`[text|url]`, `{{code}}`, `||hdr||`).
  `memory:feedback-jira-wiki-markup.md`.

Ticket scope: a change that **adds a claim / documents a behavior / discovers a defect** →
full ticket via **`/jtbd`** (summary names the *work*; two-layer description — see
`reference.md`). A pure one-fact correction with no new claim → ticket optional, MR
description suffices.

*Done when:* MR merged into `dev`; team-format comment posted; issue in the active sprint with
status «На ревью» (**verified by JQL** — `add_to_sprint` silently fails — see `reference.md`);
`git ls-remote origin <branch>` empty and no `remotes/origin/<branch>` remains.

## When NOT to use
- Auditing docs vs code (no edit) → `am-grill-docs`.
- analytics-hub specs / requirements → `am-write-specs`.
- Publishing markdown to Confluence / PDF → `am-md-to-confluence` / `am-md-to-pdf`.
