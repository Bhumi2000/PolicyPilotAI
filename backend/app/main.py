"""PolicyPilot AI - FastAPI application entry point."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


# When the front-end has been built (frontend/dist), this single service also
# serves the React app, so the deployed prototype lives at one URL with no CORS.
_FRONTEND_DIST = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend",
        "dist",
    )
)

if os.path.isdir(_FRONTEND_DIST):
    _assets_dir = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        """Serve built files, falling back to index.html for client-side routes."""
        candidate = os.path.abspath(os.path.join(_FRONTEND_DIST, full_path))
        if (
            full_path
            and candidate.startswith(_FRONTEND_DIST + os.sep)
            and os.path.isfile(candidate)
        ):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

else:

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "name": "PolicyPilot AI API",
            "docs": "/docs",
            "health": "/api/health",
            "ai_mode": settings.ai_mode,
        }
