"""Session-state tools shared by the crew."""
from google.adk.tools import ToolContext

STATE_HINT_KEY = "scenario_hint"


def get_incident_context(tool_context: ToolContext) -> dict:
    """Returns the current scenario hint (injected by tests/ops) and any prior state."""
    state = tool_context.state
    return {
        "scenario_hint": state.get(STATE_HINT_KEY, "none"),
        "has_incident_report": "incident_report" in state,
        "has_root_cause_report": "root_cause_report" in state,
        "authz_decision": state.get("authz_decision"),
    }
