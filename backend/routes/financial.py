"""
backend/routes/financial.py

Authenticated endpoints for Financial Data, Review Results, Presentation Dashboard,
Findings, Full Audit Report, and WP-514 Matrix.
Enforces per-document ownership: users can only access their own documents.
"""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user, get_user_document
from backend.db.database import get_db
from backend.db.models import User
from backend.services.dashboard_service import build_dashboard
from backend.services.storage_service import (
    JobStatus,
    financial_data_path,
    get_job,
    load_json,
    review_result_path,
)

router = APIRouter()


def _require_completed(document_id: str, db: Session, current_user: User):
    """
    Verify ownership first.
    Raise 404 if document does not belong to user or is unknown.
    Raise 409 if pipeline not yet complete.
    """
    doc = get_user_document(document_id, db, current_user)
    job = get_job(document_id)

    if job:
        if job["status"] == JobStatus.FAILED:
            raise HTTPException(500, f"Pipeline failed: {job.get('error')}")
        if job["status"] != JobStatus.COMPLETED:
            raise HTTPException(
                409,
                f"Pipeline not yet complete. Current status: {job['status']}",
            )
    elif doc.status == "FAILED":
        raise HTTPException(500, f"Pipeline failed: {doc.error_message}")
    elif doc.status != "COMPLETED":
        raise HTTPException(409, f"Pipeline not yet complete. Status: {doc.status}")

    return doc


def _load_fd(document_id: str):
    path = financial_data_path(document_id)
    data = load_json(path)
    if data is None:
        raise HTTPException(404, "financial_data.json not found or invalid.")
    return data


def _load_rr(document_id: str):
    path = review_result_path(document_id)
    data = load_json(path)
    if data is None:
        raise HTTPException(404, "review_result.json not found or invalid.")
    return data


@router.get("/{document_id}/financial-data")
async def get_financial_data(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return raw Team 1 financial_data.json output with ownership verification."""
    _require_completed(document_id, db, current_user)
    return _load_fd(document_id)


@router.get("/{document_id}/review")
async def get_review(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return raw Team 2 review_result.json output with ownership verification."""
    _require_completed(document_id, db, current_user)
    return _load_rr(document_id)


@router.get("/{document_id}/dashboard")
async def get_dashboard(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Return combined presentation response for the React dashboard.
    All values sourced directly from Team 1 & Team 2 — never recalculated.
    """
    _require_completed(document_id, db, current_user)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    return build_dashboard(fd, rr)


@router.get("/{document_id}/findings")
async def get_findings(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return findings list from Team 2 with ownership verification."""
    _require_completed(document_id, db, current_user)
    rr = _load_rr(document_id)
    from backend.services.dashboard_service import _adapt_findings
    return {
        "document_id": document_id,
        "summary": rr.get("findings", {}),
        "details": _adapt_findings(rr),
    }


@router.get("/{document_id}/report")
async def get_report(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Full report payload with ownership verification.
    """
    _require_completed(document_id, db, current_user)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    dash = build_dashboard(fd, rr)
    dash["full_financial_metrics"] = rr.get("financial_metrics", {})
    dash["full_analytical_metrics"] = rr.get("analytical_metrics", {})
    dash["run_metadata"] = rr.get("run_metadata", {})
    return dash


@router.get("/{document_id}/wp514")
async def get_wp514_review(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Return normalized WP-514 Financial Statement Review matrix with ownership verification.
    """
    _require_completed(document_id, db, current_user)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    from backend.services.wp514_service import WP514Service
    return WP514Service.generate_review_matrix(fd, rr)
