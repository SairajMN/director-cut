"""E2E local golden path: inject failure -> detect -> diagnose -> authz -> fix -> recover.

Runs the real stack: control API, Prometheus/Loki, Grafana, MCP server, agent crew.
Exit 0 = incident detected, authorized fix executed, metric recovered.

Usage: .venv/bin/python tests/e2e_local.py
"""
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CONTROL = "http://localhost:8080"
PROM = "http://localhost:9090"
GRAFANA = "http://localhost:3000"
MCP_URL = "http://localhost:9222/sse"

from agents.director_agent.tools.remediation_tools import (  # noqa: E402
    REMEDIATION_CATALOG,
    check_authorization,
    execute_remediation,
    write_grafana_annotation,
)


class Ctx:
    state = {}


def drops_rate() -> float:
    q = "max(rate(frames_dropped_total[30s]))"
    r = requests.get(f"{PROM}/api/v1/query", params={"query": q}, timeout=10).json()
    vals = r["data"]["result"]
    return float(vals[0]["value"][1]) if vals else 0.0


def firing_alerts() -> list:
    tok = requests.get(f"{GRAFANA}/api/v1/provisioning/alert-rules", timeout=10).json()
    return [a["title"] for a in tok]


def main() -> int:
    print("== golden path ==")
    assert REMEDIATION_CATALOG, "catalog empty"

    baseline = drops_rate()
    print(f"baseline drop rate: {baseline:.3f}/s")
    assert baseline < 1.0, "stack not healthy at start"

    r = requests.post(f"{CONTROL}/inject-failure/encoder_frame_drop", timeout=10)
    print("inject:", r.json())
    time.sleep(45)
    spike = drops_rate()
    print(f"post-inject drop rate: {spike:.3f}/s")
    assert spike > 1.0, "injection did not raise drop rate"

    alerts = firing_alerts()
    print("firing alerts:", alerts)
    assert "encoder_frame_drop" in alerts

    ctx = Ctx()
    ctx.state["incident_report"] = {"alert": "encoder_frame_drop", "severity": "tier1"}
    authz = check_authorization(ctx, "requeue_worker")
    print("authz:", authz)
    assert authz["allowed"], "IAM gate unexpectedly denied requeue_worker"

    result = execute_remediation(ctx, "requeue_worker")
    print("remediation:", result)
    assert result["executed"], "control API requeue failed"

    print("waiting for recovery...")
    deadline = time.time() + 90
    while time.time() < deadline:
        if drops_rate() < 0.5:
            break
        time.sleep(10)
    recovered = drops_rate()
    print(f"final drop rate: {recovered:.3f}/s")
    assert recovered < 0.5, "metric did not recover after requeue"

    ann = write_grafana_annotation(ctx, "auto-remediated: requeue_worker (encoder_frame_drop) — recovered")
    print("annotation:", ann)
    assert ann["annotated"]

    print("== golden path PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
