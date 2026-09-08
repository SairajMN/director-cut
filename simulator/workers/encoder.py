"""Encoder worker: emits frames_dropped_total + encode_latency_seconds."""
import sys
import time

from prometheus_client import Counter, Gauge

from common import jitter, log, run

frames_dropped = Counter("frames_dropped_total", "Frames dropped by encoder", ["node"])
encode_latency = Gauge("encode_latency_seconds", "Current encode latency", ["node"])


def tick(node: str, mode: str) -> None:
    if mode == "frame_drop":
        dropped = int(jitter(20, 50))
        encode_latency.labels(node).set(jitter(1.0, 2.5))
        log(node, "encode_tick", mode=mode, dropped=dropped, latency=round(encode_latency.labels(node)._value.get(), 3))
    else:
        dropped = 1 if time.time() % 10 < 1 else 0
        encode_latency.labels(node).set(jitter(0.03, 0.08))
    frames_dropped.labels(node).inc(dropped)


if __name__ == "__main__":
    run(sys.argv[1], tick)
