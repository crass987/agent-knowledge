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
| `fix` | For each finding: show a diff and ask the user to choose (keep / remove / update / merge / archive); apply approved; invoke `prune` interactive at the end. | when you want to act on the report |

## Audit surface

**IN:** Astra root `*.md` + `*.yml`; `meta/*.md` + real `meta/` structure; cross-ref
resolution into siblings (`agent-knowledge`, `am-skills`, `Next-Move-Theory-Canon`); declared-exceptions.
**OUT:** code sub-repos; per-repo `AGENTS.md` (owned by `refresh-agents`); deep internals of
`PM/` and `agent-knowledge`; auto-consolidation (forbidden).

## Run prune (umbrella)

After the doc scan, invoke the `prune` skill in the **same mode** as this run and merge its
findings into the report. `prune` owns the stores; this skill owns the docs. Do not duplicate
prune's STALE/CONFLICT/ORPHAN logic — call prune.

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
