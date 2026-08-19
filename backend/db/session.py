"""
backend/db/session.py
Database session helpers and table initialization.
"""
from __future__ import annotations

import logging
from backend.db.database import Base, engine, SessionLocal
# Import models so they are registered on Base.metadata
from backend.db import models  # noqa: F401

log = logging.getLogger("team3.db")


def init_db() -> None:
    """
    Create all tables defined in models if they do not already exist.
    """
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database tables initialized successfully.")
    except Exception as exc:
        log.error("Failed to initialize database tables: %s", exc)
        raise
