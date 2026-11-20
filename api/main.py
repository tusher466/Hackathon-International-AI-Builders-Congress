"""FastAPI main with lifespan, CORS, exception handlers."""
from __future__ import annotations

import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from storage.db import init_db
from core.pipeline import get_pipeline
from knowledge.vector_store import get_vector_store

from api.routes_machines import router as machines_router
from api.routes_alerts import router as alerts_router
from api.routes_agents import router as agents_router
from api.routes_control import router as control_router
from api.routes_extended import router as extended_router
from api.websocket import router as ws_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting Factory Brain backend ENV={settings.ENV} STREAM_BACKEND={settings.STREAM_BACKEND} LLM_MODE={settings.LLM_MODE}")

    # Init DB
    init_db()

    # Init pipeline
    pipeline = get_pipeline()
    await pipeline.init()

    yield

    # Shutdown
    logger.info("Shutting down Factory Brain")
    await pipeline.shutdown()


app = FastAPI(title="Factory Brain", version="1.0.0", lifespan=lifespan)

# CORS
settings = get_settings()
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    logger.exception(f"Unhandled exception request_id={request_id} path={request.url.path} exc={exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc), "request_id": request_id},
    )


# Routers with base path /api/v1
app.include_router(machines_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(control_router, prefix="/api/v1")
app.include_router(extended_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check():
    settings = get_settings()
    pipeline = get_pipeline()
    # Check components
    store = get_vector_store()
    # Check stream
    stream_status = "ok"
    if pipeline._sim_task:
        if pipeline._sim_task.done():
            stream_status = "stopped"
    else:
        stream_status = "not_started" if not settings.AUTO_START_STREAM else "ok"

    # DB check
    db_status = "ok"
    try:
        from storage.db import get_db
        session = get_db()
        session.close()
    except Exception as e:
        db_status = f"error: {e}"

    # Vector store
    vs_status = "ok"
    try:
        count = store.count()
    except Exception as e:
        vs_status = f"error: {e}"
        count = 0

    # LLM mode
    llm_mode = "mock" if settings.is_mock_llm else "real"

    return {
        "status": "ok",
        "components": {
            "stream": {"status": stream_status, "backend": settings.STREAM_BACKEND},
            "db": {"status": db_status},
            "vector_store": {"status": vs_status, "count": count},
            "llm": {"mode": llm_mode, "model": settings.LLM_MODEL},
        },
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


@app.get("/api/v1/metrics/impact")
def metrics_impact():
    pipeline = get_pipeline()
    return pipeline.get_metrics()


# WebSocket - support both /ws/live and /api/v1/ws/live for frontend compatibility
# Original router at /ws/live (spec) and alias at /api/v1/ws/live (legacy frontend)
app.include_router(ws_router)  # /ws/live
app.include_router(ws_router, prefix="/api/v1")  # /api/v1/ws/live

# ---- Serve Frontend Static Files (merged project) ----
# Look for frontend dist in multiple possible locations: frontend/dist, Fontend/dist, ./dist, ../frontend/dist
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_frontend_candidates = [
    Path(__file__).parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "Fontend" / "dist",
    Path(__file__).parent.parent / "dist",
    Path(__file__).parent.parent.parent / "frontend" / "dist",
]

_frontend_dist = None
for _cand in _frontend_candidates:
    if _cand.exists() and (_cand / "index.html").exists():
        _frontend_dist = _cand
        logger.info(f"Found frontend dist at {_cand}")
        break

if _frontend_dist:
    # Mount assets
    assets_dir = _frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    # Serve index.html and static files, with SPA fallback
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Do not intercept api or ws or docs or openapi
        if full_path.startswith("api/") or full_path.startswith("ws") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("redoc"):
            # Let FastAPI return 404 for unknown api routes - but this handler is fallback, so we need to check if path is api but not matched earlier -> 404 JSON
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        # Check if file exists in dist
        file_path = _frontend_dist / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for SPA routing
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Factory Brain backend running", "version": "1.0.0", "api": "/api/v1/health", "frontend": "not built"}
else:
    logger.info("Frontend dist not found, serving API only")
    @app.get("/")
    def root():
        return {"message": "Factory Brain backend running", "version": "1.0.0", "api": "/api/v1/health", "frontend": "dist not found - run 'npm run build' in frontend", "hint": "Frontend should be built to frontend/dist or Fontend/dist"}
