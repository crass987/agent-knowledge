# C2 Architecture Drift Audit

Detect drift between the C2 architecture document and the actual codebase. Output a structured drift report.

**Standalone trigger:** user says `c2-audit`
**Part of:** `update-all` (see `meta/archive/prompts-legacy/update-all.md`)
**Depends on:** fresh `meta/repos/*.md` profiles (run `refresh-agents` first if stale)

---

## Phase 1 — Parse C2 Document

Read `analytics-hub/internal_docs/docs/Архитектура/C2-контейнеры.md` fully. Extract structured claims.

### 1.1 Extract from «Обзорная диаграмма» (Mermaid graph)

Parse every edge `A --> B` in the top-level Mermaid diagram. Record:

```
{source, target, label}
```

Example: `Agent -->|proxy| Vmauth` → `{source: agent, target: vmauth, label: proxy}`

### 1.2 Extract from «Каталог сервисов» (table)

For each row, extract:

```
{
  service, role, stack,
  incoming,    // «Входящие данные» column
  outgoing,    // «Исходящие данные» column
  dependencies // «Зависимости» column
}
```

### 1.3 Extract from «Базы данных» (table)

```
{database, writers: [service, ...], readers: [service, ...]}
```

### 1.4 Extract from «Потоки данных» (sections 1–9)

For each flow section:
- All participants in Mermaid diagrams
- All interactions (arrows with labels)
- Specific claims: port numbers, protocols, batch sizes, table names, endpoint paths, transformation descriptions (e.g., "pass-through", "normalization")

### 1.5 Build claims index

Consolidate all extracted claims into a single list, grouped by service. This is the "expected state".

### 1.6 Build per-service claim packs

For each service in the claims index, create a compact claim pack:

```
{
  service,
  catalog_entry: {role, stack, incoming, outgoing, dependencies},
  diagram_edges: [{source, target, label}, ...],
  flow_claims: [{flow_section, claim, details}, ...],
  db_claims: {writes_to: [...], reads_from: [...]}
}
```

These packs are the input for per-service subagents in Phase 3.

---

## Phase 2 — Collect Evidence (Bulk)

Gather the evidence that all subagents will need, once. This avoids each subagent reading shared files independently.

### 2.1 Read facts report

Read `meta/reports/facts-{YYYY-MM-DD}.md`. Key sections:

| Section | What it provides |
|---|---|
| Per-repo Dirs/Internal/Make/GoMod | Stack verification, package layout |
| Cross-Repo Reference: Service Ports | Port numbers used in code |
| Cross-Repo Reference: CH Tables | ClickHouse tables from migrations |
| Cross-Repo Reference: Redis Channels | Pub/Sub channels from go-lib |
| **Profile Connections** | External Services + Cross-Repo Context extracted from `meta/repos/*.md` |

### 2.2 Read drift counts

From the facts report, extract drift status per repo:
- `"none"` → repo had zero commits since last profile refresh
- `"N commits since ..."` → repo changed, profile may be stale

Build a drift lookup table: `{service: drift_status}`.

### 2.3 Identify services to audit

Filter services:
- **Must audit**: services with commits since last refresh, or services in C2 claims index
- **Skip**: services not in C2 AND not in `meta/repos/`
- **Low priority**: services with `"none"` drift AND present in C2 (likely no changes, but validate)

---

## Phase 3 — Per-Service Audit (Subagent Pattern)

For each service that needs auditing, spawn a **subagent with clean context**. Each subagent gets only the data relevant to its service — no cross-contamination from other services' claims.

### 3.1 Why subagents

Holding all 15 services' claims + evidence in one context window causes:
- Earlier services' details bleeding into later services' analysis
- Context window pressure degrading analysis quality for later services
- No parallelism opportunity

Per-service subagents solve all three: clean context, parallel execution, consistent analysis quality.

### 3.2 Subagent invocation

Use the `Agent` tool with `subagent_type: "general-purpose"` for each service. Pass:

**Inputs to each subagent:**

```
1. Service name
2. Claim pack from Phase 1.6 (only this service's claims)
3. Profile connections from facts report (only this service's section)
4. Drift status from Phase 2.2
5. Relevant cross-repo data (ports, CH tables, Redis channels)
6. File path to meta/repos/{service}.md (subagent reads it if needed)
7. File path to service's cloned repo (subagent reads code if needed)
```

**Subagent prompt template:**

