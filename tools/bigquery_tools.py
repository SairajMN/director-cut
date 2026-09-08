"""BigQuery post-mortem writer (T5.1) — every incident gets a durable record."""
import os
import time

from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "director-cut")
TABLE_ID = f"{PROJECT_ID}.director_cut.post_mortems"


def write_post_mortem(incident: str, alert: str, root_cause: str, action_taken: str,
                      authz_decision: str, ticket_id: str = "") -> dict:
    """Inserts one post-mortem row. Called by the Director after each incident closes."""
    row = {
        "incident": incident,
        "alert": alert,
        "root_cause": root_cause,
        "action_taken": action_taken,
        "authz_decision": authz_decision,
        "ticket_id": ticket_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    }
    client = bigquery.Client(project=PROJECT_ID)
    errors = client.insert_rows_json(TABLE_ID, [row])
    if errors:
        return {"written": False, "errors": errors}
    return {"written": True, "table": TABLE_ID}
