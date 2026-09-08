#!/bin/bash
# Start the Grafana MCP server (SSE, port 9222). Requires uv (uvx) and .env with GRAFANA_SA_TOKEN.
set -euo pipefail
cd "$(dirname "$0")/.."
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}" \
GRAFANA_SERVICE_ACCOUNT_TOKEN="$(grep '^GRAFANA_SA_TOKEN=' .env | cut -d= -f2-)" \
exec uvx mcp-grafana@1.3.0 -t sse -address 0.0.0.0:9222
