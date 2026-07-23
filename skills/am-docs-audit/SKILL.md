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
