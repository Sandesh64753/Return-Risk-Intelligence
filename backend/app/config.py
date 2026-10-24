import os
import re
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

# Robust .env loader supporting both backend/.env and root .env
def _load_env_file() -> None:
    env_candidates = [
        BASE_DIR / ".env",
        BASE_DIR.parent / ".env",
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
    ]
    for env_file in env_candidates:
        if env_file.is_file():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


_load_env_file()

def _resolve_database_url() -> str:
    # Read POSTGRESS_DATABASE (from .env), DATABASE_URL, or POSTGRES_DATABASE
    raw_url = (
        os.getenv("POSTGRESS_DATABASE")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_DATABASE")
        or "sqlite:///./return_intelligence.db"
    )
    # Ensure SQLAlchemy 2.0+ uses psycopg2-binary for postgresql://
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return raw_url


def _resolve_artifact_path() -> Path:
    env_path = os.getenv("ARTIFACT_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    candidates = [
        BASE_DIR / "artifacts" / "model.joblib",
        BASE_DIR / "artifacts" / "product_return_prediction.joblib",
        BASE_DIR.parent / "artifacts" / "model.joblib",
        BASE_DIR.parent / "artifacts" / "product_return_prediction.joblib",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return BASE_DIR / "artifacts" / "model.joblib"


class Settings:
    APP_NAME: str = "Product Return Intelligence Platform"
    APP_DESCRIPTION: str = (
        "Multi-Company Product Return Intelligence, Analytics & Risk Decision Platform."
    )
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Security and Session Management
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-secure-session-signing-key-change-for-production-min32bytes"
    )
    SESSION_COOKIE_NAME: str = "company_session"
    SESSION_MAX_AGE_SECONDS: int = int(os.getenv("SESSION_MAX_AGE", str(60 * 60 * 24 * 7)))  # 7 days
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true" or ENVIRONMENT == "production"
    COOKIE_SAMESITE: str = "lax"

    # Database connection string (Neon PostgreSQL or SQLite fallback)
    DATABASE_URL: str = _resolve_database_url()

    # Path to serialized model bundle
    ARTIFACT_PATH: Path = _resolve_artifact_path()

    # Operational decision threshold; defaults to validation-tuned threshold (~0.3974)
    DEFAULT_THRESHOLD: float = 0.397378359285296
    OVERRIDE_THRESHOLD: Optional[float] = (
        float(os.getenv("PREDICTION_THRESHOLD")) if os.getenv("PREDICTION_THRESHOLD") else None
    )

    # Operational analytics configurations
    DEFAULT_MIN_SAMPLE_SIZE: int = int(os.getenv("MIN_SAMPLE_SIZE", "5"))


settings = Settings()

