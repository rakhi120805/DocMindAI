"""
Database session handling.

WHY A SEPARATE FILE FROM models.py:
`models.py` defines WHAT the data looks like (schema).
`session.py` defines HOW we connect to and talk to the database
(engine, sessions). Keeping them apart means you could point the same
models at Postgres later by only touching this file.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base
from backend.config.settings import settings


def _ensure_sqlite_directory_exists(database_url: str) -> None:
    """
    SQLite will create the DATABASE FILE itself if it's missing, but
    it will NOT create missing PARENT DIRECTORIES - it just fails with
    a fairly unhelpful "unable to open database file" error instead.
    This bit us directly: settings.py's default database_url changed
    to "sqlite:///./data/docmind.db" (consolidating persistent data
    under data/ for Docker), but nothing actually created that data/
    folder on a plain local run outside Docker (the Dockerfile's
    `mkdir -p data/...` only applies inside the container). Same root
    cause as needing `settings.upload_dir.mkdir(...)` in the upload
    router - any path we read from config needs its directory
    guaranteed to exist before something tries to write there.
    """
    if not database_url.startswith("sqlite:///"):
        return  # not SQLite (e.g. Postgres in some future setup) - nothing to do

    db_path = Path(database_url.replace("sqlite:///", "", 1))
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory_exists(settings.database_url)

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