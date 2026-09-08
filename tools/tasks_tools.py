"""Remediation dispatch via Cloud Tasks (T5.3).

Cloud mode (TASKS_QUEUE set): enqueues an HTTP task so every remediation is
auditable and rate-limited by the queue. Local mode: direct HTTP POST (localhost
is unreachable by Cloud Tasks HTTP targets — queue verify happens at deploy).
"""
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import load_env  # noqa: E402

load_env()

PROJECT = os.environ.get("GCP_PROJECT_ID", "")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
QUEUE = os.environ.get("TASKS_QUEUE", "")
CONTROL_API = os.environ.get("CONTROL_API_URL", "http://localhost:8080")


def dispatch_remediation(endpoint: str, payload: dict) -> dict:
    """POSTs payload to control-api/<endpoint>, via Cloud Tasks when configured."""
    if QUEUE and PROJECT:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(PROJECT, LOCATION, QUEUE)
        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{CONTROL_API}/{endpoint}",
                headers={"Content-Type": "application/json"},
                body=json.dumps(payload).encode(),
            )
        )
        resp = client.create_task(request={"parent": parent, "task": task})
        return {"queued": True, "task_name": resp.name}
    resp = requests.post(f"{CONTROL_API}/{endpoint}", json=payload, timeout=10)
    return {"queued": False, "status": resp.status_code, "response": resp.json()}
