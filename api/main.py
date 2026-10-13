"""FastAPI Application Entry Point for CombustionLens.

Thin REST API routing requests directly to headless logic in core/.
Exposes:
- POST /api/ask
- GET  /api/experiments
- POST /api/compare
- POST /api/brief
- GET  /api/status
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.routes_ask import router as ask_router
from api.routes_compare import router as compare_router
from api.routes_brief import router as brief_router
from api.routes_meta import router as meta_router

app = FastAPI(
    title="CombustionLens API",
    description="AI-powered spacecraft fire safety insights from NASA microgravity combustion research.",
    version="1.0.0"
)

import os

# Allowed origins for development and deployment
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:7860",
    "http://localhost:7860",
]
cors_env = os.environ.get("CORS_ORIGINS")
if cors_env:
    ALLOWED_ORIGINS.extend([o.strip() for o in cors_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(ask_router)
app.include_router(compare_router)
app.include_router(brief_router)
app.include_router(meta_router)


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": "CombustionLens API"}


# Serve static frontend build if present (for Docker / production deployment)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    from fastapi.responses import FileResponse

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_spa_root():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Security: Prevent path traversal attacks (e.g. /../../etc/passwd)
        dist_resolved = frontend_dist.resolve()
        try:
            target_file = (frontend_dist / full_path).resolve()
            if not target_file.is_relative_to(dist_resolved):
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Path not found")
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Path not found")

        if full_path and target_file.is_file():
            return FileResponse(target_file)
        
        # If target has a file extension (e.g. .yaml, .js, .css, .json, .ico), do not fallback to index.html
        if "." in Path(full_path).name:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(frontend_dist / "index.html")


