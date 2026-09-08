"""Remediation tools — fixed catalog + forced IAM authorization gate (Decisions #2, #3)."""
import os

import requests
from google.adk.tools import ToolContext

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
CONTROL_API_URL = os.environ.get("CONTROL_API_URL", "http://localhost:8080")

# Decision #3: the remediation catalog is a FIXED enum. Nothing outside this
# set can ever be executed, regardless of what the model proposes.
REMEDIATION_CATALOG = frozenset({
    "requeue_worker",
    "flip_cdn_region",
    "scale_encoder_pool",
    "purge_cdn_cache",
})


def check_authorization(tool_context: ToolContext, remediation: str) -> dict:
    """IAM gate. FORCED before every execute_remediation call (Decision #2).

    Delegates to the pure-Python policy evaluator (T4.1) — deterministic,
    no LLM in the authorization path. Writes the verdict to state.
    """
    from tools.policy_tools import check_authorization as evaluate

    verdict = evaluate(remediation)
    tool_context.state["authz_decision"] = verdict
    if verdict.get("escalate"):
        tool_context.state["escalate"] = True
    return verdict


def execute_remediation(tool_context: ToolContext, remediation: str) -> dict:
    """Executes a catalogued remediation against the broadcast stack control API."""
    authz = tool_context.state.get("authz_decision")
    if not authz or not authz.get("allowed"):
        return {"executed": False, "reason": "BLOCKED: no prior ALLOW from check_authorization"}

    endpoints = {"requeue_worker": ("requeue/encoder-2", {})}
    if remediation not in endpoints:
        return {"executed": False, "reason": f"no control-API binding for '{remediation}' (escalate)"}

    endpoint, payload = endpoints[remediation]
    from tools.tasks_tools import dispatch_remediation

    dispatch = dispatch_remediation(endpoint, payload)
    result = {
        "executed": dispatch.get("queued") or 200 <= dispatch.get("status", 0) < 300,
        "remediation": remediation,
        "via": "cloud_tasks" if dispatch.get("queued") else "direct",
        "dispatch": dispatch,
    }
    tool_context.state["remediation_result"] = result
    return result


def write_grafana_annotation(tool_context: ToolContext, text: str, tags: str = "directors-cut") -> dict:
    """Annotates the Grafana dashboard so the demo shows the agent acting."""
    import json

    token = os.environ.get("GRAFANA_SA_TOKEN", "")
    resp = requests.post(
        f"{GRAFANA_URL}/api/annotations",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps({"text": text, "tags": tags.split(",")}),
        timeout=10,
    )
    return {"annotated": resp.ok, "status": resp.status_code}
