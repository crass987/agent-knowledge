# Harness Improvement — P0 (operational learning loop bootstrap) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the operational learning loop in the `agent-knowledge` harness — a typed learnings store, a local skill-runs telemetry log, a standard learning-footer, a portability linter, and an AGENTS.md tool-registry — piloted on `am-research`.

**Architecture:** Agent-driven and portable (no Claude-only hooks or binaries). Skills carry a footer instruction telling the agent to append operational lessons and a skill-run row to local markdown stores. Independence is enforced by (a) a portability linter that rejects hardcoded `mcp__*` tool-names, and (b) an AGENTS.md tool-registry mapping capabilities → concrete tools. Implements variant 2 + approach A+C from the PRD (`docs/superpowers/specs/2026-06-18-harness-improvement-prd.md`).

**Tech Stack:** Markdown (skills + stores), Python 3 + pytest (linter), git.

**Scope note:** P0 is mostly artifact authoring. The only coded/tested component is the portability linter; everything else is verified by structural checks (files exist with correct format, footer present, linter clean). Heavily-tested logic (auto-prune) is deliberately deferred to P2 (YAGNI for P0).

**Branch:** Continue on `docs/harness-improvement-prd` (already created) or a fresh `feat/harness-p0` off `main` — executor's call; keep PRD + plan + P0 work reviewable together.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `learnings/README.md` | Format spec, scope rules, diff vs `memory/` | Create |
| `learnings/{patterns,pitfalls,preferences,operational}.md` | Operational-learnings store, by type | Create |
| `state/skill-runs.md` | Local telemetry log (skill/duration/outcome) | Create |
| `skills/_shared/learning-footer.md` | Standard footer block — single source of truth | Create |
| `AGENTS.md` | Add `## Tool registry (capability → tool)` section | Modify |
| `scripts/lint-portability.py` | Flag hardcoded `mcp__*` tool-names in skills | Create |
| `tests/test_lint_portability.py` | pytest for the linter | Create |
| `skills/am-research/SKILL.md` | Pilot: add footer + abstract tool references | Modify |

**Boundary rules:** `learnings/` = operational facts (this plan). `memory/` (Astra session) = reflexive facts about user/project — do NOT touch or conflate.

---

## Task 1: Operational-learnings store

**Files:**
- Create: `learnings/README.md`
- Create: `learnings/patterns.md`, `learnings/pitfalls.md`, `learnings/preferences.md`, `learnings/operational.md`

- [ ] **Step 1: Write `learnings/README.md`**

```markdown
# Operational learnings

Durable facts that save time next session: command quirks, tool gotchas, project-specific conventions. This is the **operational** channel — distinct from `memory/` (reflexive: who the user is, what feedback they gave).

## Format

Each entry is a YAML frontmatter block followed by an optional one-line body. Append new entries at the bottom of the matching category file. Append-only; on contradiction, add a newer entry (latest wins) — `auto-prune` (P2) will surface conflicts.

```yaml
---
type: operational          # pattern | pitfall | preference | operational
key: short-kebab-key       # 2-5 words
insight: one sentence, fact not opinion
confidence: 1-10
source: observed           # observed | user-stated | extracted
files: []                  # optional, relevant paths
ts: 2026-06-18             # ISO date
scope: harness             # harness | project
---
<optional one-line elaboration>
```

## Categories
- `patterns.md` — repeatable ways that work
- `pitfalls.md` — things that bite
- `preferences.md` — settled taste calls
- `operational.md` — commands, tool quirks, environment facts

## Scope
- `scope: harness` → lives here (about the harness itself).
- `scope: project` → lives with that project (a section in its `AGENTS.md`), not here.

## Gate (do not log)
Obvious facts, one-off transient errors, or anything already written in a skill.
```

- [ ] **Step 2: Seed the four category files**

Each file: a one-line `# <Category>` header + a commented example entry (so the format is visible but not counted as real data). Example for `learnings/operational.md`:

```markdown
# Operational

<!--
Example entry (copy, fill, uncomment):
---
type: operational
key: jira-via-mcp-only
insight: Use the jira capability (AGENTS.md tool-registry); never raw REST or stored creds.
confidence: 9
source: user-stated
files: []
ts: 2026-06-18
scope: harness
---
-->
```

Repeat the same skeleton for `patterns.md`, `pitfalls.md`, `preferences.md` (change the `type:` and heading).

- [ ] **Step 3: Verify structure**

Run: `ls learnings/`
Expected: `README.md  operational.md  patterns.md  pitfalls.md  preferences.md`

- [ ] **Step 4: Commit**

```bash
git add learnings/
git commit -m "feat(learnings): add operational learnings store + format spec"
```

