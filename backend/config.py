"""
backend/config.py — Environment configuration for Team 3 FastAPI layer.
All secrets come from environment variables. Never hardcoded.
"""
import os
from pathlib import Path

# ── Repository root (Finance-Analyzer/) ──────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Upload storage ────────────────────────────────────────────────────────────
UPLOADS_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(REPO_ROOT / "uploads")))
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ── Per-document output storage ───────────────────────────────────────────────
# Each document gets: outputs/{document_id}/financial_data.json
#                                           /review_result.json
OUTPUTS_DIR: Path = Path(os.getenv("OUTPUT_DIR", str(REPO_ROOT / "outputs")))
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Supported upload formats (must match Segment 1 capability) ───────────────
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".md", ".txt"}

# ── CORS ─────────────────────────────────────────────────────────────────────
_frontend_env = os.getenv("FRONTEND_URL", "")
_cors_env = os.getenv("CORS_ORIGINS", "")
_raw_origins = []
if _frontend_env:
    _raw_origins.extend([o.strip() for o in _frontend_env.split(",") if o.strip()])
if _cors_env:
    _raw_origins.extend([o.strip() for o in _cors_env.split(",") if o.strip()])
if not _raw_origins:
    _raw_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
CORS_ORIGINS = [o for o in _raw_origins if o != "*"]

# ── API settings ──────────────────────────────────────────────────────────────
API_PREFIX = "/api"
