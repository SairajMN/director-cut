"""Deploy the Director's Cut crew to Vertex AI Agent Engine (T6.1).

Usage:
  python agents/deployment.py            # create/update, prints resource ID
  python agents/deployment.py --test "status"
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env import load_env

load_env()

PROJECT = os.environ.get("GCP_PROJECT_ID", "director-cut")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
STAGING = os.environ.get("STAGING_BUCKET", "gs://director-cut-adk-staging")

from agents.director_agent.agent import root_agent  # noqa: E402


def deploy() -> str:
    import vertexai
    from vertexai import agent_engines

    vertexai.init(project=PROJECT, location=LOCATION, staging_bucket=STAGING)
    remote = agent_engines.create(
        agent_engine=root_agent,
        display_name="directors-cut",
        requirements=["google-cloud-aiplatform[agent_engines]>=1.95", "google-adk", "cloudpickle", "requests", "mcp", "PyYAML"],
    )
    return str(remote.resource_name)


def test_remote(query: str) -> str:
    import vertexai
    from vertexai import agent_engines

    vertexai.init(project=PROJECT, location=LOCATION, staging_bucket=STAGING)
    agent_id = os.environ.get("AGENT_ENGINE_ID", "")
    if not agent_id:
        raise SystemExit("AGENT_ENGINE_ID not set in .env — deploy first")
    remote = agent_engines.get(agent_id)
    session = remote.create_session(user_id="hackathon-judge")
    session_id = session["id"] if isinstance(session, dict) else session.id
    for event in remote.stream_query(user_id="hackathon-judge", session_id=session_id, message=query):
        print(event)
    return "ok"


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_remote(sys.argv[sys.argv.index("--test") + 1])
    else:
        print(deploy())