---

## Task 2: skill-runs telemetry log

**Files:**
- Create: `state/skill-runs.md`

- [ ] **Step 1: Write `state/skill-runs.md`**

```markdown
# skill-runs (harness telemetry — LOCAL ONLY)

Lightweight, agent-appended log of skill invocations. Feeds the OIAE "Observe" step and surfaces dead/failing skills. Never sent anywhere; not committed if it grows large (consider `.gitignore` once active).

| skill | ts | duration_s | outcome | branch | note |
|-------|----|-----------|---------|--------|------|

<!-- Append one row per skill run: outcome ∈ success | fail | abort -->
```

- [ ] **Step 2: Add `.gitignore` guard if state/ should stay local**

Check whether a root `.gitignore` exists: `ls -a .gitignore 2>/dev/null || echo NONE`
If you want telemetry local-only, append:
```
state/skill-runs.md
```
(Decision for the executor; if you prefer to commit a small seed, skip this step.)

- [ ] **Step 3: Commit**

```bash
git add state/skill-runs.md .gitignore 2>/dev/null
git commit -m "feat(telemetry): add local skill-runs log"
```

---

## Task 3: Standard learning-footer block

**Files:**
- Create: `skills/_shared/learning-footer.md`

- [ ] **Step 1: Write the footer source**

```markdown
## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
```

- [ ] **Step 2: Commit**

```bash
git add skills/_shared/learning-footer.md
git commit -m "feat(skills): add standard operational-learning footer block"
```

---

## Task 4: AGENTS.md tool-registry

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Read current `AGENTS.md`**

Run: `cat AGENTS.md` — note where to append (end of file unless a tools section exists).

- [ ] **Step 2: Append the tool-registry section**

Append to `AGENTS.md`:

```markdown

## Tool registry (capability → tool)

Skills reference tools by **capability**, not by vendor tool-name. Concrete tools are resolved here. (Portability principle P3: the neutral instrument layer is MCP; keep skill text tool-agnostic.)

| Capability | Tool | Notes |
|---|---|---|
| jira | `mcp__jira__*` | no raw REST, no stored creds |
| confluence | `mcp__confluence__*` | |
| web-search | `mcp__searxng__searxng_web_search` | preferred over built-in WebSearch |
| web-read | `mcp__web-reader__webReader` | url → markdown |
| repo-read (github) | `mcp__zread__*` | structure / read_file / search_doc |
| browser automation | `mcp__plugin_playwright_playwright__*` | |
| lib docs | `mcp__context7__*` | resolve-library-id → query-docs |
```

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs(agents): add capability→tool registry (portability P3)"
```

---

## Task 5: Portability linter (TDD)

**Files:**
- Create: `tests/test_lint_portability.py`
- Create: `scripts/lint-portability.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_lint_portability.py`:

```python
import importlib.util
from pathlib import Path


