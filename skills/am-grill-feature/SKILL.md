---
name: am-grill-feature
description: Use when evaluating any feature idea for Astra Monitoring — product value, technical feasibility, competitive positioning. Triggers on "grill", "evaluate", "should we build X", "is X worth it", "оцени фичу", "прожарь", "стоит ли делать", "критикуй фичу", feature assessment, prioritization. Works for product features, technical changes, and architectural proposals within the AM ecosystem.
---

# Grill a Feature

## Overview

Deep evaluation of a feature idea from two angles: **product value** and **technical feasibility**. Produces a structured markdown artifact with a clear recommendation (DO / DON'T / DO LATER).

The "feature" can be anything: a new dashboard, a backend service change, an integration, a UX improvement, or an architectural proposal — anything within the Astra Monitoring product.

## When to Use

- User asks whether a feature is worth building
- User wants product + technical assessment of an idea
- User needs to compare or prioritize features
- User says "grill this", "evaluate X", "should we build X", "is it worth it"

## When NOT to Use

- Just researching how something works → use `am-research`
- Writing requirements / specs → use `am-write-specs`
- Auditing or critiquing an existing document → use `am-grill-docs`
- Mining pain points from client conversations → use `am-pain-mining`

## Process

### Step 0: Clarify What You're Evaluating

**CRITICAL.** Do not skip this step.

The input might be a feature name, a document, a Jira ticket, a client question, or a vague idea. Before grilling:

1. **Identify the feature**: What exactly is being evaluated? Name it in one sentence.
2. **Check scope**: Is this a product feature, a technical change, or an architectural proposal?
3. **Extract, don't evaluate the container**: If the user provides a document — extract the feature FROM the document. Don't critique the document itself.

**If unclear which feature to evaluate — ask the user before proceeding.**

### Phase 1: Product Grill

Research and answer these questions:

1. **Value proposition**: What problem does this solve? For whom? How painful is the problem? Find evidence — user requests, support tickets, client feedback.
2. **Target users**: Which user segment? Admins, operators, DevOps, managers (like Pavel-type decision makers)? How many users affected?
3. **Alternatives**: How do users solve this problem now? Workarounds? Competitors?
4. **Success metrics**: How would we measure this is working? (adoption %, time saved, incidents reduced, MTTR improved)
5. **Dependencies**: Does this depend on other features? On external systems? On specific infrastructure?
6. **Risks**: What could go wrong? (adoption risk, complexity, scope creep, cannibalization)

**Research instructions:**
- Use the **web-search** capability (see `AGENTS.md` tool-registry) for competitor analysis and market context
- Compare against: Zabbix, Prometheus+Grafana, Datadog, Icinga, VictoriaMetrics ecosystem — whichever is relevant
- Include source links in the output
- Check existing PM docs (`docs/`, Confluence) for prior art

### Phase 2: Technical Grill

Investigate the actual codebase. Don't assume — verify.

**Investigation path:**
1. Read `PM.md` Knowledge Map → identify affected services
2. For each service: read `meta/repos/<service>.md` for architecture profile
3. Use code exploration (Grep, Glob, Read) to verify claims against real code
4. Use Explore agent for broad investigation across services

**Answer these questions:**

1. **Affected services**: Which services need changes? List with estimated change scope (small/medium/large)
2. **Complexity**: How invasive are the changes? Based on actual service profiles, not gut feeling
3. **Shared dependencies**: Does this require go-lib changes? Database schema changes? API contract changes?
4. **Cross-repo coordination**: Do multiple teams need to coordinate? Which services are in active development?
5. **Technical risks**: Performance implications? Data migration needed? Backward compatibility? Security?
6. **Existing foundation**: How much already exists vs needs to be built from scratch?

### Phase 3: Verdict

Produce a structured markdown artifact and save it under `PM/` per the routing test in `PM/CLAUDE.md`: a feature grill → `PM/initiatives/<theme>/`; a competitive grill → `PM/competitive/`. Never into `meta/`.

**Output template:**

```
## Feature: [name]

### Product Assessment
| Criterion | Rating | Notes |
|---|---|---|
| User value | High/Medium/Low | ... |
| Urgency | High/Medium/Low | ... |
| Risk | High/Medium/Low | ... |

### Technical Assessment
| Criterion | Rating | Notes |
|---|---|---|
| Complexity | High/Medium/Low | ... |
| Services affected | N services | ... |
| Coordination needed | Yes/No | ... |
| Data migration | Yes/No | ... |

### Competitive Context
[What competitors offer in this area. Links to sources.]

### Verdict: DO / DON'T / DO LATER
[2-3 sentences with specific reasoning]

### Conditions (if DO)
- [ ] Prerequisites that must be met first
- [ ] Scope boundaries (what's in/out)

### Open Questions
- [things that need clarification before implementation]
```

## Rules

- **Output in Russian.** The final artifact must be written in Russian. Section headers, assessments, verdict, conditions, open questions — everything in the saved markdown file is in Russian. Source URLs and code identifiers stay in their original form.
- **Be honest.** If a feature is low value or high risk, say so. The goal is truth, not optimism.
- **Investigate, don't assume.** Technical complexity must be based on actual code investigation.
- **Flag unknowns.** If you can't assess something, explicitly flag it rather than guessing.
- **Consider the cost of NOT doing the feature.** What happens if we skip it?
- **Output location.** Save product output under `PM/` per the routing test in `PM/CLAUDE.md` (theme-specific → `PM/initiatives/<theme>/`; competitive → `PM/competitive/`; untethered one-off → `PM/sessions/`; disposable → `PM/tmp/`). Never write product artifacts into `meta/` — `meta/` is meta-repo infrastructure only.
- **Use external research.** Include source links for competitive and market claims.
- **The feature is what's evaluated** — not the document, ticket, or conversation that mentions it.

## Operational learning (run before finishing)

If this run surfaced a durable operational lesson that would save 5+ minutes next time — an unexpected command quirk, a tool gotcha, a project-specific fact — append it to the matching file in `agent-knowledge/learnings/` (`patterns.md` / `pitfalls.md` / `preferences.md` / `operational.md`), using the frontmatter format in `learnings/README.md`.

Gate: do NOT log obvious facts, one-off transient errors, or anything already in this skill.

Then append one row to `agent-knowledge/state/skill-runs.md`: skill name, ISO timestamp, approximate duration in seconds, outcome (success/fail/abort), branch, optional note.

Both stores are local-only; never transmit externally.
