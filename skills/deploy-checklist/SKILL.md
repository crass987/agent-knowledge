---
name: deploy-checklist
description: Pre-deploy and post-deploy checklist
---

# Deploy Checklist Skill

## When to use

- Before deploying to staging or production.
- After deploying to verify success.

## Pre-deploy

- [ ] All tests pass (unit + integration).
- [ ] No outstanding PR review comments.
- [ ] Migration scripts tested against production-like data.
- [ ] Feature flags configured for gradual rollout (if applicable).
- [ ] Rollback plan documented (command or revert PR ready).
- [ ] Monitoring dashboards and alerts are in place.
- [ ] Notify stakeholders if the deploy affects users.

## Deploy

- [ ] Deploy to staging first. Run smoke tests.
- [ ] Deploy to production with monitoring open.
- [ ] If using feature flags: enable for internal users first, then gradual % rollout.

## Post-deploy

- [ ] Check error rates in monitoring (compare to baseline).
- [ ] Verify critical user paths work (login, purchase, core flow).
- [ ] Check logs for warnings or unexpected messages.
- [ ] If issues found: rollback first, investigate second.

## Rollback criteria

Decide BEFORE deploying:
- What error rate triggers a rollback? (e.g., >5% 5xx responses)
- What latency threshold? (e.g., p99 > 2s)
- How long to wait before calling it stable? (e.g., 30 minutes)

## Scripts

See `scripts/` directory for deploy and rollback automation templates.
