"""CDN worker: emits cdn_p99_latency_ms + buffer_ratio."""
import sys

from prometheus_client import Gauge

from common import jitter, log, run

cdn_p99 = Gauge("cdn_p99_latency_ms", "CDN p99 latency", ["node"])
buffer_ratio = Gauge("buffer_ratio", "Player buffering ratio", ["node"])


def tick(node: str, mode: str) -> None:
    if mode == "multi_region":
        p99 = jitter(900, 1800)
        buf = jitter(0.4, 0.9)
    else:
        p99 = jitter(40, 120)
        buf = jitter(0.0, 0.02)
    cdn_p99.labels(node).set(p99)
    buffer_ratio.labels(node).set(buf)
    log(node, "cdn_tick", mode=mode, p99_ms=round(p99, 1), buffer_ratio=round(buf, 3))


if __name__ == "__main__":
    run(sys.argv[1], tick)
