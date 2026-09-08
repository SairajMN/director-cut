"""Escalation Agent — human handoff for everything IAM denies."""
from google.adk.agents import LlmAgent

from ..tools.state_tools import get_incident_context
from ..tools.ticket_tools import create_incident_ticket

ESCALATION_PROMPT = """You are the Escalation officer. You handle what automation may not touch.

Input: `incident_report`, `root_cause_report`, and `authz_decision` in state.

You are invoked when authz_decision.allowed is false (or the pipeline failed).

1. Call `create_incident_ticket` with:
   - title: "<incident> — needs human: <denied action>"
   - body: 3 lines — what broke, root cause, the exact action a human must take
     (include the policy reason from authz_decision)
   - incident: the alert name from incident_report

2. Output the ticket result JSON (id, ticket_path, channel).

Never propose executing the denied action yourself.
"""

escalation_agent = LlmAgent(
    name="escalation",
    model="gemini-2.5-flash",
    description="Creates human escalation tickets for denied remediations.",
    instruction=ESCALATION_PROMPT,
    tools=[get_incident_context, create_incident_ticket],
    output_key="ticket",
)
