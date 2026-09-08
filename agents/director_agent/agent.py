"""Director — root orchestrator for the broadcast reliability crew."""
from google.adk.agents import LlmAgent

from .prompts import DIRECTOR_PROMPT
from .sub_agents.escalation_agent import escalation_agent
from .sub_agents.remediation_agent import remediation_agent
from .sub_agents.root_cause_agent import root_cause_agent
from .sub_agents.sensor_agent import sensor_agent
from .sub_agents.studio_head_agent import studio_head_agent

root_agent = LlmAgent(
    name="director",
    model="gemini-2.5-flash",
    description="Orchestrates incident response for the live broadcast stack.",
    instruction=DIRECTOR_PROMPT,
    sub_agents=[sensor_agent, root_cause_agent, studio_head_agent, remediation_agent, escalation_agent],
)
