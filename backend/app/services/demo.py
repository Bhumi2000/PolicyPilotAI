"""Deterministic demo output used ONLY when ENABLE_DEMO_MODE=true.

Every record produced through this module is tagged with mode="demo" and shown
with a warning banner in the UI, so demo output is never presented as a real
model response.
"""
from __future__ import annotations

import json
from typing import List

from ..schemas.models import PolicyClause


def _topic(complaint: str) -> str:
    text = complaint.lower()
    if any(w in text for w in ("refund", "money back", "return")):
        return "refund"
    if any(w in text for w in ("late", "deliver", "delivery", "shipping", "shipment")):
        return "delivery"
    if any(w in text for w in ("damage", "broken", "defect", "faulty", "wrong item")):
        return "damaged"
    if any(w in text for w in ("cancel",)):
        return "cancellation"
    return "general"


def generate(version: str, complaint: str, clauses: List[PolicyClause]) -> str:
    topic = _topic(complaint)
    evidence = [c.clause_id for c in clauses] or ["none"]

    if version == "v1":
        return (
            "Hello, thank you for contacting us. We are sorry to hear about the issue "
            "you described. Our team will look into your request and get back to you "
            "shortly with the best possible resolution."
        )

    if version == "v2":
        payload = {
            "complaint_summary": complaint.strip()[:160],
            "category": topic,
            "sentiment": "negative",
            "urgency": "medium",
            "customer_intent": "Get the issue resolved or be compensated.",
            "suggested_resolution": "Review the request against the policy and respond.",
            "missing_information": [],
            "risk_level": "medium",
            "generated_reply": (
                "Hello, we are sorry for the inconvenience. We have noted your request "
                "and will review it against our policy before replying."
            ),
        }
        return json.dumps(payload)

    # v3 - grounded, guardrailed, escalates when evidence is thin.
    missing = []
    if "order" not in complaint.lower():
        missing.append("order id")
    weak = not clauses
    escalation = weak or topic in {"refund", "cancellation"}
    payload = {
        "complaint_summary": complaint.strip()[:160],
        "category": topic,
        "sentiment": "negative",
        "urgency": "high" if escalation else "medium",
        "customer_intent": "Obtain a resolution supported by company policy.",
        "policy_evidence": evidence,
        "suggested_resolution": (
            "Explain the applicable policy clause and the exact next step it allows."
        ),
        "missing_information": missing,
        "risk_level": "high" if escalation else "medium",
        "human_review_required": escalation,
        "human_review_reason": (
            "Requested outcome is not clearly supported by the retrieved policy clauses."
            if escalation
            else ""
        ),
        "generated_reply": (
            "Hello, thank you for reaching out. Based on our policy I can confirm the "
            "next steps available for your case. "
            + ("Could you share your order id so we can proceed? " if missing else "")
            + "A support specialist will confirm the outcome before any commitment is made."
        ),
    }
    return json.dumps(payload)
