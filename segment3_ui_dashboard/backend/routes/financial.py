"""
backend/routes/financial.py
GET /api/documents/{id}/financial-data  — returns raw Team 1 output
GET /api/documents/{id}/review          — returns raw Team 2 output
GET /api/documents/{id}/dashboard       — returns combined presentation response
GET /api/documents/{id}/findings        — returns findings list
GET /api/documents/{id}/report          — returns full report payload
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.services.storage_service import (
    JobStatus, get_job, financial_data_path, review_result_path, load_json
)
from backend.services.dashboard_service import build_dashboard

router = APIRouter()


def _require_completed(document_id: str):
    """Raise 404 if job unknown, 409 if not yet COMPLETED."""
    job = get_job(document_id)
    if not job:
        raise HTTPException(404, f"Document '{document_id}' not found.")
    if job["status"] == JobStatus.FAILED:
        raise HTTPException(500, f"Pipeline failed: {job.get('error')}")
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            409,
            f"Pipeline not yet complete. Current status: {job['status']}",
        )
    return job


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
async def get_financial_data(document_id: str):
    """Return the raw Team 1 financial_data.json output. Fields are unchanged."""
    _require_completed(document_id)
    return _load_fd(document_id)


@router.get("/{document_id}/review")
async def get_review(document_id: str):
    """Return the raw Team 2 review_result.json output. Fields are unchanged."""
    _require_completed(document_id)
    return _load_rr(document_id)


@router.get("/{document_id}/dashboard")
async def get_dashboard(document_id: str):
    """
    Return a combined, presentation-adapted response for the React dashboard.
    All financial values are sourced from Team 1/2 — never recalculated.
    """
    _require_completed(document_id)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    return build_dashboard(fd, rr)


@router.get("/{document_id}/findings")
async def get_findings(document_id: str):
    """Return the findings list from Team 2."""
    _require_completed(document_id)
    rr = _load_rr(document_id)
    from backend.services.dashboard_service import _adapt_findings
    return {
        "document_id": document_id,
        "summary": rr.get("findings", {}),
        "details": _adapt_findings(rr),
    }


@router.get("/{document_id}/report")
async def get_report(document_id: str):
    """
    Full report payload — same data as dashboard plus full analytical blocks.
    The AuditReport component must use the same data as the Dashboard.
    """
    _require_completed(document_id)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    dash = build_dashboard(fd, rr)
    # Attach full Team 2 check blocks for the detailed report sections
    dash["full_financial_metrics"] = rr.get("financial_metrics", {})
    dash["full_analytical_metrics"] = rr.get("analytical_metrics", {})
    dash["run_metadata"] = rr.get("run_metadata", {})
    return dash


@router.get("/{document_id}/wp514")
async def get_wp514_review(document_id: str):
    """
    Return the normalized WP-514 Financial Statement Review matrix.
    All data is sourced from Team 1 + Team 2 + Language Quality.
    """
    _require_completed(document_id)
    fd = _load_fd(document_id)
    rr = _load_rr(document_id)
    from backend.services.wp514_service import WP514Service
    return WP514Service.generate_review_matrix(fd, rr)
