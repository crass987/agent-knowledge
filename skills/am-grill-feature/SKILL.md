---
name: am-grill-feature
description: Use when evaluating a feature idea for Astra Monitoring — "прожарь X", "оцени фичу", "стоит ли делать X", "grill feature", "evaluate". Triggers on feature assessment and prioritization questions.
---

# Grill a Feature

## Overview

Deep evaluation of a feature idea from two angles: product value and technical feasibility. Produces a structured assessment with a clear recommendation.

## When to Use

- User asks whether a feature is worth building
- User wants product + technical assessment of an idea
- User needs to compare or prioritize features

## When NOT to Use

- Just researching how something works → use `am-research`
- Writing requirements → use `am-write-specs`
- Auditing existing docs → use `am-grill-docs`

## Process

### Phase 1: Product Grill

Answer these questions:

1. **Value proposition**: What problem does this solve? For whom? How painful is the problem?
2. **Target users**: Which user segment? Admins, operators, all users?
3. **Alternatives**: How do users solve this problem now? Workarounds? Competitors?
4. **Success metrics**: How would we measure this is working? (adoption, time saved, incidents reduced)
5. **Dependencies**: Does this depend on other features? On external systems?
6. **Risks**: What could go wrong from product perspective? (adoption risk, complexity, scope creep)

### Phase 2: Technical Grill

Read `PM.md` Knowledge Map → identify affected services → read `meta/repos/<service>.md` for each.

Answer these questions:

1. **Affected services**: Which services need changes? List with estimated change scope (small/medium/large)
2. **Complexity**: Based on service profiles — how invasive are the changes?
3. **Shared dependencies**: Does this require go-lib changes? Database schema changes? API contract changes?
4. **Cross-repo coordination**: Do multiple teams need to coordinate? Which services are in active development?
5. **Technical risks**: Performance implications? Data migration needed? Backward compatibility?
6. **Existing foundation**: How much of this already exists in code vs needs to be built from scratch?

### Phase 3: Verdict

Produce a recommendation:

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

### Verdict: DO / DON'T / DO LATER
[2-3 sentences with specific reasoning]

### Conditions (if DO)
- [ ] Prerequisites that must be met first
- [ ] Scope boundaries (what's in/out)

### Open Questions
- [things that need clarification before implementation]
```

## Rules

- Be honest. If a feature is low value or high risk, say so.
- Technical complexity must be based on actual code investigation, not assumptions.
- If you can't assess something, explicitly flag it rather than guessing.
- Always consider the cost of NOT doing the feature.
- Compare against competitor capabilities when relevant (Zabbix, Prometheus, Grafana).
