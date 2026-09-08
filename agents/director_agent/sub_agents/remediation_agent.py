"""Remediation Agent — executes authorized fixes, annotates Grafana."""
from google.adk.agents import LlmAgent

from ..tools.remediation_tools import execute_remediation, write_grafana_annotation
from ..tools.state_tools import get_incident_context

REMEDIATION_PROMPT = """You are the Remediation engineer. Execute what the policy allows.

Input: `authz_decision` (from the Studio Head) and `root_cause_report` in state.

If authz_decision.allowed is true:
1. Call `execute_remediation` with the authorized action. This refuses to run
   without a prior ALLOW — never attempt workarounds.
2. On success, call `write_grafana_annotation` with a one-line summary like
   "auto-remediated: requeue_worker (encoder_frame_drop) — recovered".

If allowed is false: execute NOTHING. Say exactly:
  "REMEDICATION DENIED — escalating" and stop.

Output a JSON dict: {"executed": bool, "action": str, "annotated": bool}
"""

remediation_agent = LlmAgent(
    name="remediation",
    model="gemini-2.5-flash",
    description="Executes authorized remediations and annotates the dashboard.",
    instruction=REMEDIATION_PROMPT,
    tools=[execute_remediation, write_grafana_annotation, get_incident_context],
    output_key="remediation_result",
)
