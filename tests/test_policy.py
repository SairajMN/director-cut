"""Unit tests for the deterministic IAM gate (T4.1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.policy_tools import check_authorization, load_policy


def test_policy_loads_with_all_catalog_actions() -> None:
    policy = load_policy()
    assert set(policy["remediations"]) == {
        "requeue_worker", "flip_cdn_region", "scale_encoder_pool", "purge_cdn_cache",
    }


def test_t1_auto_approved_for_agent_sa() -> None:
    v = check_authorization("requeue_worker")
    assert v["allowed"] is True and v["tier"] == "T1"


def test_t2_requires_human_approval() -> None:
    v = check_authorization("scale_encoder_pool")
    assert v["allowed"] is False and v["tier"] == "T2" and v.get("escalate") is True


def test_t3_blocked_with_escalation() -> None:
    v = check_authorization("purge_cdn_cache")
    assert v["allowed"] is False and v["tier"] == "T3" and v.get("escalate") is True


def test_unknown_action_rejected() -> None:
    v = check_authorization("rm_rf_slash")
    assert v["allowed"] is False and v["tier"] == "UNKNOWN"


def test_unauthorized_caller_denied_even_on_t1() -> None:
    v = check_authorization("requeue_worker", caller="random-guy@example.iam.gserviceaccount.com")
    assert v["allowed"] is False
