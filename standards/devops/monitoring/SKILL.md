---
name: devops-monitoring
description: Monitoring, alerting, and observability conventions
---

# Monitoring Standards

## Metrics

- Use the RED method for services: Rate (requests/sec), Errors (%), Duration (latency).
- Use the USE method for resources: Utilization, Saturation, Errors.
- Label metrics with service name, environment, and critical dimensions (e.g., `handler`, `status_code`).

## Alerting

- Alert on symptoms (user-facing impact), not causes (CPU at 80%).
- Every alert must be actionable. If nobody knows what to do, it's a dashboard, not an alert.
- Define severity levels: P1 (page immediately), P2 (page during business hours), P3 (ticket).
- Set alert thresholds based on SLOs, not static values.

## Dashboards

- One dashboard per service with: request rate, error rate, p50/p95/p99 latency.
- Add a "troubleshooting" panel section with top error types and slowest endpoints.
- Use consistent time ranges: default 1h for debugging, 7d for trends.

## Logging

- Structured JSON logs. Include: timestamp, level, message, trace_id, span_id.
- Log levels: ERROR (action needed), WARN (unexpected but handled), INFO (business events), DEBUG (development only).
- Correlate logs with traces using trace_id.

## SLOs

- Define SLOs for critical user journeys: "99.9% of checkout requests complete in <2s."
- Track error budget burn rate, not just raw percentages.
- Review SLOs quarterly with product and engineering.
