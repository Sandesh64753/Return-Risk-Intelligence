import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings

logger = logging.getLogger("prduct_return_prediction.database")

def _create_database_engine():
    target_url = settings.DATABASE_URL
    engine_kwargs = {"pool_pre_ping": True}
    if target_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
        engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "300"))

    try:
        return create_engine(target_url, **engine_kwargs)
    except Exception as e:
        logger.error(
            f"Failed to create database engine for '{target_url}': {e}. Falling back to SQLite."
        )
        return create_engine("sqlite:///./return_intelligence.db", connect_args={"check_same_thread": False})


engine = _create_database_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()




def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified / initialized successfully.")
    except Exception as e:
        logger.exception(f"Error initializing database schema: {e}")
        raise
