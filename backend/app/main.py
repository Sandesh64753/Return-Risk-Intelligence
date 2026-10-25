import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.auth.dependencies import AuthenticationRequiredException
from app.routers import api_router
from app.services.prediction_service import prediction_service

# Configure clean logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prduct_return_prediction")

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler for startup/shutdown logging and DB initialization."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")

    if prediction_service.is_ready():
        logger.info(
            f"Prediction service ready: model='{prediction_service.model_name}', "
            f"threshold={prediction_service.threshold:.4f}, "
            f"features={len(prediction_service.expected_features)}"
        )
    else:
        logger.warning("Prediction service failed to initialize model. Inference will be unavailable.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend applications (Vite, React dev servers, Nginx container)
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:80",
    "http://127.0.0.1:80",
]
extra_cors = os.getenv("CORS_ORIGINS")
if extra_cors:
    for origin in extra_cors.split(","):
        origin = origin.strip()
        if origin and origin not in cors_origins:
            cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API router
app.include_router(api_router)

# Unified single-container mode: serve compiled React SPA if available
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "true").lower() == "true"
FRONTEND_DIST_DIR = Path(os.getenv("FRONTEND_DIST_DIR", BASE_DIR / "frontend_dist"))
if not FRONTEND_DIST_DIR.exists():
    candidate_dist = BASE_DIR.parent / "frontend" / "dist"
    if candidate_dist.exists() and (candidate_dist / "index.html").exists():
        FRONTEND_DIST_DIR = candidate_dist

if SERVE_FRONTEND and FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    logger.info(f"Serving compiled React SPA from {FRONTEND_DIST_DIR}")
    frontend_assets = FRONTEND_DIST_DIR / "assets"
    if frontend_assets.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="frontend_assets")

    @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        # Do not hijack API or docs endpoints
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
            return JSONResponse(status_code=404, content={"detail": "Resource not found"})
        candidate_file = FRONTEND_DIST_DIR / full_path
        if full_path and candidate_file.is_file():
            return FileResponse(candidate_file)
        index_file = FRONTEND_DIST_DIR / "index.html"
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
else:
    @app.get("/", include_in_schema=False)
    async def api_root():
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "health": "/health",
        }


# Authentication redirect exception handler
@app.exception_handler(AuthenticationRequiredException)
async def auth_required_handler(request: Request, exc: AuthenticationRequiredException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication required. Please log in with your company credentials."},
    )


# Custom error handlers for clean UX and security
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Clean 404 handler returning JSON for API calls or React SPA index for browser routes."""
    if (
        SERVE_FRONTEND
        and FRONTEND_DIST_DIR.exists()
        and (FRONTEND_DIST_DIR / "index.html").exists()
        and not request.url.path.startswith(("/api/", "/health", "/docs", "/redoc", "/openapi.json"))
    ):
        index_file = FRONTEND_DIST_DIR / "index.html"
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Resource not found", "path": request.url.path},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Clean 500 handler preventing stack trace or system path disclosure."""
    logger.error(f"Internal server error processing request to {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
