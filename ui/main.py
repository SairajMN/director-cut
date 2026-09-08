"""War-room UI: incident timeline, reasoning trace, Grafana embeds, ticket queue."""
import json
import os
import time
from pathlib import Path

import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Director's Cut War Room")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
CONTROL_API = os.environ.get("CONTROL_API", "http://localhost:8080")
DASHBOARD_UID = os.environ.get("DASHBOARD_UID", "broadcast-reliability")
TICKETS_DIR = Path(os.environ.get("TICKETS_DIR", Path(__file__).parent / "tickets"))

# demo timeline events (persisted per-process; the e2e driver appends via /api/event)
EVENTS: list[dict] = []


def _tickets() -> list[dict]:
    if not TICKETS_DIR.exists():
        return []
    out = []
    for p in sorted(TICKETS_DIR.glob("ESC-*.json"), reverse=True):
        try:
            out.append(json.loads(p.read_text()))
        except json.JSONDecodeError:
            continue
    return out


def _grafana_ok() -> bool:
    try:
        return requests.get(f"{GRAFANA_URL}/api/health", timeout=2).ok
    except requests.RequestException:
        return False


@app.get("/", response_class=HTMLResponse)
def warroom(request: Request):
    ctx = {
        "grafana_ok": _grafana_ok(),
        "grafana_url": GRAFANA_URL,
        "dashboard_uid": DASHBOARD_UID,
        "control_api": CONTROL_API,
        "events": EVENTS[-30:],
        "tickets": _tickets(),
    }
    return templates.TemplateResponse(request, "warroom.html", ctx)


@app.post("/api/event")
async def add_event(request: Request):
    """Demo driver / agents append timeline events: {"actor","text","kind"}."""
    body = await request.json()
    EVENTS.append({**body, "ts": time.strftime("%H:%M:%S")})
    return {"ok": True, "count": len(EVENTS)}


@app.post("/api/approve/{node}")
def approve_fix(node: str):
    """Human approval button: requeue the worker through the control API."""
    try:
        resp = requests.post(f"{CONTROL_API}/requeue/{node}", timeout=5)
        EVENTS.append({"actor": "human", "kind": "approve",
                       "text": f"Approved fix: requeue {node} -> {resp.status_code}",
                       "ts": time.strftime("%H:%M:%S")})
        return {"ok": resp.ok, "status": resp.status_code}
    except requests.RequestException as exc:
        return {"ok": False, "error": str(exc)}
