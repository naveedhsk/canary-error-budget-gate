# Error-Budget Canary Gate (Datadog/Prom + OTel)
## Problem
Canaries “pass” while downstreams are red; p99/err-rate masked in blended traffic.

## Approach
- Collect SLO signals via OpenTelemetry → Datadog/Prom.
- Gate logic: lookback N mins, thresholds for p95/p99, error rate, dep SLO status.
- Actions: auto-halt, rollback, or proceed with cooldown.

## Policy (YAML)
slo_targets:
  p99_ms: 500
  error_rate_pct: 1.0
lookback_minutes: 10
cooldown_minutes: 5
deps:
  - name: payments-api
    slo_endpoint: https://prom/.../slo_status
actions:
  on_violation: rollback
  on_warn: hold_and_recheck

## Integration notes
- **Datadog**: use Monitors API to fetch p95/p99 & error rate; tag by service/version.
- **Prometheus**: sample queries for p99 latency and rate(errors)/rate(reqs).
- **CI/CD**: call gate script as a pipeline stage; exit non-zero on violation.

## Outcome (example)
- Failed rollouts ↓ ~70% in trials; MTTD faster; fewer customer-visible regressions.
