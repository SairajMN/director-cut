"""Control API: in-memory node state that workers poll; mutations flip worker behavior."""
import os
from typing import Any

from fastapi import FastAPI, HTTPException

app = FastAPI(title="director-cut control-api")

ENCODERS = ["encoder-1", "encoder-2", "encoder-3"]
CDNS = ["cdn-1", "cdn-2"]

# node -> "healthy" | "frame_drop" | "multi_region" | "drained"
state: dict[str, str] = {}
for enc in ENCODERS:
    state[enc] = "healthy"
for cdn in CDNS:
    state[cdn] = "healthy"


def _set(nodes: list[str], mode: str) -> dict[str, Any]:
    for n in nodes:
        state[n] = mode
    return {"nodes": nodes, "mode": mode}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/state")
def all_state() -> dict[str, str]:
    return state


@app.get("/state/{node}")
def node_state(node: str) -> dict[str, str]:
    if node not in state:
        raise HTTPException(404, f"unknown node {node}")
    return {"node": node, "mode": state[node]}


@app.post("/inject-failure/{scenario}")
def inject_failure(scenario: str) -> dict[str, Any]:
    if scenario == "encoder_frame_drop":
        return _set([os.getenv("FAIL_NODE", "encoder-2")], "frame_drop")
    if scenario == "cdn_multi_region":
        return _set(CDNS, "multi_region")
    raise HTTPException(400, f"unknown scenario {scenario}")


@app.post("/requeue/{node}")
def requeue(node: str) -> dict[str, Any]:
    if node not in ENCODERS:
        raise HTTPException(404, f"not an encoder: {node}")
    return _set([node], "healthy")


@app.post("/drain/{node}")
def drain(node: str) -> dict[str, Any]:
    if node not in state:
        raise HTTPException(404, f"unknown node {node}")
    return _set([node], "drained")


@app.post("/flip-cdn")
def flip_cdn() -> dict[str, Any]:
    return _set(CDNS, "healthy")
