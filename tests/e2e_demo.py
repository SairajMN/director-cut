"""Scripted demo driver — clean timing for the 3-min video recording.

Scenario A: encoder_frame_drop (Tier-1) -> auto-remediation -> recovery + annotation.
Scenario B: cdn_multi_region_latency (Tier-3) -> DENIED -> escalation ticket.

Events stream to the war-room UI (UI_URL, default localhost:8090).
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.director_agent.tools.remediation_tools import (  # noqa: E402
    check_authorization,
    execute_remediation,
)
from agents.director_agent.tools.ticket_tools import create_incident_ticket  # noqa: E402
from tools.bigquery_tools import write_post_mortem  # noqa: E402

CONTROL = os.environ.get("CONTROL_API", "http://localhost:8080")
UI = os.environ.get("UI_URL", "http://localhost:8090")
PROM = "http://localhost:9090"


class Ctx:
    state = {}


def event(actor: str, text: str, kind: str = "info") -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {actor}: {text}")
    try:
        requests.post(f"{UI}/api/event", json={"actor": actor, "text": text, "kind": kind}, timeout=3)
    except requests.RequestException:
        pass


def wait_healthy(node: str, timeout_s: int = 120) -> bool:
    expr = f'max(rate(frames_dropped_total{{worker="{node}"}}[30s]))'
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(f"{PROM}/api/v1/query", params={"query": expr}, timeout=5).json()
        series = r["data"]["result"]
        if not series or float(series[0]["value"][1]) < 0.5:
            return True
        time.sleep(10)
    return False


def scenario_a() -> None:
    event("director", "SCENARIO A — encoder_frame_drop (Tier-1)")
    requests.post(f"{CONTROL}/inject-failure/encoder_frame_drop", timeout=5)
    time.sleep(20)
    rate = requests.get(f"{PROM}/api/v1/query",
                        params={"query": 'max(rate(frames_dropped_total[30s]))'}, timeout=5).json()
    event("sensor", f"ALERT FIRING: encoder_frame_drop (rate={rate['data']['result'][0]['value'][1][:5]}/s)")

    ctx = Ctx()
    ctx.state["incident_report"] = {"alert": "encoder_frame_drop", "worker": "encoder-2"}
    verdict = check_authorization(ctx, "requeue_worker")
    event("studio_head", f"authz: {verdict['reason']}")
    result = execute_remediation(ctx, "requeue_worker")
    event("remediation", f"requeue encoder-2 -> {result}")
    event("root_cause", "Runbook match: frame-drop loop playbook (T5.2 RAG)")

    if wait_healthy("encoder-2"):
        event("director", "RECOVERED — frame drops back to baseline. Post-mortem written to BigQuery.")
        write_post_mortem("encoder_frame_drop", "encoder_frame_drop",
                          "frame-drop loop on encoder-2", "requeue_worker",
                          str(verdict["reason"]))
    else:
        event("director", "WARNING: recovery not confirmed in window")


def scenario_b() -> None:
    event("director", "SCENARIO B — cdn_multi_region_latency (Tier-3)")
    requests.post(f"{CONTROL}/inject-failure/cdn_multi_region", timeout=5)
    time.sleep(15)
    event("sensor", "ALERT FIRING: cdn_multi_region_latency (global blast radius)")

    ctx = Ctx()
    ctx.state["incident_report"] = {"alert": "cdn_multi_region_latency", "severity": "tier3"}
    verdict = check_authorization(ctx, "purge_cdn_cache")
    event("studio_head", f"DENIED — {verdict['reason']}")
    attempt = execute_remediation(ctx, "purge_cdn_cache")
    assert attempt["executed"] is False
    ticket = create_incident_ticket(
        title="cdn_multi_region_latency — needs human: purge_cdn_cache",
        body="Multi-region CDN latency breach.\nRoot cause: unhealthy region.\n"
             f"Action required: {verdict['reason']}",
        incident="cdn_multi_region_latency",
    )
    event("escalation", f"Ticket {Path(ticket['ticket_path']).stem} filed -> war-room queue", "human")
    requests.post(f"{CONTROL}/flip-cdn", timeout=5)  # human fixes it for the demo
    event("human", "Human approved CDN failover (demo). Streams green.")


def main() -> int:
    event("director", "Director's Cut demo starting — crew online")
    scenario_a()
    time.sleep(5)
    scenario_b()
    event("director", "Demo complete. Auto-remediate what IAM allows; escalate what it doesn't.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
