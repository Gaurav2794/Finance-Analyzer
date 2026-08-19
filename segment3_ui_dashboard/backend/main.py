"""
backend/main.py — Team 3 FastAPI orchestration layer.
Single backend. No duplicate financial logic.
"""
from __future__ import annotations

import logging
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
from backend.routes import documents, financial, evidence, ai

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance Analyzer — Team 3 API",
    description="Orchestration layer connecting Segment 1 → Segment 2 → React Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
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
        "docs": "/docs",
        "health": "/health",
    }
