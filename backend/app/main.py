"""PolicyPilot AI - FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import complaints, dashboard, policies, prompts
from .schemas.models import HealthResponse

app = FastAPI(
    title="PolicyPilot AI API",
    description=(
        "Policy-grounded customer support and complaint-resolution assistant. "
        "All policy data used in the demo is fictional."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(policies.router)
app.include_router(complaints.router)
app.include_router(prompts.router)


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        ai_mode=settings.ai_mode,
        model=settings.gemini_model,
        demo_enabled=settings.enable_demo_mode,
    )


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "name": "PolicyPilot AI API",
        "docs": "/docs",
        "health": "/api/health",
        "ai_mode": settings.ai_mode,
    }
