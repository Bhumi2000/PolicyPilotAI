"""Orchestrates a single complaint analysis run end to end."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import settings
from ..prompts.versions import PROMPTS, render
from ..schemas.models import (
    AnalysisRecord,
    AnalysisResult,
    ComplaintRequest,
    EvaluationScores,
    PolicyClause,
)
from ..store import add_complaint, new_id
from . import demo, gemini_client
from .evaluator import evaluate
from .retrieval import format_clauses_for_prompt, retrieve_relevant_clauses


class AnalysisError(Exception):
    """Raised when a run cannot be completed honestly (e.g. no API key)."""


_EXCEPTION_PHRASES = (
    "exception", "special case", "make an exception", "waive", "outside the policy",
)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    cleaned = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _normalise(value: Any, allowed: tuple, default: str) -> str:
    lowered = str(value or "").strip().lower()
    return lowered if lowered in allowed else default


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _coerce(data: Dict[str, Any]) -> AnalysisResult:
    return AnalysisResult(
        complaint_summary=str(data.get("complaint_summary", "")).strip(),
        category=str(data.get("category", "unknown")).strip() or "unknown",
        sentiment=_normalise(
            data.get("sentiment"),
            ("positive", "neutral", "negative", "angry", "unknown"),
            "unknown",
        ),
        urgency=_normalise(data.get("urgency"), ("low", "medium", "high", "unknown"), "unknown"),
        customer_intent=str(data.get("customer_intent", "")).strip(),
        policy_evidence=_as_list(data.get("policy_evidence")),
        suggested_resolution=str(data.get("suggested_resolution", "")).strip(),
        missing_information=_as_list(data.get("missing_information")),
        risk_level=_normalise(
            data.get("risk_level"), ("low", "medium", "high", "unknown"), "unknown"
        ),
        human_review_required=bool(data.get("human_review_required", False)),
        human_review_reason=str(data.get("human_review_reason", "")).strip(),
        generated_reply=str(data.get("generated_reply", "")).strip(),
    )


def _parse(version: str, text: str) -> Optional[AnalysisResult]:
    if version == "v1":
        reply = text.strip()
        if not reply:
            return None
        # v1 produces free text only - no structured fields - by design.
        return AnalysisResult(category="unknown", generated_reply=reply)
    data = _extract_json(text)
    if data is None:
        return None
    return _coerce(data)


def _apply_review_guardrails(
    result: AnalysisResult, clauses: List[PolicyClause], complaint: str
) -> AnalysisResult:
    """Deterministic safety floor applied after the model call.

    The model is asked to escalate in v3, but the application enforces a minimum
    set of escalation rules for every version so no version can silently skip a
    high-risk case.
    """
    reasons: List[str] = []
    if not clauses:
        reasons.append("no policy clause could be retrieved for this complaint")
    if result.risk_level == "high":
        reasons.append("complaint classified as high risk")
    lowered = complaint.lower()
    if any(phrase in lowered for phrase in _EXCEPTION_PHRASES):
        reasons.append("customer appears to request an exception to policy")
    if len(result.missing_information) >= 3:
        reasons.append("several required customer details are missing")

    if reasons and not result.human_review_required:
        result.human_review_required = True
    if result.human_review_required:
        merged = result.human_review_reason.strip()
        combined = "; ".join(filter(None, [merged, *reasons]))
        result.human_review_reason = combined[:300]
    return result


async def run_analysis(request: ComplaintRequest, policy_text: str) -> AnalysisRecord:
    clauses = (
        retrieve_relevant_clauses(policy_text, request.complaint) if policy_text.strip() else []
    )
    version = request.prompt_version
    prompt = PROMPTS[version]

    values = {
        "complaint": request.complaint,
        "policy_text": policy_text.strip() or "NO POLICY DOCUMENT AVAILABLE.",
        "customer_name": request.customer_name or "not provided",
        "order_id": request.order_id or "not provided",
        "product_category": request.product_category or "not provided",
        "policy_clauses": format_clauses_for_prompt(clauses),
    }
    user_prompt = render(prompt.user_prompt_template, values)

    mode = settings.ai_mode
    if mode == "unconfigured":
        raise AnalysisError(
            "The AI backend is not configured. Add GEMINI_API_KEY to backend/.env, "
            "or set ENABLE_DEMO_MODE=true to explore the interface offline. "
            "No fake result was returned."
        )

    started = time.perf_counter()
    if mode == "live":
        raw = await gemini_client.generate(
            prompt.system_prompt, user_prompt, json_mode=(version != "v1")
        )
    else:  # demo
        raw = demo.generate(version, request.complaint, clauses)
    latency_ms = int((time.perf_counter() - started) * 1000)

    result = _parse(version, raw)
    if result is None and mode == "live":
        # One retry for a malformed answer, then fail honestly.
        raw = await gemini_client.generate(
            prompt.system_prompt, user_prompt, json_mode=(version != "v1")
        )
        result = _parse(version, raw)
    if result is None:
        raise AnalysisError(
            "The model did not return valid output for this prompt version. Please retry."
        )

    result = _apply_review_guardrails(result, clauses, request.complaint)
    evaluation: EvaluationScores = evaluate(result, clauses)

    record = AnalysisRecord(
        id=new_id("cmp"),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        prompt_version=version,
        mode=mode,
        model=(settings.gemini_model if mode == "live" else "demo"),
        latency_ms=latency_ms,
        input=request,
        result=result,
        retrieved_clauses=clauses,
        evaluation=evaluation,
    )
    return add_complaint(record)
