# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Extra options for SQLite
connect_args = {}
if settings.database_url.startswith("sqlite"):
    # Needed for SQLite when used in multi-threaded apps (like FastAPI + Uvicorn)
    connect_args["check_same_thread"] = False

# Create the SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=connect_args,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
