"""
backend/routes/evidence.py
GET /api/documents/{id}/evidence/{finding_id}
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.services.storage_service import get_job, JobStatus, financial_data_path, review_result_path, load_json
from backend.services.evidence_service import resolve_evidence

router = APIRouter()


@router.get("/{document_id}/evidence/{finding_id}")
async def get_evidence(document_id: str, finding_id: str):
    """
    Return source evidence for a specific finding.
    Evidence comes from Team 1 source traces and Team 2 finding metadata.
    No fabrication — if unavailable, returns metadata_only status.
    """
    job = get_job(document_id)
    if not job:
        raise HTTPException(404, f"Document '{document_id}' not found.")
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(409, f"Pipeline not complete. Status: {job['status']}")

    fd = load_json(financial_data_path(document_id))
    rr = load_json(review_result_path(document_id))

    if fd is None or rr is None:
        raise HTTPException(500, "Output files not available.")

    return resolve_evidence(finding_id, fd, rr)
