"""
backend/routes/evidence.py
GET /api/documents/{id}/evidence/{finding_id}
Enforces ownership validation: users can only view evidence for their own documents.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user, get_user_document
from backend.db.database import get_db
from backend.db.models import User
from backend.services.storage_service import (
    financial_data_path,
    load_json,
    review_result_path,
)
from backend.services.evidence_service import resolve_evidence

router = APIRouter()


@router.get("/{document_id}/evidence/{finding_id}")
async def get_evidence(
    document_id: str,
    finding_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Return source evidence for a specific finding with strict ownership validation.
    Evidence is sourced from Team 1 traces and Team 2 finding metadata.
    """
    # Enforce document ownership
    get_user_document(document_id, db, current_user)

    fd = load_json(financial_data_path(document_id))
    rr = load_json(review_result_path(document_id))

    if fd is None or rr is None:
        raise HTTPException(500, "Output files not available.")

    return resolve_evidence(finding_id, fd, rr)
