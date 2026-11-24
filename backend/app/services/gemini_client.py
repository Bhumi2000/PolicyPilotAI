"""Thin async client for the Google Gemini REST API.

Only the live path lives here. Demo/offline behaviour is handled explicitly in
``analysis_service`` so that a demo answer can never be mistaken for a real model
call.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, List, Optional, Tuple

import httpx

from ..config import settings

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiError(Exception):
    """Raised when the Gemini API cannot be reached or returns an error."""


# Status codes that mean "temporarily unavailable" - worth retrying / falling back.
_TRANSIENT = {429, 500, 502, 503, 504}
_RETRIES_PER_MODEL = 2
_BACKOFF_SECONDS = 1.5
# The browser gives up after 90s, so stop trying well before that.
_TOTAL_BUDGET_SECONDS = 75.0
_CALL_TIMEOUT_SECONDS = 45.0


class _TransientError(GeminiError):
    """Gemini is overloaded or rate-limited; another attempt may succeed."""


async def generate(
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
    json_mode: bool = True,
) -> Tuple[str, str]:
    """Call Gemini and return ``(text, model_used)``.

    Temporary failures (overloaded model, rate limit) are retried with backoff and
    then the configured fallback models are tried in order.
    """
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

    models: List[str] = []
    for model in [settings.gemini_model, *settings.gemini_fallback_models]:
        if model and model not in models:
            models.append(model)

    last_error: Optional[GeminiError] = None
    deadline = time.monotonic() + _TOTAL_BUDGET_SECONDS
    async with httpx.AsyncClient() as client:
        for model in models:
            for attempt in range(_RETRIES_PER_MODEL):
                remaining = deadline - time.monotonic()
                if remaining < 3:
                    break
                try:
                    timeout = min(_CALL_TIMEOUT_SECONDS, remaining)
                    return await _call(client, model, payload, timeout), model
                except _TransientError as exc:
                    last_error = exc
                    if attempt + 1 < _RETRIES_PER_MODEL:
                        await asyncio.sleep(_BACKOFF_SECONDS * (attempt + 1))
                except GeminiError as exc:
                    # A model that is missing for this key: try the next one.
                    last_error = exc
                    if "was not found" not in str(exc):
                        raise
                    break
    if last_error is None:
        last_error = GeminiError("Gemini did not answer in time.")
    raise GeminiError(
        f"{last_error} (tried: {', '.join(models)}). Please retry in a minute."
    )


async def _call(
    client: httpx.AsyncClient, model: str, payload: dict, timeout: float
) -> str:
    url = _ENDPOINT.format(model=model)
    try:
        response = await client.post(
            url, headers={"x-goog-api-key": settings.gemini_api_key},
            json=payload,
            timeout=timeout,
        )
    except httpx.TimeoutException as exc:
        raise _TransientError(f"Gemini model '{model}' timed out.") from exc
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
            f"Gemini model '{model}' was not found or is not available for this API key."
        )
    if response.status_code in _TRANSIENT:
        raise _TransientError(
            f"Gemini model '{model}' is temporarily unavailable ({response.status_code}, "
            "high demand or rate limit)"
        )
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
