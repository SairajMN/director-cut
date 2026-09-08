# Runbook: Loki ingestion gap

## Symptoms
- `query_loki_logs` returns nothing for a worker that is definitely up
- Grafana logs panel empty for one container

## Diagnosis
1. `check_datasources_health` via MCP — Loki datasource may be degraded.
2. `docker logs <worker>` directly (operator only) to confirm emission.

## Remediation (T1 — auto-approved)
- Restart the shipping side only if health check confirms Loki is reachable;
  otherwise escalate — a dead Loki means we are flying blind.
