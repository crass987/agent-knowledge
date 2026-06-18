# state/ — harness runtime state (LOCAL ONLY)

Files here record harness runtime data (telemetry, logs). They are **local-only** — never committed, never transmitted. Append-only data files are gitignored.

## skill-runs.md

Lightweight, agent-appended log of skill invocations. Feeds the OIAE "Observe" step (P1) and surfaces dead/failing skills.

Columns: `skill | ts | duration_s | outcome | branch | note`
- `ts`: ISO 8601 UTC (e.g. `2026-06-18T14:03Z`)
- `duration_s`: approximate seconds
- `outcome`: `success` | `fail` | `abort`

The agent appends one row at the end of each skill run (see `skills/_shared/learning-footer.md`).
