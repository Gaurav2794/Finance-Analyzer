"""
backend/main.py — Team 3 FastAPI orchestration layer.
Single backend. No duplicate financial logic.
Includes User Authentication, Database Persistence, and Audit History.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Ensure repo root on sys.path ──────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

from backend.config import API_PREFIX, CORS_ORIGINS
from backend.db.session import init_db
from backend.routes import auth, documents, financial, evidence, ai

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

# ── Initialize Database Tables ────────────────────────────────────────────────
init_db()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance Analyzer — Team 3 API",
    description="Orchestration layer connecting Segment 1 → Segment 2 → React Dashboard with Authentication & Persistence",
    version="2.0.0",
)

# Ensure no wildcard origins with credentials enabled
origins = [o.strip() for o in CORS_ORIGINS if o.strip()]
for _loc in ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://localhost:3000", "http://127.0.0.1:3000"]:
    if _loc not in origins:
        origins.append(_loc)

if "*" in origins:
    origins.remove("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(documents.router, prefix=f"{API_PREFIX}/documents", tags=["Documents"])
app.include_router(financial.router, prefix=f"{API_PREFIX}/documents", tags=["Financial Data"])
app.include_router(evidence.router, prefix=f"{API_PREFIX}/documents", tags=["Evidence"])
app.include_router(ai.router, prefix=f"{API_PREFIX}/documents", tags=["AI"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Finance Analyzer Team 3 API"}


@app.get("/")
async def root():
    return {
        "service": "Finance Analyzer — Team 3 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
