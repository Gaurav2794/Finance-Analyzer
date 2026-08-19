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
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,*").split(",")

# ── API settings ──────────────────────────────────────────────────────────────
API_PREFIX = "/api"
