# Runbook: Origin overload / viewer surge

## Symptoms
- Buffer ratio rising on all channels simultaneously
- Encoder latency increasing but no drops yet

## Diagnosis
1. Confirm surge: `query_prometheus` on viewer count vs encode latency.
2. Verify no single encoder is the bottleneck (should be distributed).

## Remediation (T2 — requires human approval)
- `scale_encoder_pool` spends money (autoscaler). Propose with current/max
  replica counts and wait for Studio Head approval. Never auto-scale.
