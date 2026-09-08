"""Smoke tests against the running simulator (docker compose must be up)."""
import time

import requests

PROM = "http://localhost:9090"
API = "http://localhost:8080"


def prom(query: str) -> list:
    r = requests.get(f"{PROM}/api/v1/query", params={"query": query}, timeout=5)
    return r.json()["data"]["result"]


def test_health() -> None:
    assert requests.get(f"{API}/health", timeout=5).json()["status"] == "ok"


def test_metrics_flow() -> None:
    assert prom("frames_dropped_total"), "no encoder metrics in Prometheus"
    assert prom("cdn_p99_latency_ms"), "no cdn metrics in Prometheus"


def test_inject_and_recover() -> None:
    requests.post(f"{API}/inject-failure/encoder_frame_drop", timeout=5)
    time.sleep(35)  # scrape interval + rate window
    rates = {r["metric"]["node"]: float(r["value"][1]) for r in prom("rate(frames_dropped_total[30s])")}
    assert rates.get("encoder-2", 0) > 5, f"encoder-2 not spiking: {rates}"

    requests.post(f"{API}/requeue/encoder-2", timeout=5)
    time.sleep(35)
    rates = {r["metric"]["node"]: float(r["value"][1]) for r in prom("rate(frames_dropped_total[30s])")}
    assert rates.get("encoder-2", 0) < 5, f"encoder-2 did not recover: {rates}"


def test_unknown_scenario_rejected() -> None:
    assert requests.post(f"{API}/inject-failure/nope", timeout=5).status_code == 400
