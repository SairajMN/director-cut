# Runbook: CDN multi-region latency

## Symptoms
- Alert `cdn_multi_region_latency` firing (Tier 3)
- `cdn_p99_latency_ms` > 400ms sustained across regions

## Diagnosis
1. Compare per-region p99 with `query_prometheus` (by region label).
2. Confirm whether one region is an outlier or all regions degraded.

## Remediation
- Single-region outlier: **T3 — BLOCKED**. Purging CDN cache has global blast
  radius; page the on-call engineer with the region and evidence.
- All regions: check origin health first (encoder pool) before touching CDN.
