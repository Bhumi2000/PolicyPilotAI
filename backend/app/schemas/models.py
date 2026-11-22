"""Pydantic models shared across the PolicyPilot AI backend."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

PromptVersionId = Literal["v1", "v2", "v3"]
RiskLevel = Literal["low", "medium", "high", "unknown"]
Urgency = Literal["low", "medium", "high", "unknown"]
Sentiment = Literal["positive", "neutral", "negative", "angry", "unknown"]


class ComplaintRequest(BaseModel):
    """Input submitted from the "Analyze Complaint" page."""

    complaint: str = Field(..., min_length=3, description="Raw customer complaint text")
    customer_name: Optional[str] = None
    order_id: Optional[str] = None
    product_category: Optional[str] = None
    policy_ids: List[str] = Field(default_factory=list)
    prompt_version: PromptVersionId = "v3"


class PolicyTextRequest(BaseModel):
    """Pasted policy text from the Policy Library page."""

    name: str = Field(..., min_length=2)
    text: str = Field(..., min_length=20)


class PolicyClause(BaseModel):
    clause_id: str
    heading: str
    text: str
    score: float = 0.0


class PolicySummary(BaseModel):
    id: str
    name: str
    source_type: Literal["pdf", "text"]
    characters: int
    clauses: int
    uploaded_at: str


class PolicyDetail(PolicySummary):
    text: str
    extracted_clauses: List[PolicyClause] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Structured AI output. Mirrors what the Gemini response must contain."""

    complaint_summary: str = ""
    category: str = "unknown"
    sentiment: Sentiment = "unknown"
    urgency: Urgency = "unknown"
    customer_intent: str = ""
    policy_evidence: List[str] = Field(default_factory=list)
    suggested_resolution: str = ""
    missing_information: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = "unknown"
    human_review_required: bool = False
    human_review_reason: str = ""
    generated_reply: str = ""


class EvaluationScores(BaseModel):
    """Scores derived from an actual generated output (never hard-coded)."""

    policy_adherence: int = Field(0, ge=0, le=5)
    completeness: int = Field(0, ge=0, le=5)
    tone_empathy: int = Field(0, ge=0, le=5)
    unsupported_claims: int = Field(0, ge=0, le=5, description="5 = none found, 0 = many")
    escalation_appropriateness: int = Field(0, ge=0, le=5)
    total: int = Field(0, ge=0, le=25)
    flags: List[str] = Field(default_factory=list)


class AnalysisRecord(BaseModel):
    id: str
    created_at: str
    prompt_version: PromptVersionId
    mode: str
    model: str
    latency_ms: int
    input: ComplaintRequest
    result: AnalysisResult
    retrieved_clauses: List[PolicyClause] = Field(default_factory=list)
    evaluation: EvaluationScores = Field(default_factory=EvaluationScores)
    review_status: Literal["pending", "approved", "edited"] = "pending"
    edited_reply: Optional[str] = None


class CompareRequest(BaseModel):
    complaint: str = Field(..., min_length=3)
    customer_name: Optional[str] = None
    order_id: Optional[str] = None
    product_category: Optional[str] = None
    policy_ids: List[str] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    criterion: str
    v1: str
    v2: str
    v3: str


class CompareResponse(BaseModel):
    v1: AnalysisRecord
    v2: AnalysisRecord
    v3: AnalysisRecord
    comparison: List[ComparisonRow]


class ReviewRequest(BaseModel):
    review_status: Literal["approved", "edited"]
    edited_reply: Optional[str] = None


class DashboardStats(BaseModel):
    total_complaints: int
    human_review_required: int
    high_risk: int
    approved: int
    by_category: Dict[str, int]
    by_risk: Dict[str, int]
    prompt_evaluation: Dict[str, Dict[str, float]]
    recent_activity: List[Dict[str, Any]]
    total_policies: int


class PromptVersionInfo(BaseModel):
    id: PromptVersionId
    name: str
    step: str
    purpose: str
    tool_model: str
    settings: str
    system_prompt: str
    user_prompt_template: str
    variables: Dict[str, str]
    examples_included: int
    output_format: str


class HealthResponse(BaseModel):
    status: str
    ai_mode: str
    model: str
    demo_enabled: bool
