---
name: product-metrics
description: Product metrics, KPIs, and analytics conventions
---

# Product Metrics Standards

## Metric hierarchy

1. **North Star metric** — one metric that reflects core product value.
2. **Driver metrics** — 3-5 metrics that directly influence the North Star.
3. **Supporting metrics** — diagnostic metrics for specific features or funnels.

## Metric design

- Every metric needs a clear definition, calculation, data source, and owner.
- Distinguish rate metrics (% of total) from count metrics (absolute number).
- Use cohort-based analysis for retention and engagement — not aggregate totals.
- Define guardrail metrics: what must NOT decrease when optimizing the target metric.

## Dashboards

- One dashboard per product area with: current value, trend (7d/30d), and target.
- Include confidence intervals for volatile metrics.
- Annotate dashboards with known events (launches, outages, holidays).

## Funnel analysis

- Map the full user journey: acquisition → activation → retention → revenue → referral.
- Measure step-to-step conversion rates, not just total conversion.
- Break down funnels by segment (platform, geography, user type) to find disparities.

## Experimentation

- Define hypothesis, primary metric, and minimum detectable effect before running experiments.
- Run tests for full statistical significance. Don't peek at results early.
- Document learnings regardless of outcome — failed experiments are valuable data.