def _load_linter():
    here = Path(__file__).resolve().parent
    script = here.parent / "scripts" / "lint-portability.py"
    spec = importlib.util.spec_from_file_location("lint_portability", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flags_hardcoded_toolname(tmp_path):
    (tmp_path / "SKILL.md").write_text("Use mcp__jira__get_issue for Jira.\n")
    mod = _load_linter()
    findings = mod.scan_dir(tmp_path)
    assert any("mcp__jira__get_issue" in f for f in findings), findings


def test_clean_skill_passes(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "Use the jira capability (see AGENTS.md tool-registry).\n"
    )
    mod = _load_linter()
    assert mod.scan_dir(tmp_path) == []
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m pytest tests/test_lint_portability.py -v`
Expected: 2 FAILED (module/file not found).

- [ ] **Step 3: Implement the linter**

`scripts/lint-portability.py`:

```python
#!/usr/bin/env python3
"""Flag hardcoded mcp__* tool-names in skill texts.

Enforces portability principle P3: skills reference capabilities, concrete
tools live in the AGENTS.md tool-registry. Exit 1 if any found.
"""
import re
import sys
from pathlib import Path

TOOLNAME = re.compile(r"\bmcp__[A-Za-z0-9_]+__[A-Za-z0-9_]+")


def scan_dir(root: Path) -> list[str]:
    findings: list[str] = []
    for md in Path(root).rglob("SKILL.md"):
        for lineno, line in enumerate(
            md.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for hit in TOOLNAME.findall(line):
                findings.append(
                    f"{md}:{lineno}: hardcoded tool-name '{hit}' "
                    f"— reference by capability in the AGENTS.md tool-registry"
                )
    return findings


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("skills")
    for finding in scan_dir(root):
        print(finding)
    return 1 if scan_dir(root) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run tests — verify they pass**

Run: `python -m pytest tests/test_lint_portability.py -v`
Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add scripts/lint-portability.py tests/test_lint_portability.py
git commit -m "feat(scripts): add portability linter for hardcoded tool-names"
```

---

## Task 6: Pilot — wire footer into am-research

**Files:**
- Modify: `skills/am-research/SKILL.md`

- [ ] **Step 1: Read current `skills/am-research/SKILL.md`**

Run: `cat skills/am-research/SKILL.md` — note any hardcoded `mcp__*` references and where the footer should go (end of file, before any closing section).

- [ ] **Step 2: Abstract any hardcoded tool references**

Replace any literal `mcp__<x>__<y>` in the body with capability phrasing, e.g. `mcp__jira__*` → "the jira capability (AGENTS.md tool-registry)". If the skill does not currently hardcode tool-names, note that and skip.

- [ ] **Step 3: Append the footer**

Append the contents of `skills/_shared/learning-footer.md` to the end of `skills/am-research/SKILL.md` (copy the block inline — skills are self-contained).

- [ ] **Step 4: Verify the pilot skill passes the linter**

Run: `python scripts/lint-portability.py skills/am-research`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/am-research/SKILL.md
git commit -m "feat(am-research): add operational-learning footer + abstract tool refs"
```

---

## Task 7: Repo-wide portability audit + fix

**Files:**
- Modify (as needed): every `skills/**/SKILL.md` flagged by the linter

- [ ] **Step 1: Run the linter across all skills**

Run: `python scripts/lint-portability.py skills`
Expected: a list of `<file>:<line>: hardcoded tool-name ...` for each violation.

- [ ] **Step 2: Record the baseline count**

Note the count (e.g. `N findings across M files`). This is the P0 portability baseline — capture it for the metrics in the PRD §9.

- [ ] **Step 3: Fix flagged lines (capability phrasing)**

For each finding, edit the line to reference the capability per the tool-registry. Do NOT mass-rewrite unrelated prose — only the flagged tool-name tokens. (Out of scope for P0: skills that legitimately must name a tool — document those as explicit allowlist candidates for P2.)

- [ ] **Step 4: Re-run linter — verify clean (or document exceptions)**

Run: `python scripts/lint-portability.py skills`
Expected: no output (exit 0), or a short documented allowlist of intentional exceptions.

- [ ] **Step 5: Commit**

```bash
git add skills/ scripts/ AGENTS.md
git commit -m "refactor(skills): replace hardcoded tool-names with capability refs (portability P3)"
```

---

## Task 8: P0 documentation + wrap

**Files:**
- Modify: `README.md` (or `CHANGELOG.md` if present)

- [ ] **Step 1: Add a short P0 section to README**

Append to `README.md` (under a new `## Harness: operational learning loop` heading, or existing harness/docs section):

```markdown
### Operational learning loop (P0)

- `learnings/` — operational facts (separate from reflexive `memory/`). See `learnings/README.md`.
- `state/skill-runs.md` — local skill-run telemetry.
- `skills/_shared/learning-footer.md` — standard footer appended to operational skills.
- `AGENTS.md` tool-registry — capability → tool mapping (skills stay tool-agnostic).
- `scripts/lint-portability.py` — CI gate against hardcoded tool-names.

Rollout: footer is on `am-research` (pilot). Roll out to remaining am-* skills incrementally.
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest -q`
Expected: all pass (including the new linter tests).

- [ ] **Step 3: Final commit**

```bash
git add README.md
git commit -m "docs: document P0 operational learning loop + portability linter"
```

---

## Self-review notes

- **Spec coverage (PRD §5 components):** learnings store ✅ Task 1; skill-runs telemetry ✅ Task 2; learning-footer ✅ Task 3; tool-registry ✅ Task 4; linter (portability mini-audit, automated) ✅ Task 5/7; pilot rollout ✅ Task 6. `decisions.active` (P1), OIAE-upgrade (P1), auto-prune + regression-evals (P2) are intentionally out of P0.
- **Placeholder scan:** none — every step has real content or exact commands.
- **Type consistency:** `scan_dir(root: Path) -> list[str]` matches across test + impl; capability names match between tool-registry (Task 4) and footer phrasing (Task 3).

---

## Subsequent plans (not in P0)

- **P1 plan:** `decisions.active.md` store + supersede; OIAE-upgrade of `improve-skill` (Observe→Inspect→Amend→Evaluate→rollback, maker≠checker).
- **P2 plan:** `auto-prune` skill (stale/contradiction, generalizing `am-research-index`); regression-eval seed per skill; optional decay.
- **Rollout plan:** extend learning-footer from `am-research` pilot to all am-* operational skills (mechanical, after P0 lands).
