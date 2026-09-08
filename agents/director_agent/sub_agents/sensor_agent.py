"""Sensor Agent — first pipeline stage. Writes `incident_report` to state."""
from google.adk.agents import LlmAgent

from ..tools.grafana_tools import get_grafana_toolset
from ..tools.state_tools import get_incident_context

SENSOR_PROMPT = """You are the Sensor. Detect and characterize live broadcast incidents.

Steps:
1. Call `list_alerts` (alerting_manage_rules with operation=list) to find FIRING alert rules.
2. For any firing rule, pull the underlying metric via `query_prometheus`
   (e.g. rate(frames_dropped_total[30s])) to quantify severity.
3. Optionally pull recent encoder/CDN logs via `query_loki_logs` for symptoms.
4. Call `get_incident_context` to merge what you found with the failing-scenario hint.

Then write the final report to session state key `incident_report` as a dict:
  alert: alert rule title
  metric: the PromQL you queried
  value: current offending value
  severity: "tier1" | "tier2" | "tier3"  (from the alert's tier label)
  summary: one-sentence factual description

Output ONLY the report JSON after your final tool call. No recommendations.
"""

sensor_agent = LlmAgent(
    name="sensor",
    model="gemini-2.5-flash",
    description="Gathers live incident facts from Grafana and writes incident_report.",
    instruction=SENSOR_PROMPT,
    tools=[get_grafana_toolset(), get_incident_context],
    output_key="incident_report",
)
