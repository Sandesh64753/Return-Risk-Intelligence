import sys
from pathlib import Path

# Resolve backend directory across local dev, installed package, and container environments
BASE_DIR = Path(__file__).resolve().parent.parent.parent
candidates = [
    BASE_DIR / "backend",
    Path.cwd() / "backend",
    Path.cwd(),
]
BACKEND_DIR = None
for cand in candidates:
    if cand.is_dir() and (cand / "app").is_dir():
        BACKEND_DIR = cand
        if str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
        break

if not BACKEND_DIR and str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    import uvicorn
    from app.config import settings  # type: ignore
    from app.main import app  # type: ignore
except ImportError:
    try:
        from backend.app.config import settings  # type: ignore
        from backend.app.main import app  # type: ignore
    except ImportError:
        settings = None  # type: ignore
        app = None  # type: ignore


def main() -> None:
    """Run the FastAPI web server using Uvicorn."""
    import uvicorn

    host = getattr(settings, "HOST", "0.0.0.0") if settings else "0.0.0.0"
    port = getattr(settings, "PORT", 8000) if settings else 8000
    reload = getattr(settings, "DEBUG", False) if settings else False
    app_name = (
        getattr(settings, "APP_NAME", "Product Return Risk Intelligence Platform")
        if settings
        else "Product Return Risk Intelligence Platform"
    )

    print(f"Starting {app_name} on http://{host}:{port}")

    app_dir_str = str(BACKEND_DIR) if BACKEND_DIR else None
    if app_dir_str:
        uvicorn.run("app.main:app", host=host, port=port, reload=reload, app_dir=app_dir_str)
    else:
        uvicorn.run("app.main:app", host=host, port=port, reload=reload)


__all__ = ["app", "settings", "main"]

if __name__ == "__main__":
    main()
