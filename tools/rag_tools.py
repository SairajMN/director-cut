"""Runbook retrieval (T5.2).

Uses Vertex AI Search when RUNBOOK_DATASTORE is configured; otherwise a
deterministic lexical scorer over docs/runbooks/*.md (good enough for the
known runbook set, and works offline during the demo).
"""
import os
import re
from pathlib import Path

RUNBOOKS_DIR = Path(__file__).resolve().parents[1] / "docs" / "runbooks"
DATASTORE = os.environ.get("RUNBOOK_DATASTORE", "")

STOP = {"the", "a", "an", "is", "are", "on", "in", "for", "of", "to", "and", "with"}


def _load_runbooks() -> dict[str, str]:
    return {p.stem: p.read_text() for p in RUNBOOKS_DIR.glob("*.md")}


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2}


def _lexical_search(query: str, top_k: int) -> list[dict]:
    q = _tokens(query)
    scored = []
    for name, body in _load_runbooks().items():
        overlap = q & _tokens(name + " " + body.split("## Remediation")[0])
        scored.append({"runbook": name, "score": len(overlap), "snippet": _best_snippet(body, q)})
    scored.sort(key=lambda d: -d["score"])
    return scored[:top_k]


def _best_snippet(body: str, q: set[str]) -> str:
    for para in body.split("\n## "):
        if q & _tokens(para):
            return para.strip().replace("\n", " ")[:200]
    return body.strip().replace("\n", " ")[:200]


def _vertex_search(query: str, top_k: int) -> list[dict]:
    from google.cloud import discoveryengine_v as discoveryengine

    client = discoveryengine.SearchServiceClient()
    project, location = os.environ["GCP_PROJECT_ID"], "global"
    serving_config = (
        f"projects/{project}/locations/{location}/collections/default_collection/"
        f"dataStores/{DATASTORE}/servingConfigs/default_search"
    )
    request = discoveryengine.SearchRequest(
        serving_config=serving_config, query=query, page_size=top_k
    )
    return [
        {"runbook": r.document.derived_struct_data.get("title", r.document.id),
         "score": r.relevance_score, "snippet": r.document.derived_struct_data.get("snippets", [{}])[0].get("snippet", "")}
        for r in client.search(request)
    ]


def search_runbooks(query: str, top_k: int = 2) -> dict:
    """Returns the most relevant runbooks for a symptom or alert name."""
    if DATASTORE:
        results = _vertex_search(query, top_k)
        source = "vertex_ai_search"
    else:
        results = _lexical_search(query, top_k)
        source = "lexical_fallback"
    return {"source": source, "results": results}
