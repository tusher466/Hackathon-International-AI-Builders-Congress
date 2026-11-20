"""DB engine and session management."""
from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import get_settings
from storage.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        # SQLite needs check_same_thread False for multi-thread use
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            echo=False,
            future=True,
        )
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    return _SessionLocal


def init_db() -> None:
    """Create tables if not exist."""
    settings = get_settings()
    settings.ensure_dirs()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    SessionLocal = get_session_local()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Session:
    """For non-FastAPI usage, return session that caller must close."""
    SessionLocal = get_session_local()
    return SessionLocal()
