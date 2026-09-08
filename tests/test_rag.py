"""T5.2 verify: search_runbooks surfaces the right runbook for known symptoms."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.rag_tools import search_runbooks


def test_frame_drop_query_returns_encoder_runbook() -> None:
    out = search_runbooks("encoder dropping frames alert firing")
    names = [r["runbook"] for r in out["results"]]
    assert "encoder-frame-drop-loop" in names[0] or "encoder-frame-drop-loop" in names
    assert out["source"] == "lexical_fallback"


def test_cdn_query_returns_cdn_runbook() -> None:
    out = search_runbooks("cdn p99 latency high multi region")
    top = out["results"][0]["runbook"]
    assert "cdn" in top


def test_results_have_snippets_and_scores() -> None:
    out = search_runbooks("loki logs missing ingestion", top_k=2)
    assert len(out["results"]) == 2
    for r in out["results"]:
        assert r["snippet"]
        assert r["score"] >= 0