```
You are auditing a single service for C2 architecture drift.

## Service: {service_name}

## C2 Claims (from architecture document)
{claim_pack}

## Profile Evidence (from meta/repos/{service}.md)
{profile_connections_section}

## Drift Status
{drift_status}

## Cross-Repo Reference Data
- Service ports: {relevant_ports}
- CH tables: {relevant_tables}
- Redis channels: {relevant_channels}

## Your Task

1. Read meta/repos/{service}.md fully (if drift status shows recent changes, also read key source files from the cloned repo)
2. For each claim in the claim pack, classify:
   - ✅ Validated — claim matches evidence
   - ⚠️ Drift — claim partially matches, details differ
   - ❓ Undocumented — evidence in code but missing from C2
   - 👻 Ghost — C2 claims something with no code evidence
   - 🔒 No Access — source not available, cannot validate
3. For each drift/undocumented/ghost, assign severity:
   - HIGH — data flow drift: wrong source/target, missing or extra connection
   - MED — detail drift: wrong port, missing endpoint, undocumented dependency
   - LOW — cosmetic: stack typo, missing comment, stale note
4. Return findings in this exact format:

## {service_name} Findings

### ✅ Validated
- {claim}: {one-line confirmation} — source: {file}

### ⚠️ Drifts
#### [{SEVERITY}] {title}
- **C2 says:** {claim}
- **Code shows:** {evidence}
- **Source:** {file}
- **Fix:** {what to change in C2}

### ❓ Undocumented
- {finding} — source: {file}

### 👻 Ghost
- {claim with no evidence}

### 🔒 No Access
- {claim that couldn't be verified}
```

### 3.3 Parallel execution

Services are independent — audit them in **parallel**. Spawn up to 5 subagents at once (avoid overwhelming the system). Group services by expected complexity:

- **Simple** (profile-only, low drift): agent, snmp-agent, vmclient, license-service, db-migration-service
- **Medium** (some cross-repo connections): config-api, identity-provider, incident-service, admin-console
- **Complex** (many connections, core data flow): clickhouse-adapter, clickhouse-selecter, admin-backend, event-processing, notification-service, go-lib

Process complex services first (they surface the most drift), then medium, then simple.

### 3.4 Collect results

Each subagent returns its findings section. Assemble all results into:
- A per-service findings list (for the drift report)
- A count of validated/drift/undocumented/ghost/no-access statuses

---

## Phase 4 — Generate Report

### 4.1 Output

Write to `meta/reports/c2-drift-{YYYY-MM-DD}.md`.

### 4.2 Template

```markdown
# C2 Architecture Drift Report — {date}

**C2 doc last modified:** {date from history table}
**Evidence freshness:** meta/repos/*.md last refreshed {date}
**Audited:** {N} of {M} services
**Audit method:** per-service subagents with clean context

## Summary

| Status | Count |
|---|---|
| ✅ Validated | {N} |
| ⚠️ Drift | {N} |
| ❓ Undocumented | {N} |
| 👻 Ghost | {N} |
| 🔒 No Access | {N} |

**HIGH severity:** {N}

## Drifts

### ⚠️ [{SEVERITY}] {title}

- **C2 says:** {claim}
- **Code shows:** {evidence}
- **Source:** `{file}` (or meta/repos/{service}.md)
- **Fix:** {what to change in C2}

## Validated

- ✅ **{service}**: {what was checked} — confirmed in meta/repos/{service}.md
(One line per check, grouped by service)

## Not audited

- 🔒 {service}: {reason}
```

### 4.3 Rules

- Every drift must cite a source file. If source unavailable → 🔒, not 👻.
- Do NOT modify C2-контейнеры.md. Report only.
- Ambiguous claims → ✅ with a note. Don't flag ambiguity as drift.
- Group by service, not by flow section.
- One sentence per validated claim. Two sentences per drift.

---

## Phase 5 — Update Evidence Sources

After generating the drift report, update `meta/repos/*.md` where stale.

### 5.1 Cross-reference drift report with profile freshness

For each service where drift was found:
1. Check `meta/repos/{service}.md` — does it reflect current code?
2. If stale, update it (same scope as `skills/am-update/prompts/refresh-agents.md` Step 2)

### 5.2 What to update

Only sections affecting C2 audit accuracy:
- **External Services** table — ports, connections, new/removed dependencies
- **HTTP Endpoints** — new/removed routes
- **Cross-Repo Context** — changed calls/receives-from
- **Architecture** section — changed goroutines, loaders, pipelines

Do NOT rewrite entire profiles — only fix stale sections.

### 5.3 Report profile updates

In the drift report, add:

```markdown
## Profile Updates Applied

- Updated meta/repos/{service}.md: {what was changed}
(If no updates needed, omit this section)
```

---

## Edge Cases

- **Service in repos.yml but not in C2** → report as ❓ HIGH.
- **Service in C2 but no meta/repos file** → fall back to live code. If no cloned repo → 🔒.
- **Feature flags / conditional code** → note but don't flag as drift if C2 describes default behavior.
- **BTM / planned features** → note status change (planned → partial implementation), not drift.
- **Mermaid diagrams** → read source text, extract edges by pattern `A -->|label| B`. Do not parse programmatically.
- **Drift found, but meta/repos is stale** → update the profile FIRST (Phase 5), then re-check. The drift may disappear once the profile reflects current code.
- **Profile update vs C2 fix** → if code is correct and profile was stale, update the profile. If profile is correct and C2 doesn't match, that's a real C2 drift.
- **Subagent returns unexpected format** → re-run that single subagent with stricter prompt. Do NOT manually re-analyze in main context.
