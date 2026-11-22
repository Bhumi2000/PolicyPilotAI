"""Complaint analysis, prompt comparison, history and human review endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from ..schemas.models import (
    AnalysisRecord,
    CompareRequest,
    CompareResponse,
    ComparisonRow,
    ComplaintRequest,
    ReviewRequest,
)
from ..services.analysis_service import AnalysisError, run_analysis
from ..store import get_complaint, list_complaints, list_policies, update_complaint

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _combined_policy_text(policy_ids: List[str]) -> str:
    policies = list_policies()
    if policy_ids:
        wanted = set(policy_ids)
        policies = [policy for policy in policies if policy.id in wanted]
    return "\n\n".join(policy.text for policy in policies)


@router.post("/analyze", response_model=AnalysisRecord)
async def analyze_complaint(payload: ComplaintRequest) -> AnalysisRecord:
    policy_text = _combined_policy_text(payload.policy_ids)
    if not policy_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No policy available. Upload or paste a policy in the Policy Library first.",
        )
    try:
        return await run_analysis(payload, policy_text)
    except AnalysisError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/compare", response_model=CompareResponse)
async def compare_versions(payload: CompareRequest) -> CompareResponse:
    policy_text = _combined_policy_text(payload.policy_ids)
    if not policy_text.strip():
        raise HTTPException(status_code=400, detail="No policy available to compare against.")

    records = {}
    for version in ("v1", "v2", "v3"):
        request = ComplaintRequest(
            complaint=payload.complaint,
            customer_name=payload.customer_name,
            order_id=payload.order_id,
            product_category=payload.product_category,
            policy_ids=payload.policy_ids,
            prompt_version=version,  # type: ignore[arg-type]
        )
        try:
            records[version] = await run_analysis(request, policy_text)
        except AnalysisError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    def score(record: AnalysisRecord) -> str:
        return f"{record.evaluation.total}/25"

    comparison = [
        ComparisonRow(
            criterion="Policy evidence cited",
            v1="none (free text)",
            v2=str(records["v2"].result.policy_evidence or "none"),
            v3=str(records["v3"].result.policy_evidence or "none"),
        ),
        ComparisonRow(
            criterion="Structured fields filled",
            v1="0 of 7 (plain reply only)",
            v2=f"{sum(1 for v in (records['v2'].result.complaint_summary, records['v2'].result.category, records['v2'].result.sentiment, records['v2'].result.urgency, records['v2'].result.customer_intent, records['v2'].result.suggested_resolution, records['v2'].result.generated_reply) if v and v != 'unknown')}/7",
            v3=f"{sum(1 for v in (records['v3'].result.complaint_summary, records['v3'].result.category, records['v3'].result.sentiment, records['v3'].result.urgency, records['v3'].result.customer_intent, records['v3'].result.suggested_resolution, records['v3'].result.generated_reply) if v and v != 'unknown')}/7",
        ),
        ComparisonRow(
            criterion="Missing info flagged",
            v1="no",
            v2=str(records["v2"].result.missing_information or "none"),
            v3=str(records["v3"].result.missing_information or "none"),
        ),
        ComparisonRow(
            criterion="Human review required",
            v1=str(records["v1"].result.human_review_required),
            v2=str(records["v2"].result.human_review_required),
            v3=str(records["v3"].result.human_review_required),
        ),
        ComparisonRow(
            criterion="Reply length (chars)",
            v1=str(len(records["v1"].result.generated_reply)),
            v2=str(len(records["v2"].result.generated_reply)),
            v3=str(len(records["v3"].result.generated_reply)),
        ),
        ComparisonRow(
            criterion="Evaluation score",
            v1=score(records["v1"]),
            v2=score(records["v2"]),
            v3=score(records["v3"]),
        ),
    ]

    return CompareResponse(
        v1=records["v1"], v2=records["v2"], v3=records["v3"], comparison=comparison
    )


@router.get("", response_model=List[AnalysisRecord])
def get_history() -> List[AnalysisRecord]:
    return list_complaints()


@router.get("/{record_id}", response_model=AnalysisRecord)
def get_record(record_id: str) -> AnalysisRecord:
    record = get_complaint(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Complaint record not found.")
    return record


@router.patch("/{record_id}/review", response_model=AnalysisRecord)
def review_record(record_id: str, payload: ReviewRequest) -> AnalysisRecord:
    patch = {"review_status": payload.review_status}
    if payload.edited_reply is not None:
        patch["edited_reply"] = payload.edited_reply
    record = update_complaint(record_id, patch)
    if record is None:
        raise HTTPException(status_code=404, detail="Complaint record not found.")
    return record
