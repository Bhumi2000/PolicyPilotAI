"""Thin async client for the Google Gemini REST API.

Only the live path lives here. Demo/offline behaviour is handled explicitly in
``analysis_service`` so that a demo answer can never be mistaken for a real model
call.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from ..config import settings

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiError(Exception):
    """Raised when the Gemini API cannot be reached or returns an error."""


async def generate(
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
    json_mode: bool = True,
) -> str:
    """Call Gemini and return the raw text of the first candidate."""
    if not settings.gemini_api_key:
        raise GeminiError("GEMINI_API_KEY is not configured.")

    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature if temperature is not None else settings.gemini_temperature,
        },
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    url = _ENDPOINT.format(model=settings.gemini_model)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url, params={"key": settings.gemini_api_key}, json=payload
            )
    except httpx.HTTPError as exc:
        raise GeminiError(f"Could not reach the Gemini API: {exc}") from exc

    if response.status_code == 400 and "API key not valid" in response.text:
        raise GeminiError("The Gemini API key is invalid. Check GEMINI_API_KEY.")
    if response.status_code in (401, 403):
        raise GeminiError(
            f"Gemini rejected the API key ({response.status_code}). Check GEMINI_API_KEY."
        )
    if response.status_code == 404:
        raise GeminiError(
            f"Gemini model '{settings.gemini_model}' was not found or is not available "
            "for this API key. Set GEMINI_MODEL to a model your key can use."
        )
    if response.status_code == 429:
        raise GeminiError("Gemini rate limit hit (429). Wait a moment and retry.")
    if response.status_code >= 400:
        raise GeminiError(f"Gemini error {response.status_code}: {response.text[:200]}")

    try:
        data = response.json()
    except ValueError as exc:
        raise GeminiError("Gemini returned a non-JSON response.") from exc
    return _extract_text(data)


def _extract_text(data: Any) -> str:
    """Join the non-thought text parts of the first candidate."""
    if not isinstance(data, dict):
        raise GeminiError("Gemini returned an unexpected response shape.")
    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason")
        if reason:
            raise GeminiError(f"Gemini blocked the request ({reason}).")
        raise GeminiError("Gemini returned no candidates.")

    candidate = candidates[0] or {}
    parts = ((candidate.get("content") or {}).get("parts")) or []
    text = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and not part.get("thought")
    ).strip()
    if not text:
        finish = candidate.get("finishReason", "unknown")
        raise GeminiError(f"Gemini returned an empty answer (finish reason: {finish}).")
    return text
