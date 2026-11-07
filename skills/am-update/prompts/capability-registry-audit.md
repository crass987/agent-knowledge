# Capability Registry Drift Audit

Detect drift between the capability registry and the actual product (`analytics-hub/internal_docs` + code). Output a structured drift report.

**Standalone trigger:** user says `capability-registry-audit`
**Part of:** `am-update` (Stage 4 — see `agent-knowledge/skills/am-update/SKILL.md`)
**Source of truth:** `PM/strategy/functional-registry.md` (PM is a sibling repo, NOT synced by Stage 0 — maintained directly).
**Depends on:** fresh `analytics-hub` (Stage 0 `sync-repos.sh --force`).

---

## Phase 1 — Run the validator (deterministic)

```bash
python3 meta/scripts/capability_registry_check.py PM/strategy/functional-registry.md analytics-hub/internal_docs
```

Collect every `❌` line. Error codes: `bad_id`, `bad_status`, `empty_proof`, `ne_naideno_requires_overclaim`, `broken_link` (a `доказательство` path that no longer exists under `internal_docs`).

## Phase 2 — Detect graduations (LLM judgment)

For rows with status `роадмап` or `Частично / с оговоркой`: grep the feature name across `analytics-hub/internal_docs/docs/` (not only `improvements/`). If a feature now has a GA page/doc → candidate to upgrade (`роадмап`→`Поддерживается`, or narrow the `Частично` caveat). A `Поддерживается` row whose `доказательство` path disappeared = the feature may have been removed/renamed → flag.

## Phase 3 — Output

`meta/reports/capability-registry-drift-<date>.md`. One entry per finding:

```
- [code-wins|judgment] **<fn-slug or feature>** <what changed> → <proposed edit> · source: <validator|grep>
```

Report-only — do NOT edit the registry in this stage (that is `-fix`).
