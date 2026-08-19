"""
backend/services/storage_service.py

Manages per-document job state and file paths.
No financial logic — purely I/O and state tracking.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from backend.config import OUTPUTS_DIR, UPLOADS_DIR


class JobStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ── In-memory job store (sufficient for demo; swap for Redis/DB in production) ──
_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}


def create_job(source_filename: str) -> str:
    """Create a new job entry and return its document_id."""
    doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
    with _lock:
        _jobs[doc_id] = {
            "document_id": doc_id,
            "source_filename": source_filename,
            "status": JobStatus.UPLOADED,
            "step": "Document Uploaded",
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
    return doc_id


def update_job(doc_id: str, status: JobStatus, step: str, error: Optional[str] = None) -> None:
    with _lock:
        if doc_id in _jobs:
            _jobs[doc_id]["status"] = status
            _jobs[doc_id]["step"] = step
            _jobs[doc_id]["error"] = error
            _jobs[doc_id]["updated_at"] = time.time()


def get_job(doc_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        job = _jobs.get(doc_id)
        if job:
            return dict(job)
    return None


# ── File path helpers ─────────────────────────────────────────────────────────

def upload_path(doc_id: str, filename: str) -> Path:
    p = UPLOADS_DIR / doc_id
    p.mkdir(parents=True, exist_ok=True)
    return p / filename


def output_dir(doc_id: str) -> Path:
    p = OUTPUTS_DIR / doc_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def financial_data_path(doc_id: str) -> Path:
    return output_dir(doc_id) / "financial_data.json"


def review_result_path(doc_id: str) -> Path:
    return output_dir(doc_id) / "review_result.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely; return None on any error."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None
