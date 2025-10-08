# Error-Budget Canary Gate (Datadog/Prom + OTel)

**Problem**  
Canaries “pass” while downstreams are red; p99/err-rate masked in blended traffic.

**Approach**  
Collect SLO signals via OpenTelemetry → Datadog/Prom.  
Gate logic: lookback N mins, thresholds for p95/p99, error rate, dep SLO status.  
Actions: auto-halt, rollback, or proceed with cooldown.

**Quickstart (local, no K8s needed)**
```bash
make up          # start Prometheus (:9090) + Grafana (:3000) + OTel
make app         # run Go sample at :8080
make load        # send traffic
make gate        # evaluate SLOs via Prometheus -> OK/WARN/VIOLATION
```

**Policy (YAML)**
See `config/policy.yaml`

**CI/CD**
Use `gate/gate.py` in a pipeline stage; non-zero exit on violation.

**Outcome (example)**
Failed rollouts ↓ ~70% in trials; MTTD faster; fewer customer-visible regressions.

**Screenshots to add later**
- Prometheus p99 spike
- Gate JSON output
- (Optional) Argo Rollouts blocked step
