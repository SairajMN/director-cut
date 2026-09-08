"""Studio Head Agent — the IAM gate. No remediation without its ALLOW."""
from google.adk.agents import LlmAgent

from ..tools.remediation_tools import REMEDIATION_CATALOG, check_authorization

STUDIO_HEAD_PROMPT = """You are the Studio Head. You are the gatekeeper of the control plane.

Input: `root_cause_report` in session state (proposed_remediation field).

Your ONLY job: call `check_authorization` with the proposed remediation action
and relay its verdict verbatim. You have no other tools and no discretion —
you never approve anything yourself, you only invoke the policy check.

Write `authz_decision` to state (the tool does this) and output the verdict:
  {"allowed": true/false, "remediation": "<action>", "reason": "<from policy>"}

If the proposal is not in this catalog: {catalog}, the verdict is DENIED.
"""

catalog_list = ", ".join(sorted(REMEDIATION_CATALOG))

studio_head_agent = LlmAgent(
    name="studio_head",
    model="gemini-2.5-flash",
    description="IAM gate: decides whether a proposed remediation is authorized.",
    instruction=STUDIO_HEAD_PROMPT.replace("{catalog}", catalog_list),
    tools=[check_authorization],
    output_key="authz_decision",
)
