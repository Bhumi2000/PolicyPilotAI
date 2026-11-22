"""Evaluation of a generated output against clearly defined, documented criteria.

All scores are computed from the actual model output for the current run.
Nothing here is hard-coded or pre-baked, so two different outputs can receive
different scores.
"""
from __future__ import annotations

import re
from typing import List

from ..schemas.models import AnalysisResult, EvaluationScores, PolicyClause

_PROMISE_PATTERNS = [
    r"\bwe (?:will|can|are going to) (?:refund|replace|compensate|reimburse|pay)\b",
    r"\byou will (?:receive|get) (?:a |your )?(?:refund|replacement|compensation|money)\b",
    r"\bguarantee(?:d|s)?\b",
    r"\brefund (?:has been|will be|is) (?:processed|issued|approved)\b",
    r"\b(?:within|in) \d+ (?:business |working )?days\b",
    r"\bwill arrive by\b",
    r"\bdelivery by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow)\b",
]
_SHORT_PROMISE = re.compile("|".join(_PROMISE_PATTERNS), re.IGNORECASE)

_EMPATHY_WORDS = (
    "sorry", "apolog", "understand", "frustrat", "inconvenienc", "thank",
    "appreciate", "assist", "help", "regret",
)
_APOLOGY_WORDS = ("sorry", "apolog", "regret")


def _count(text: str, needles) -> int:
    lowered = text.lower()
    return sum(lowered.count(word) for word in needles)


def evaluate(result: AnalysisResult, clauses: List[PolicyClause]) -> EvaluationScores:
    flags: List[str] = []

    # 1. Policy adherence --------------------------------------------------- #
    if clauses:
        if result.policy_evidence:
            policy_adherence = 5
        elif result.suggested_resolution and result.generated_reply:
            policy_adherence = 3
            flags.append("no clause ids cited although policy was available")
        else:
            policy_adherence = 2
    else:
        if result.policy_evidence:
            policy_adherence = 1
            flags.append("claims policy evidence but no policy was provided")
        else:
            policy_adherence = 2
            flags.append("no policy available to ground the answer")

    # 2. Completeness ------------------------------------------------------- #
    checks = [
        bool(result.complaint_summary.strip()),
        result.category not in ("", "unknown"),
        result.sentiment != "unknown",
        result.urgency != "unknown",
        bool(result.customer_intent.strip()),
        bool(result.suggested_resolution.strip()),
        bool(result.generated_reply.strip()),
    ]
    completeness = round(5 * sum(checks) / len(checks))
    if completeness < 7:
        flags.append(f"{sum(checks)}/7 core fields populated")

    # 3. Tone and empathy --------------------------------------------------- #
    reply = result.generated_reply
    tone = 1 if reply.strip() else 0
    tone += 1 if _count(reply, _EMPATHY_WORDS) >= 1 else 0
    tone += 1 if _count(reply, _EMPATHY_WORDS) >= 2 else 0
    tone += 1 if _count(reply, _APOLOGY_WORDS) >= 1 else 0
    tone += 1 if len(reply) >= 160 else 0
    tone_empathy = min(5, tone)

    # 4. Unsupported claims ------------------------------------------------- #
    matches = _SHORT_PROMISE.findall(reply)
    unsupported = max(0, 5 - 2 * len(matches))
    if matches:
        unique = sorted({m.strip().lower() for m in matches if m.strip()})
        flags.append("possible unsupported promise: " + ", ".join(unique[:3]))

    # 5. Escalation appropriateness ----------------------------------------- #
    should_escalate = (
        len(clauses) == 0
        or result.risk_level == "high"
        or bool(result.missing_information)
    )
    if should_escalate and result.human_review_required:
        escalation = 5
    elif should_escalate and not result.human_review_required:
        escalation = 2
        flags.append("should have escalated but human_review_required is false")
    elif not should_escalate and not result.human_review_required:
        escalation = 5
    else:
        escalation = 3
        flags.append("escalated although the case looks routine")

    total = (
        policy_adherence + completeness + tone_empathy + unsupported + escalation
    )
    return EvaluationScores(
        policy_adherence=policy_adherence,
        completeness=completeness,
        tone_empathy=tone_empathy,
        unsupported_claims=unsupported,
        escalation_appropriateness=escalation,
        total=total,
        flags=flags,
    )
