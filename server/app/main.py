"""Atlas API entrypoint.

Serves the JSON API under ``/api`` plus ``/healthz``, and (when a built SPA
exists) the static frontend with client-side routing fallback. Demo-only routes
are registered exclusively when ``APP_MODE=demo``; a production process never
imports the demo route module.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import create_auth_provider
from .config import Settings, get_settings
from .errors import install_error_handlers
from .gemini import create_gemini
from .observability import log_event
from .rate_limit import RateLimiter
from .store import create_store

_MISSING_WEB_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Atlas — frontend not built</title>
<style>body{{font-family:system-ui,sans-serif;max-width:40rem;margin:4rem auto;padding:0 1rem;color:#132029;line-height:1.6}}
code{{background:#eef1ee;padding:.15rem .35rem;border-radius:.25rem}}</style></head>
<body><h1>Frontend not built yet</h1>
<p>The API is running. To see the app:</p>
<ul><li>Development: run <code>npm run dev</code> in <code>web/</code> and open the Vite URL, or</li>
<li>Single-service mode: run <code>npm run build</code> in <code>web/</code>, then reload this page.</li></ul>
<p>API health: <a href="/healthz">/healthz</a></p></body></html>"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        log_event(
            "app_start",
            app_mode=settings.app_mode,
            cloud_configured=settings.cloud_configured,
            demo_routes=settings.is_demo,
        )
        yield
        log_event("app_stop")

    app = FastAPI(title="Atlas", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.store = create_store(settings)
    app.state.auth_provider = create_auth_provider(settings)
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.gemini = create_gemini(settings)

    install_error_handlers(app)

    # Seed the sample catalogue and synthetic mentor corpus in demo mode only,
    # so the advice journey and discovery are runnable without cloud
    # credentials. Every catalogue entry carries `is_sample_content=true` and
    # every mentor `is_synthetic=true` (old spec sections 7/8). Production
    # stores are seeded explicitly with `python -m app.seed` (never as a side
    # effect of booting, which would touch Firestore credentials during
    # construction).
    if settings.is_demo:
        from .catalogue import INTERESTS, seed_catalogue
        from .mentor_corpus import MENTORS_COLLECTION, seed_mentors

        if app.state.store.list(INTERESTS, limit=1) == []:
            seeded = seed_catalogue(app.state.store)
            log_event("catalogue_seeded", **seeded)
        if app.state.store.list(MENTORS_COLLECTION, limit=1) == []:
            seeded_mentors = seed_mentors(app.state.store)
            log_event("mentors_seeded", **seeded_mentors)

    @app.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/config")
    async def api_config() -> dict[str, object]:
        """Public, non-sensitive runtime flags for the frontend. No secrets."""
        return {
            "app_mode": settings.app_mode,
            "demo": settings.is_demo,
            "ai_available": settings.cloud_configured,
            "notice": "Prototype using synthetic data." if settings.is_demo else None,
        }

    # --- Application routes (demo route module only imported in demo mode) ---
    from .routes.auth import router as auth_router
    from .routes.interests import router as interests_router
    from .routes.library import router as library_router
    from .routes.mentors import router as mentors_router
    from .routes.needs import router as needs_router
    from .routes.public import router as public_router
    from .routes.sessions import router as sessions_router

    app.include_router(auth_router)
    app.include_router(interests_router)
    app.include_router(library_router)
    app.include_router(mentors_router)
    app.include_router(needs_router)
    app.include_router(public_router)
    app.include_router(sessions_router)

    if settings.is_demo:
        from .routes.dev import router as dev_router

        app.include_router(dev_router)

    # --- Static SPA ---------------------------------------------------------
    dist = Path(settings.web_dist)
    if dist.is_dir():
        assets_dir = dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_or_not_found(full_path: str) -> object:
        if full_path.startswith(("api/", "healthz")):
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "not_found", "message": "Unknown API route."}},
            )
        index = Path(settings.web_dist) / "index.html"
        if index.is_file():
            return FileResponse(index)
        return HTMLResponse(content=_MISSING_WEB_HTML, status_code=503)

    return app


app = create_app()
