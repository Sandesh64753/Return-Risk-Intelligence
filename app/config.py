import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACT_PATH = BASE_DIR / "artifacts" / "product_return_prediction.joblib"


class Settings:
    APP_NAME: str = "Product Return Intelligence Platform"
    APP_DESCRIPTION: str = (
        "Multi-Company Product Return Intelligence, Analytics & Risk Decision Platform."
    )
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Security and Session Management
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-secure-session-signing-key-change-for-production-min32bytes"
    )
    SESSION_COOKIE_NAME: str = "company_session"
    SESSION_MAX_AGE_SECONDS: int = int(os.getenv("SESSION_MAX_AGE", str(60 * 60 * 24 * 7)))  # 7 days
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true" or ENVIRONMENT == "production"
    COOKIE_SAMESITE: str = "lax"

    # Database connection string (SQLite for development / PostgreSQL for production)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./return_intelligence.db")

    # Path to serialized model bundle
    ARTIFACT_PATH: Path = Path(os.getenv("ARTIFACT_PATH", str(DEFAULT_ARTIFACT_PATH)))

    # Operational decision threshold; defaults to validation-tuned threshold (~0.3974)
    DEFAULT_THRESHOLD: float = 0.397378359285296
    OVERRIDE_THRESHOLD: Optional[float] = (
        float(os.getenv("PREDICTION_THRESHOLD")) if os.getenv("PREDICTION_THRESHOLD") else None
    )

    # Operational analytics configurations
    DEFAULT_MIN_SAMPLE_SIZE: int = int(os.getenv("MIN_SAMPLE_SIZE", "5"))


settings = Settings()
