"""Pure-Python IAM policy evaluator. No LLM — deterministic governance."""
from functools import lru_cache
from pathlib import Path

import yaml

POLICY_PATH = Path(__file__).resolve().parent.parent / "policy" / "iam_policy.yaml"


@lru_cache(maxsize=1)
def load_policy() -> dict:
    with open(POLICY_PATH) as f:
        return yaml.safe_load(f)


def check_authorization(remediation: str, caller: str | None = None) -> dict:
    """Evaluates the catalog. Returns a verdict dict; NEVER executes anything."""
    policy = load_policy()
    entry = policy["remediations"].get(remediation)
    if entry is None:
        return {
            "allowed": False,
            "tier": "UNKNOWN",
            "reason": f"'{remediation}' is not in the remediation catalog",
        }

    tier = entry["tier"]
    sa = caller or policy["service_account"]
    if tier == "T1" and sa in entry["grants"]:
        return {"allowed": True, "tier": tier, "reason": f"auto-approved: {entry['scope']}"}
    if tier == "T2":
        return {
            "allowed": False,
            "tier": tier,
            "reason": f"requires human approval: {entry.get('reason', 'T2 approval flow')}",
            "escalate": True,
        }
    return {
        "allowed": False,
        "tier": tier,
        "reason": entry.get("reason", "blocked by policy"),
        "escalate": True,
    }
