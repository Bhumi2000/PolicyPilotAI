"""API level tests. These run in demo mode so no API key is required."""
import os

os.environ.setdefault("ENABLE_DEMO_MODE", "true")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

POLICY_TEXT = """
1. REFUND POLICY
Customers may request a full refund within 7 days of delivery if the item is unused.

2. REPLACEMENT POLICY
Damaged items reported within 10 days are eligible for a free replacement with a photo.

3. DELIVERY POLICY
Standard delivery takes 4 to 6 business days. No compensation unless the delay exceeds 15 days.
"""


def _seed_policy() -> str:
    response = client.post(
        "/api/policies/text", json={"name": "Demo Policy", "text": POLICY_TEXT}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_health_reports_demo_mode():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_add_text_policy_creates_clauses():
    payload = client.post(
        "/api/policies/text", json={"name": "Test Policy", "text": POLICY_TEXT}
    ).json()
    assert payload["clauses"] >= 3
    assert payload["characters"] > 0


def test_analyze_requires_a_policy():
    response = client.post(
        "/api/complaints/analyze",
        json={"complaint": "I want a refund", "policy_ids": ["missing-id"]},
    )
    assert response.status_code == 400


def test_analyze_returns_structured_record_in_demo_mode():
    policy_id = _seed_policy()
    response = client.post(
        "/api/complaints/analyze",
        json={
            "complaint": "My order arrived damaged and I want a refund.",
            "order_id": "ORD-1",
            "policy_ids": [policy_id],
            "prompt_version": "v3",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["result"]["generated_reply"]
    assert body["prompt_version"] == "v3"
    assert "evaluation" in body
    assert body["mode"] in ("demo", "live")


def test_compare_runs_all_three_versions():
    policy_id = _seed_policy()
    response = client.post(
        "/api/complaints/compare",
        json={"complaint": "The item is broken, please replace it.", "policy_ids": [policy_id]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert {body["v1"]["prompt_version"], body["v2"]["prompt_version"], body["v3"]["prompt_version"]} == {"v1", "v2", "v3"}
    assert len(body["comparison"]) >= 4


def test_history_and_dashboard_are_consistent():
    history = client.get("/api/complaints").json()
    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_complaints"] == len(history)


def test_upload_rejects_non_pdf():
    response = client.post(
        "/api/policies/upload",
        files={"file": ("notes.txt", b"hello world, this is not a pdf", "text/plain")},
    )
    assert response.status_code == 400
