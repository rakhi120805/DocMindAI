"""
Database session handling.

WHY A SEPARATE FILE FROM models.py:
`models.py` defines WHAT the data looks like (schema).
`session.py` defines HOW we connect to and talk to the database
(engine, sessions). Keeping them apart means you could point the same
models at Postgres later by only touching this file.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base
from backend.config.settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables. Called once at app startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency. Yields a DB session per-request and always
    closes it, even if the request raises an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
