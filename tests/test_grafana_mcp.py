"""Runtime proof that agents talk to Grafana via MCP — partner-integration evidence.

Requires: simulator stack up + MCP server running (mcp/start_mcp.sh).
"""
import json

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_URL = "http://localhost:9222/sse"


@pytest.fixture
def mcp_tools():
    async def _get():
        async with sse_client(MCP_URL) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return [t.name for t in (await s.list_tools()).tools]
    return asyncio_run(_get())


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


def _text(result) -> str:
    return "".join(c.text for c in result.content if c.type == "text")


def _call(name: str, args: dict) -> str:
    async def _run():
        async with sse_client(MCP_URL) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return _text(await s.call_tool(name, args))
    return asyncio_run(_run())


def test_mcp_server_lists_grafana_tools(mcp_tools) -> None:
    for tool in ("query_prometheus", "query_loki_logs", "alerting_manage_rules", "create_annotation"):
        assert tool in mcp_tools, f"{tool} missing from MCP server"


def test_mcp_list_alert_rules_returns_both_rules() -> None:
    rules = json.loads(_call("alerting_manage_rules", {"operation": "list"}))
    titles = {r["title"] for r in rules}
    assert "encoder_frame_drop" in titles
    assert "cdn_multi_region_latency" in titles


def test_mcp_prometheus_query_roundtrip() -> None:
    out = _call("query_prometheus", {
        "datasourceUid": "prometheus",
        "expr": "rate(frames_dropped_total[30s])",
        "startTime": "now-1h",
        "endTime": "now",
        "stepSeconds": 15,
    })
    data = json.loads(out)["data"]
    assert data and data[0]["values"], "expected real metric series via MCP"
