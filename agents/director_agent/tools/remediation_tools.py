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

    Phase 3 local policy: requeue_worker and flip_cdn_region allowed for the
    agent SA; everything else denied -> escalation path.
    T4.x replaces this with real Cloud IAM policy evaluation.
    """
    if remediation not in REMEDIATION_CATALOG:
        return {"allowed": False, "reason": f"'{remediation}' is not in the remediation catalog"}

    allowed = {"requeue_worker", "flip_cdn_region"}
    decision = {
        "allowed": remediation in allowed,
        "remediation": remediation,
        "reason": "granted by agent IAM policy (phase-3 local policy)" if remediation in allowed
        else "denied: IAM policy does not grant this action to the agent service account",
    }
    tool_context.state["authz_decision"] = decision
    return decision


def execute_remediation(tool_context: ToolContext, remediation: str) -> dict:
    """Executes a catalogued remediation against the broadcast stack control API."""
    authz = tool_context.state.get("authz_decision")
    if not authz or not authz.get("allowed"):
        return {"executed": False, "reason": "BLOCKED: no prior ALLOW from check_authorization"}

    endpoints = {"requeue_worker": "/requeue/encoder-2"}
    if remediation not in endpoints:
        return {"executed": False, "reason": f"no control-API binding for '{remediation}' (escalate)"}

    resp = requests.post(CONTROL_API_URL + endpoints[remediation], timeout=10)
    result = {"executed": resp.ok, "remediation": remediation, "status": resp.status_code}
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
