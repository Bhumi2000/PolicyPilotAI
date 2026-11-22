"""Dashboard aggregate statistics computed from real stored records."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter

from ..schemas.models import DashboardStats
from ..store import list_complaints, policy_count

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats() -> DashboardStats:
    records = list_complaints()

    by_category: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    scores: Dict[str, List[float]] = defaultdict(list)
    sub_scores: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    human_review = 0
    high_risk = 0
    approved = 0

    for record in records:
        by_category[record.result.category or "unknown"] += 1
        by_risk[record.result.risk_level or "unknown"] += 1
        if record.result.human_review_required:
            human_review += 1
        if record.result.risk_level == "high":
            high_risk += 1
        if record.review_status in ("approved", "edited"):
            approved += 1

        scores[record.prompt_version].append(record.evaluation.total)
        for field in (
            "policy_adherence",
            "completeness",
            "tone_empathy",
            "unsupported_claims",
            "escalation_appropriateness",
        ):
            sub_scores[record.prompt_version][field].append(
                getattr(record.evaluation, field)
            )

    prompt_evaluation: Dict[str, Dict[str, float]] = {}
    for version, totals in scores.items():
        entry = {"avg_total": round(sum(totals) / len(totals), 2), "runs": float(len(totals))}
        for field, values in sub_scores[version].items():
            entry[f"avg_{field}"] = round(sum(values) / len(values), 2)
        prompt_evaluation[version] = entry

    recent_activity = [
        {
            "id": record.id,
            "created_at": record.created_at,
            "summary": record.result.complaint_summary or record.input.complaint[:80],
            "category": record.result.category,
            "risk_level": record.result.risk_level,
            "prompt_version": record.prompt_version,
            "human_review_required": record.result.human_review_required,
        }
        for record in records[:6]
    ]

    return DashboardStats(
        total_complaints=len(records),
        human_review_required=human_review,
        high_risk=high_risk,
        approved=approved,
        by_category=dict(by_category),
        by_risk=dict(by_risk),
        prompt_evaluation=prompt_evaluation,
        recent_activity=recent_activity,
        total_policies=policy_count(),
    )
