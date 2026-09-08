# Runbook: Encoder frame-drop loop

## Symptoms
- Alert `encoder_frame_drop` firing (Tier 1)
- `rate(frames_dropped_total[30s])` > 5/s on one encoder
- Buffer ratio climbing on the affected channel

## Diagnosis
1. Identify the wedged encoder via `query_prometheus` (max by instance).
2. Check its logs with `query_loki_logs` for repeated "segment re-encode" lines.

## Remediation (T1 — auto-approved)
- `requeue_worker` on the affected encoder. Recovery is expected within ~30s.
- If drops continue after two requeues, escalate: the encoder is likely
  hardware-degraded — do not keep cycling it.
