"""
Database session factory — SmartTrim 360.

Reads DATABASE_URL from the environment. Defaults to SQLite for local dev.
In production, set DATABASE_URL to a PostgreSQL connection string.

Usage (dependency injection):
    from app.db.session import get_db

    @router.get("/me")
    async def me(db: Session = Depends(get_db)):
        ...
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./smarttrim.db"           # dev default
)

# PostgreSQL requires the asyncpg driver; for async routes use
# create_async_engine + AsyncSession. For simplicity we use sync here
# and wrap calls in run_in_executor where needed.
#
# If DATABASE_URL starts with "postgres://", SQLAlchemy 1.4+ needs it
# rewritten to "postgresql://":
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,          # validates connections before use
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures
    it is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables. Called once on startup."""
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)
