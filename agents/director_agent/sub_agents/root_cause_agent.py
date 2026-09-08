"""Root-Cause Agent — second pipeline stage. Writes `root_cause_report` to state."""
from google.adk.agents import LlmAgent

from ..tools.grafana_tools import get_grafana_toolset
from ..tools.state_tools import get_incident_context


def search_runbooks(query: str) -> dict:
    """Placeholder runbook search. Replaced by BigQuery RAG in T5.2."""
    runbooks = {
        "encoder_frame_drop": "Runbook ENC-101: frame drops correlate with encoder input burst; standard fix is requeue_worker.",
        "cdn_multi_region_latency": "Runbook CDN-201: multi-region latency spike indicates unhealthy region; standard fix is flip_cdn_region.",
    }
    for key, text in runbooks.items():
        if key in query or query in key:
            return {"runbook": text}
    return {"runbook": None, "note": "no matching runbook yet (T5.2 pending)"}


ROOT_CAUSE_PROMPT = """You are the Root-Cause analyst for broadcast incidents.

Input: `incident_report` in session state (from the Sensor).

Steps:
1. Call `search_runbooks` with the incident alert name to get the known fix pattern.
2. Gather evidence: range-query the suspect metric via `query_prometheus` and
   recent logs via `query_loki_logs` (last 15 minutes, step 15).
3. Compare evidence against the runbook and rank ONE hypothesis.

Write `root_cause_report` to state as a dict:
  hypothesis: one sentence
  evidence: list of 2-4 concrete items (query + observed value, or log line)
  confidence: "high" | "medium" | "low"
  proposed_remediation: exactly one action name from the runbook, or "manual"

Evidence must cite real query results. Never invent numbers.
"""

root_cause_agent = LlmAgent(
    name="root_cause",
    model="gemini-2.5-flash",
    description="Diagnoses incidents into a ranked hypothesis with evidence.",
    instruction=ROOT_CAUSE_PROMPT,
    tools=[get_grafana_toolset(), get_incident_context, search_runbooks],
    output_key="root_cause_report",
)
