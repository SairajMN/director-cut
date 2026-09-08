"""Shared simulator worker loop: poll control-api for node state, emit metrics + JSON logs."""
import json
import random
import sys
import time

import requests
from prometheus_client import start_http_server

CONTROL_API = "http://control-api:8080"
POLL_SECONDS = 2


def get_mode(node: str) -> str:
    try:
        r = requests.get(f"{CONTROL_API}/state/{node}", timeout=2)
        return r.json()["mode"]
    except Exception:
        return "healthy"


def log(node: str, event: str, **fields) -> None:
    print(json.dumps({"ts": time.time(), "node": node, "event": event, **fields}))


def run(node: str, tick) -> None:
    # tick returns a dict of {metric_name: value_to_inc_or_set}
    start_http_server(9100)
    log(node, "worker_started")
    while True:
        mode = get_mode(node)
        tick(node, mode)
        time.sleep(1)


def jitter(lo: float, hi: float) -> float:
    return random.uniform(lo, hi)
