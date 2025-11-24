# File: backend/app/database.py (NEW FILE)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# SQLAlchemy's engine requires a string URL. Pydantic's AnyUrl returns a
# specialized object, so we cast to str to avoid type errors during startup.
engine = create_engine(str(settings.database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()