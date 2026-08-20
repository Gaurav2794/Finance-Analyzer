"""
backend/db/database.py
SQLAlchemy database engine, sessionmaker, and Base declarative model.
Supports SQLite (development/default) and PostgreSQL (production).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Repository root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Database URL from environment; defaults to sqlite file in repository root
raw_db_url = os.getenv("DATABASE_URL", f"sqlite:///{REPO_ROOT}/finance_analyzer.db")
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# SQLite needs connect_args={"check_same_thread": False} for multi-threaded FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request
    and ensures clean closure after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
