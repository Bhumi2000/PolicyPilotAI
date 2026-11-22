"""Exposes the prompt version definitions used by the app and the PDF."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from ..prompts.versions import PROMPTS
from ..schemas.models import PromptVersionInfo

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("", response_model=List[PromptVersionInfo])
def get_prompts() -> List[PromptVersionInfo]:
    return [PROMPTS["v1"], PROMPTS["v2"], PROMPTS["v3"]]


@router.get("/{version_id}", response_model=PromptVersionInfo)
def get_prompt(version_id: str) -> PromptVersionInfo:
    prompt = PROMPTS.get(version_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Unknown prompt version.")
    return prompt
