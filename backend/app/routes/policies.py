"""Policy upload, listing and retrieval endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..schemas.models import PolicyClause, PolicyDetail, PolicySummary, PolicyTextRequest
from ..services.pdf_service import PdfExtractionError, extract_text_from_pdf
from ..services.retrieval import split_clauses
from ..store import add_policy, delete_policy, get_policy, list_policies, new_id

router = APIRouter(prefix="/api/policies", tags=["policies"])


def _build_policy(name: str, text: str, source_type: str) -> PolicyDetail:
    clauses = split_clauses(text)
    extracted = [
        PolicyClause(clause_id=f"c{index}", heading=heading, text=body)
        for index, (heading, body) in enumerate(clauses, start=1)
    ]
    return PolicyDetail(
        id=new_id("pol"),
        name=name,
        source_type=source_type,
        characters=len(text),
        clauses=len(extracted),
        uploaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        text=text,
        extracted_clauses=extracted,
    )


@router.post("/upload", response_model=PolicyDetail)
async def upload_policy(file: UploadFile = File(...)) -> PolicyDetail:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    data = await file.read()
    try:
        text = extract_text_from_pdf(data)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    policy = _build_policy(file.filename or "policy.pdf", text, "pdf")
    return add_policy(policy)


@router.post("/text", response_model=PolicyDetail)
def add_text_policy(payload: PolicyTextRequest) -> PolicyDetail:
    policy = _build_policy(payload.name, payload.text.strip(), "text")
    return add_policy(policy)


@router.get("", response_model=List[PolicySummary])
def get_policies() -> List[PolicySummary]:
    return [
        PolicySummary(
            id=policy.id,
            name=policy.name,
            source_type=policy.source_type,
            characters=policy.characters,
            clauses=policy.clauses,
            uploaded_at=policy.uploaded_at,
        )
        for policy in list_policies()
    ]


@router.get("/{policy_id}", response_model=PolicyDetail)
def get_policy_detail(policy_id: str) -> PolicyDetail:
    policy = get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


@router.delete("/{policy_id}")
def remove_policy(policy_id: str) -> dict:
    if not delete_policy(policy_id):
        raise HTTPException(status_code=404, detail="Policy not found.")
    return {"deleted": policy_id}
