# C2 Architecture Drift Fix

Turn confirmed C2 drifts into applied edits (code-wins) or queued decisions (product-decision). Maker≠checker (P9).

**Standalone trigger:** user says `c2-fix`
**Part of:** `am-update` Stage 3
**Depends on:** fresh `meta/reports/c2-drift-YYYY-MM-DD.md` (run `c2-audit` first)

---

## Phase 1 — Load + classify

Read `meta/reports/c2-drift-<date>.md`. For each ⚠️ Drift / ❓ Undocumented / 👻 Ghost, classify:

- **code-wins** → auto-fix candidate. Code/facts unambiguous, C2 simply wrong/stale. Examples: wrong port, missing/extra connection with clear code evidence, count off ("37"→"36"), stale note.
- **product-decision** → queue. Needs a human/product call. Examples: ambiguous behavior, feature-flag conditional, planned→partial, "should this even be in C2".

Record classification + one-line rationale per drift.

## Phase 2 — Maker (per code-wins drift)

Spawn a **maker subagent** (`Agent`, `subagent_type: "general-purpose"`, clean context) per code-wins drift. Inputs: the drift (C2 says / Code shows / Source), path to `analytics-hub/internal_docs/docs/Архитектура/C2-контейнеры.md`, relevant code/facts. Maker returns the **exact edit** (old → new text in C2) + evidence relied on.

Up to 5 makers in parallel. HIGH severity first.

## Phase 3 — Checker (per proposed edit)

Spawn a **separate checker subagent** (clean context, NOT the maker) per proposed edit. Checker:
1. Re-verifies the edit against code/facts independently.
2. Re-checks classification: if actually a product-decision → REJECT, route to review queue.
3. Returns `APPROVE` or `REJECT <reason>`.

Only APPROVED edits proceed.

## Phase 4 — Apply + report

Apply APPROVED edits to `analytics-hub/internal_docs/docs/Архитектура/C2-контейнеры.md`. For REJECTED + product-decision drifts, append to `meta/reports/review-queue.md` under `## Open`:

```
- [open] **[<service>]** <drift title> — source: c2-drift-<date> · 📅 opened <date> · 🔎 <rationale>
```

Write `meta/reports/c2-fix-summary-<date>.md`:

```markdown
# C2 Fix Summary — {date}
- Auto-fixed (code-wins, checker-approved): N
- Queued (product-decision / checker-rejected): M
## Applied edits
- [<service>] <what changed in C2> — checker: APPROVE
## Queued
- [<service>] <drift> — 🔎 <rationale>
```

Commit C2 edits + c2-fix-summary + review-queue updates.

## Edge cases

- **No source access** (🔒) → queue, never guess.
- **Edit rewires a whole flow** (broad semantic change) → queue even if code-wins; flag HIGH-for-review in summary.
- **Maker/checker disagree on facts** → REJECT, queue.
