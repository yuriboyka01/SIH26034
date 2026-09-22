"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from app.core.config import settings

def _build_db_url(url: str) -> str:
    """Ensure the URL uses the psycopg3 driver prefix exactly once."""
    if url.startswith("postgresql+psycopg://"):
        return url  # already correct
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url  # e.g. already has another driver specified

engine = create_engine(
    _build_db_url(settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_size=2,        # Render free tier + Neon serverless — keep it small
    max_overflow=5,
    pool_recycle=300,   # recycle connections every 5 min (Neon drops idle ones)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
