# Runbook: Prometheus target scrape failures

## Symptoms
- Stale metrics; alerts stop evaluating or fire on old data
- `up == 0` for one or more workers

## Diagnosis
1. `query_prometheus` on `up` by job to find failed targets.
2. Check whether the worker container restarted (target URL changed).

## Remediation (T1 — auto-approved)
- Re-register target via control API if the worker is healthy.
- If the worker itself is down, follow encoder-frame-drop-loop instead.
