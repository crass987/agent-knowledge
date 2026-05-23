---
name: incident-response
description: Incident response and postmortem process
---

# Incident Response Skill

## When to use

- Production outage, degradation, or data issue.
- SEV-level alert triggered.

## Response phases

```
1. DETECT  — Alert fires or user reports come in.
2. TRIAGE  — Assess severity and scope. Assign incident commander.
3. COMMUNICATE — Notify stakeholders. Open incident channel.
4. MITIGATE — Stop the bleeding. Rollback, feature flag off, scale up.
5. RESOLVE — Fix the root cause. Verify recovery.
6. REVIEW  — Postmortem within 48 hours.
```

## Severity levels

| Level | Impact | Response time |
|-------|--------|---------------|
| SEV1 | Full outage or data loss | Page immediately |
| SEV2 | Degraded for many users | Page during business hours |
| SEV3 | Minor impact, workaround exists | Next business day |

## Communication template

```
**[SEV level] - [Brief description]**
When: [timestamp UTC]
Impact: [who/what affected]
Status: [investigating/mitigating/resolved]
Current actions: [what's being done]
Next update: [time]
```

## Postmortem

- Blameless. Focus on systems and processes, not people.
- Include: timeline, root cause, impact (users/duration/revenue), what went well, what to improve.
- Every action item must have an owner and deadline.
- Share postmortem with the wider team within 1 week.

## References

See `references/` for incident communication templates and postmortem examples.
