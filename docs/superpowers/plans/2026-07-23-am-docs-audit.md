# am-docs-audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `am-docs-audit` skill — a cleanliness umbrella that audits the Astra meta-repo doc-layer against an ownership model in `AGENTS.md` and runs `prune` on the stores.

**Architecture:** The ownership/layering contract lives as a section in Astra `AGENTS.md` (canonical, agent-agnostic SoT; no new file). `am-docs-audit` (in `agent-knowledge/skills/`) reads that contract, runs 8 signals (3 mechanical, 5 judgment), reports findings with proposed actions, and delegates the knowledge stores to the existing `prune` skill. `CLAUDE.md` is trimmed to a thin pointer (dogfooding the skill's own `NON-CANONICAL-CONFIG` signal).

**Tech Stack:** Markdown skill (YAML frontmatter + prose), shell checks (`test`/`grep`/`find`/`comm`), `lint-portability.py` gate. No new runtime code in P1.

**Two repos involved:**
- `agent-knowledge/` (GitHub `crass987/agent-knowledge`) — the skill, router, USAGE.
- `Astra/` (GitLab meta-repo; push is VPN-gated) — `AGENTS.md` ownership section, `CLAUDE.md` trim.

Commit steps are **local**, repo-scoped (`git -C <path>`). Push is out of scope — owner pushes per repo rules.

**Spec:** `agent-knowledge/docs/superpowers/specs/2026-07-23-am-docs-audit-design.md`

---

## File Structure

| Action | File | Responsibility |
|---|---|---|
| Modify | `Astra/AGENTS.md` | Add `## Ownership & Layering` section — the contract the audit reads |
| Create | `agent-knowledge/skills/am-docs-audit/SKILL.md` | The skill: modes, 8 signals, prune-delegation, output, footer |
| Modify | `agent-knowledge/skills/_INDEX.md` | Router/trigger entry so the skill is discoverable |
| Modify | `Astra/CLAUDE.md` | Trim to thin pointer (dogfood `NON-CANONICAL-CONFIG`) |
| Modify | `agent-knowledge/USAGE.md` | Note `am-docs-audit` as the umbrella in the governance section |

---

## Task 1: Add the Ownership & Layering contract to Astra AGENTS.md

**Files:**
- Modify: `Astra/AGENTS.md` (append a new section after the existing content)

- [ ] **Step 1: Append the ownership section**

Append exactly this to `Astra/AGENTS.md`:

```markdown

## Ownership & Layering

Canonical map of who owns what in this meta-repo. Agent-specific files defer to
`AGENTS.md` (this file) — never duplicate canonical content into `CLAUDE.md`. The
`am-docs-audit` skill checks the doc-layer against this table.

| File | Layer | Owner (concern) |
|---|---|---|
| `AGENTS.md` | root | canonical SoT: product + architecture + this ownership section |
| `CLAUDE.md` | root | thin Claude Code config: pointers, PM-rules, branch, auth → delegates to AGENTS.md |
| `HARNESS.md` | root | human onboarding: setup, day-1 by role |
| `README.md` | root | engineering-ops guide: clone/sync/refresh-AGENTS |
| `CONTEXT.md` | root | HOT channel: active tasks, open questions (agents write here) |
| `repos.yml` | root | repository registry — the one list (`.gitignore` generated from it) |
| `meta/research-index.md` | meta | research registry |
| `meta/skills-guide.md` | meta | routing "want X → skill Y" |
| `meta/repos/*.md` | meta | service profiles (49) |
| `PM/` | subrepo | product-artifact home (separate GitLab); map in `PM/CLAUDE.md` |

**Layer rule:** global (`~/.claude/CLAUDE.md`) → Astra root → subrepo (`PM/`). A lower
layer supplements, never replaces, a higher one.

**Declared exceptions (do not flag as duplication):**
- `agent-knowledge/` (GitHub: my skills + stores) ↔ `am-skills/` (GitLab: team AM skills) — intentional split.
- `NMT-Canon/` — external read-only (CC BY-NC-SA).
```

- [ ] **Step 2: Verify MISSING-OWNER holds (every root/meta doc is in the table)**

Run from `Astra/`:
```bash
comm -23 \
  <(ls *.md *.yml meta/*.md 2>/dev/null | sort -u) \
  <(grep -oE '`[A-Za-z0-9_./*-]+`' AGENTS.md | tr -d '`' | sort -u)
```
Expected: output lists only files intentionally out of the ownership table (e.g. `HARNESS.md` should NOT appear — it is in the table). If a tracked root/meta doc appears here, add it to the table before continuing.

- [ ] **Step 3: Commit (Astra repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/Astra add AGENTS.md
git -C /Users/CraSS/Documents/Code_projects/Astra commit -m "docs(agents): ownership & layering contract for am-docs-audit"
```

---

## Task 2: Create the SKILL.md skeleton (frontmatter + modes + contract)

**Files:**
- Create: `agent-knowledge/skills/am-docs-audit/SKILL.md`

- [ ] **Step 1: Write the file with frontmatter, overview, contract, and modes**

Create `agent-knowledge/skills/am-docs-audit/SKILL.md` with exactly this content:

```markdown
---
name: am-docs-audit
description: Audit the Astra harness doc-layer against the ownership model in AGENTS.md — stale refs, missing owners, divergent file-tables, duplication, layer violations, dead artifacts, non-canonical config, relevance — and run prune on the stores. Use to keep the whole harness clean.
---

# am-docs-audit — cleanliness umbrella for the Astra harness

One command to keep the **whole** harness clean: audit the documentation layer of the
Astra meta-repo against the ownership model in `AGENTS.md`, **and** run `prune` on the
knowledge stores (`learnings/`, `decisions/`). Detect → report → human-approve. Never
auto-rewrite instruction files.

## Contract

The audit checks docs against the **Ownership & Layering** section of Astra `AGENTS.md`
(the canonical, agent-agnostic SoT). That section is the source of truth — not a target of
the audit. If the contract itself is wrong, fix it in `AGENTS.md`, not here.

## Modes

| Mode | What it does | When |
|---|---|---|
| `check` (default, no arg) | Scan doc-layer by the 8 signals + invoke `prune` in check mode; print one report with proposed actions. Changes nothing. | periodic health-check; before onboarding/release |
| `fix` | For each finding: show a diff + AskUserQuestion (keep / remove / update / merge / archive); apply approved; invoke `prune` interactive at the end. | when you want to act on the report |

## Audit surface

**IN:** Astra root `*.md` + `*.yml`; `meta/*.md` + real `meta/` structure; cross-ref
resolution into siblings (`agent-knowledge/`, `am-skills/`, `NMT-Canon/`); declared-exceptions.
**OUT:** code sub-repos; per-repo `AGENTS.md` (owned by `refresh-agents`); deep internals of
`PM/` and `agent-knowledge`; auto-consolidation (forbidden).

## Run prune (umbrella)

After the doc scan, invoke the `prune` skill in the **same mode** as this run and merge its
findings into the report. `prune` owns the stores; this skill owns the docs. Do not duplicate
prune's STALE/CONFLICT/ORPHAN logic — call prune.
```

- [ ] **Step 2: Verify frontmatter is valid**

Run:
```bash
head -4 agent-knowledge/skills/am-docs-audit/SKILL.md
```
Expected: lines starting `---`, `name: am-docs-audit`, `description: ...`, `---`.

- [ ] **Step 3: Commit (agent-knowledge repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge add skills/am-docs-audit/SKILL.md
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge commit -m "feat(am-docs-audit): skill skeleton — contract, modes, prune delegation"
```

---

## Task 3: Add the 8 signals to SKILL.md

**Files:**
- Modify: `agent-knowledge/skills/am-docs-audit/SKILL.md` (append before the closing of the file)

- [ ] **Step 1: Append the signals section**

Append exactly this to the SKILL.md:

```markdown

## The 8 signals

Run the mechanical signals (1-3) via the commands; assess the judgment signals (4-8) from
the gathered evidence. **Age alone never flags — only change** (same rule as `prune`). Each
finding is reported as `{file · signal · evidence · proposed action}`.

### Mechanical (deterministic)

1. **STALE-REF** — a doc references a path that does not exist.
   Collect path-like tokens from docs, then `test -e` each against the right root:
   ```bash
   grep -rhoE '`[A-Za-z0-9_./-]+`' *.md meta/*.md | tr -d '`' | sort -u
   ```
   Resolve each: Astra-relative under `./`, agent-knowledge under `~/Documents/Code_projects/agent-knowledge/`, home under `~/`. Flag misses (e.g. `meta/reference/`).

2. **MISSING-OWNER** — a root/meta doc with no row in the AGENTS.md ownership table, or a row whose file is gone.
   ```bash
   comm -23 <(ls *.md *.yml meta/*.md 2>/dev/null | sort -u) \
           <(grep -oE '`[A-Za-z0-9_./*-]+`' AGENTS.md | tr -d '`' | sort -u)
   ```

3. **TABLE-DIVERGENCE** — a file-listing inside a doc disagrees with real files.
   For each listing block (CLAUDE File-Map, README structure tree, HARNESS "Что где"):
   compare the listed set to `find <dir> -maxdepth 1`. Flag listed-but-missing and present-but-unlisted.

### Judgment (agent + human — propose, never auto-apply)

4. **NON-CANONICAL-CONFIG** — an agent-specific file (`CLAUDE.md`) restates a canonical
   `AGENTS.md` section instead of pointing to it. Confirm by reading; propose "replace with pointer".

5. **DUPLICATION** — the same fact in 2+ entry docs. grep canonical facts across root docs;
   propose "keep in canonical AGENTS.md, replace copy with a pointer".

6. **LAYER-VIOLATION** — a lower layer (e.g. `PM/CLAUDE.md`) restates or contradicts root
   `AGENTS.md` instead of supplementing. Propose "defer to the higher layer".

7. **DEAD-ARTIFACT** — stray/backup files (`*.bak`, untracked clutter in `meta/`) [mechanical:
   `git status --porcelain meta/` + `find meta -name '*.bak*'`]; or a doc superseded but not
   archived [judgment]. Zero references is a strong dead-prior:
   ```bash
   grep -rl '<filename>' . --include='*.md' | grep -v '/<filename>$' | wc -l
   ```

8. **RELEVANCE** — is each root/meta doc still needed? Combine: reference-count (0 = dead-prior)
   + mtime (tiebreaker only) [mechanical]; redundancy with canonical + necessity of a distinct
   concern [judgment]. Propose one of: **KEEP / TRIM / MERGE-into-\<X\> / ARCHIVE / SPLIT**.
```

- [ ] **Step 2: Verify each mechanical signal surfaces the known oracle findings**

Run from `Astra/`:

STALE-REF oracle (`meta/reference` must be flagged):
```bash
grep -rl 'meta/reference' *.md meta/*.md && [ ! -e meta/reference ] && echo "STALE-REF confirmed: meta/reference"
```
Expected: prints the referencing file(s) + `STALE-REF confirmed: meta/reference`.

DEAD-ARTIFACT oracle (`jtbd-snapshot.yml` has 0 inbound refs):
```bash
n=$(grep -rl 'jtbd-snapshot.yml' . --include='*.md' | grep -v '/jtbd-snapshot.yml$' | wc -l | tr -d ' '); echo "refs=$n"
```
Expected: `refs=0`.

TABLE-DIVERGENCE oracle (CLAUDE.md File-Map undercounts root docs):
```bash
ls *.md | wc -l
```
Expected: `6` — more than the File-Map's 4 entries (pre-trim).

- [ ] **Step 3: Commit (agent-knowledge repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge add skills/am-docs-audit/SKILL.md
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge commit -m "feat(am-docs-audit): 8 signals (3 mechanical, 5 judgment) + oracle commands"
```

---

## Task 4: Add output format + learning-footer to SKILL.md

**Files:**
- Modify: `agent-knowledge/skills/am-docs-audit/SKILL.md` (append)

- [ ] **Step 1: Append output format and footer**

Append exactly this:

```markdown

## Output

Each finding: `{file · signal · evidence · proposed action}`.
- `check` → table to chat. Optionally also write `meta/reports/docs-audit-<date>.md`
  (mirror of `refresh-agents` → `refresh-summary-…`).
- `fix` → show a diff per finding, AskUserQuestion, apply approved changes.

Docs are **not** append-only (unlike the stores): edits are normal in-place changes, but
**every** change goes through human approval. Do not delete or rewrite a published doc
without an explicit yes on its diff.

<!-- learning-footer: am-docs-audit is operational — capture a learning + log the run -->
After the run: if a durable operational lesson emerged (saves 5+ min next time), append it
to `agent-knowledge/learnings/` (format in `learnings/README.md`), and append one row to
`agent-knowledge/state/skill-runs.md` (skill / mode / finding-count / outcome).
```

- [ ] **Step 2: Verify the footer + prune reference are present**

Run:
```bash
grep -c 'state/skill-runs.md' agent-knowledge/skills/am-docs-audit/SKILL.md
grep -c 'invoke .prune.' agent-knowledge/skills/am-docs-audit/SKILL.md
```
Expected: both print `1` (or more).

- [ ] **Step 3: Commit (agent-knowledge repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge add skills/am-docs-audit/SKILL.md
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge commit -m "feat(am-docs-audit): output format + learning-footer"
```

---

## Task 5: Register the skill in the router (_INDEX.md)

**Files:**
- Modify: `agent-knowledge/skills/_INDEX.md`

- [ ] **Step 1: Read the current _INDEX.md to match its table format**

Run:
```bash
sed -n '1,60p' agent-knowledge/skills/_INDEX.md
```
Note the exact table header/columns and the Knowledge-Meta track grouping (where `prune`, `improve-skill`, `decisions` are listed).

- [ ] **Step 2: Add the am-docs-audit row**

Add a row to the Knowledge-Meta section matching the existing column shape. Content to use:
- trigger keywords: `почисти харнес`, `доки устарели`, `дубли в CLAUDE/AGENTS`, `stale docs`, `context hygiene`, `am-docs-audit`
- skill: `am-docs-audit`
- one-liner: "audit doc-layer vs AGENTS.md ownership + run prune; keep the whole harness clean"

- [ ] **Step 3: Verify the entry resolves**

Run:
```bash
grep -c 'am-docs-audit' agent-knowledge/skills/_INDEX.md
```
Expected: `>= 1`.

- [ ] **Step 4: Commit (agent-knowledge repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge add skills/_INDEX.md
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge commit -m "feat(skills-index): register am-docs-audit (Knowledge-Meta)"
```

---

## Task 6: Dogfood — trim Astra CLAUDE.md to a thin pointer (NON-CANONICAL-CONFIG fix)

**Files:**
- Modify: `Astra/CLAUDE.md`

- [ ] **Step 1: Run the NON-CANONICAL-CONFIG check on CLAUDE.md**

Run from `Astra/`:
```bash
grep -nE 'File Map|PM/|NMT|Branch Convention|Authentication' CLAUDE.md
```
Read CLAUDE.md and identify sections that restate canonical AGENTS.md content (the File Map
table is now superseded by the `## Ownership & Layering` section in AGENTS.md). Keep only
genuinely Claude-specific/operational bits; convert the rest to pointers.

- [ ] **Step 2: Apply the trim via the skill's fix flow**

Edit `Astra/CLAUDE.md`:
- Replace the **File Map** table with a one-line pointer:
  `> Full file ownership & layering map: see the **Ownership & Layering** section in `AGENTS.md`.`
- Keep **Branch Convention** and **Authentication** (operational, short, not duplicated in AGENTS.md) — or, if they already exist in AGENTS.md, replace with a pointer.
- Keep the **PM/** and **NMT** routing as thin pointers only if the content is not already in `AGENTS.md`/`PM.md`; otherwise delegate.

Show the diff to the user and get explicit approval before saving (this is a published doc).

- [ ] **Step 3: Verify the trim removed the duplicate**

Run:
```bash
grep -c 'Ownership & Layering section in .AGENTS.md' CLAUDE.md
test ! -s "$(grep -l '| \*\*File\*\* |' CLAUDE.md 2>/dev/null)" && echo "File Map table removed"
```
Expected: first prints `>= 1` (pointer present); second prints `File Map table removed`.

- [ ] **Step 4: Commit (Astra repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/Astra add CLAUDE.md
git -C /Users/CraSS/Documents/Code_projects/Astra commit -m "docs(claude): trim to thin pointer — defer to AGENTS.md ownership (am-docs-audit dogfood)"
```

---

## Task 7: Lint portability + note umbrella in USAGE.md

**Files:**
- Modify: `agent-knowledge/USAGE.md`

- [ ] **Step 1: Run the agent-agnostic gate**

Run:
```bash
cd /Users/CraSS/Documents/Code_projects/agent-knowledge && python3 scripts/lint-portability.py skills/am-docs-audit
```
Expected: `0` findings (no hardcoded `mcp__*` or agent-specific tool names). If non-zero, replace the offending name with a capability phrase and re-run.

- [ ] **Step 2: Add the umbrella note to USAGE.md governance**

In `agent-knowledge/USAGE.md`, in the «Поддержка (governance)» section (the «Чистка.» bullet),
append one sentence:

```markdown
 Единый зонтик чистоты — навык `am-docs-audit`: аудирует док-слой мета-репо Astra против ownership-секции в `AGENTS.md` и затем запускает `prune` (сторты). Один вход «почисти весь харнес».
```

- [ ] **Step 3: Verify**

Run:
```bash
grep -c 'am-docs-audit' agent-knowledge/USAGE.md
```
Expected: `>= 1`.

- [ ] **Step 4: Commit (agent-knowledge repo, local)**

```bash
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge add USAGE.md
git -C /Users/CraSS/Documents/Code_projects/agent-knowledge commit -m "docs(usage): am-docs-audit as the cleanliness umbrella (runs prune)"
```

---

## Task 8: Integration run — first real `check` against Astra

**Files:**
- Read-only run; optional write `Astra/meta/reports/docs-audit-2026-07-23.md`

- [ ] **Step 1: Run am-docs-audit in check mode**

Invoke the skill against the Astra meta-repo. Expected findings (the oracle from the spec):
- `STALE-REF`: `meta/reference/` referenced in `README.md`, path missing.
- `DEAD-ARTIFACT` + `RELEVANCE=ARCHIVE`: `jtbd-snapshot.yml` (0 inbound refs, superseded by strategy-docset).
- `TABLE-DIVERGENCE`: `README.md` structure tree lists `meta/reference/` (missing) and omits real `meta/` entries (`research-index.md`, `skills-guide.md`, `repos/`, `harness-pitch-deck.*`).
- `DUPLICATION`: "what's where" tables in both `HARNESS.md` and `README.md`; go-lib/data-flow in both `PM.md` and `AGENTS.md`.
- `RELEVANCE=TRIM`: `PM.md` (used, 9 refs, but overlaps `AGENTS.md`).
- prune findings: `learnings/` + `decisions/` (expect near-clean — earlier scan found no STALE/CONFLICT/ORPHAN).

- [ ] **Step 2: Confirm the skill invokes prune and merges the report**

Verify the report contains a `prune` section (store findings) alongside the doc-layer findings.

- [ ] **Step 3: Log the run**

Append one row to `agent-knowledge/state/skill-runs.md`:
`am-docs-audit | check | 2026-07-23 | <finding-count> | first run, oracles confirmed`

- [ ] **Step 4: Hand findings to the user for `fix` triage**

Do NOT auto-fix. Present the report; the user decides which findings to resolve in a `fix` run
(e.g. archive `jtbd-snapshot.yml`, fix `README.md` structure tree, trim `PM.md`). Each `fix`
action goes through diff + approval.

---

## Self-Review (run after writing)

**1. Spec coverage:** every spec section maps to a task —
- §3 architecture (model in AGENTS.md) → Task 1; §4 ownership table → Task 1;
- §5 skill (home/modes/surface/output/prune) → Tasks 2-4; §6 eight signals → Task 3;
- agent-agnostic gate → Task 7; CLAUDE.md trim (NON-CANONICAL-CONFIG) → Task 6;
- router discoverability → Task 5; governance note → Task 7; integration/behavioral test → Task 8.
- §9 P2 (CI script `docs_audit.py`) — intentionally excluded (deferred). ✓

**2. Placeholder scan:** no TBD/TODO; every code step shows exact content; commands have expected output. The only judgment-step (Task 6 Step 2) deliberately defers final wording to the skill's fix flow + user approval — this is the spec's "human approves each change" rule, not a placeholder. ✓

**3. Type/name consistency:** signal names (`STALE-REF`, `MISSING-OWNER`, `TABLE-DIVERGENCE`, `NON-CANONICAL-CONFIG`, `DUPLICATION`, `LAYER-VIOLATION`, `DEAD-ARTIFACT`, `RELEVANCE`) and the RELEVANCE action set (`KEEP/TRIM/MERGE/ARCHIVE/SPLIT`) are identical across spec, SKILL.md (Task 3), and the oracle (Task 8). `am-docs-audit` name consistent everywhere. ✓

No issues found. Plan is complete.
