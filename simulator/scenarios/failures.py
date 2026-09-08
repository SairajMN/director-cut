"""Scripted failure scenarios — the fixed enum of injectable incidents."""
from typing import Callable

# scenario name -> (nodes affected, mode to set). Deterministic by design.
SCENARIOS: dict[str, tuple[list[str], str]] = {
    "encoder_frame_drop": (["encoder-2"], "frame_drop"),   # single node, Tier-1 (auto-approve)
    "cdn_multi_region": (["cdn-1", "cdn-2"], "multi_region"),  # global, Tier-3 (blocked)
}
