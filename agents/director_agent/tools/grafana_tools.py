"""Grafana MCP toolset for ADK — the ONLY observability access path for agents (Decision #1)."""
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

MCP_URL = "http://localhost:9222/sse"

# v1.3.0 mcp-grafana names; read-only + annotation writes only (Decision #2/#3 friendly)
GRAFANA_TOOLS = [
    "query_prometheus",
    "query_loki_logs",
    "alerting_manage_rules",   # operation=list == list alert rules
    "list_alert_groups",
    "get_annotations",
    "create_annotation",
    "list_datasources",
]


def get_grafana_toolset() -> McpToolset:
    return McpToolset(
        connection_params=SseConnectionParams(url=MCP_URL),
        tool_filter=GRAFANA_TOOLS,
    )
