"""E2E blocked path: tier-3 incident proposed -> policy DENIES -> ticket produced.

Simulates a cdn_multi_region_latency incident where the model's proposed fix is
purge_cdn_cache (T3: blocked). Verifies: DENIED verdict, no execution, ticket JSON.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.director_agent.tools.remediation_tools import (  # noqa: E402
    check_authorization,
    execute_remediation,
)
from agents.director_agent.tools.ticket_tools import TICKETS_DIR, create_incident_ticket  # noqa: E402


class Ctx:
    state = {}


def main() -> int:
    print("== blocked path ==")

    ctx = Ctx()
    ctx.state["incident_report"] = {"alert": "cdn_multi_region_latency", "severity": "tier3"}

    verdict = check_authorization(ctx, "purge_cdn_cache")
    print("verdict:", verdict)
    assert verdict["allowed"] is False and verdict["tier"] == "T3"

    attempt = execute_remediation(ctx, "purge_cdn_cache")
    print("execution attempt:", attempt)
    assert attempt["executed"] is False, "BLOCKED action must never execute"

    ticket = create_incident_ticket(
        title="cdn_multi_region_latency — needs human: purge_cdn_cache",
        body="Multi-region CDN latency breach.\nRoot cause: unhealthy region (see root_cause_report).\n"
             f"Action required: {verdict['reason']}",
        incident="cdn_multi_region_latency",
    )
    print("ticket:", ticket)
    data = json.loads(Path(ticket["ticket_path"]).read_text())
    assert data["escalated"] is True and "purge_cdn_cache" in data["title"]

    print("== blocked path PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
