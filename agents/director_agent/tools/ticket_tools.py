"""Ticket output for denied remediations (T4.3). Webhook is a stub until T6."""
import json
import time
from pathlib import Path

import requests

TICKETS_DIR = Path(__file__).resolve().parents[3] / "tickets"
WEBHOOK_URL = "http://localhost:8080/ticket-webhook"


def create_incident_ticket(title: str, body: str, incident: str = "unknown", channel: str = "#broadcast-oncall") -> dict:
    """Writes a pre-filled ticket JSON to tickets/ and posts to the webhook (best-effort)."""
    ticket = {
        "id": f"ESC-{int(time.time())}",
        "title": title,
        "incident": incident,
        "body": body,
        "channel": channel,
        "escalated": True,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    TICKETS_DIR.mkdir(exist_ok=True)
    path = TICKETS_DIR / f"{ticket['id']}.json"
    path.write_text(json.dumps(ticket, indent=2))

    webhook = {"delivered": False, "status": None}
    try:
        resp = requests.post(WEBHOOK_URL, json=ticket, timeout=5)
        webhook = {"delivered": resp.ok, "status": resp.status_code}
    except requests.RequestException:
        pass

    return {"ticket_path": str(path), **webhook}
