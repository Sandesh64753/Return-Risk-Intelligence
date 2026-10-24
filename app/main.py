import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.auth.dependencies import AuthenticationRequiredException
from app.routers import (
    pages_router,
    auth_router,
    dashboard_router,
    prediction_router,
    analytics_router,
    recommendation_router,
    import_router,
    api_router,
)
from app.services.prediction_service import prediction_service

# Configure clean logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prduct_return_prediction")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


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

# Enable CORS for frontend applications (Vite, React dev servers)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directory
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount page and API routers
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(prediction_router)
app.include_router(analytics_router)
app.include_router(recommendation_router)
app.include_router(import_router)
app.include_router(api_router)


# Authentication redirect exception handler
@app.exception_handler(AuthenticationRequiredException)
async def auth_required_handler(request: Request, exc: AuthenticationRequiredException):
    """Redirect unauthenticated users accessing protected console pages directly to login."""
    return RedirectResponse(
        url=exc.redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


# Custom error handlers for clean UX and security
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Clean 404 handler returning HTML for browser requests or JSON for API calls."""
    if request.url.path.startswith("/api/") or request.headers.get("accept") == "application/json":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Resource not found", "path": request.url.path},
        )
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={"page_title": "Page Not Found"},
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Clean 500 handler preventing stack trace or system path disclosure."""
    logger.error(f"Internal server error processing request to {request.url.path}: {exc}")
    if request.url.path.startswith("/api/") or request.headers.get("accept") == "application/json":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please try again later."},
        )
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={
            "page_title": "Internal Error",
            "error_message": "An unexpected server condition occurred. Our operations team has been alerted.",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
