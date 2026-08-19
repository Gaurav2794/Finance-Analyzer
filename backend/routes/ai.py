"""
backend/routes/ai.py
POST /api/documents/{id}/ai
Enforces ownership validation: users can only query AI on their own documents.
Logs interaction history in the database.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user, get_user_document
from backend.db.database import get_db
from backend.db.models import AIInteraction, User
from backend.services.ai_service import generate_ai_response
from backend.services.storage_service import (
    financial_data_path,
    load_json,
    review_result_path,
)

router = APIRouter()


class AIRequest(BaseModel):
    finding_id: Optional[str] = None
    question: str = "Why was this flagged?"
    category: Optional[str] = None

AIRequest.model_rebuild()


@router.post("/{document_id}/ai")
async def ask_ai(
    document_id: str,
    body: AIRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    POST /api/documents/{id}/ai
    Generate a grounded explanation for a finding or general report review.
    Uses server-side Gemini configuration with strict grounding in Team 1 + Team 2 data.
    """
    # Enforce document ownership
    get_user_document(document_id, db, current_user)

    fd = load_json(financial_data_path(document_id))
    rr = load_json(review_result_path(document_id))

    if fd is None or rr is None:
        raise HTTPException(500, "Output files not available.")

    ai_result = generate_ai_response(
        question=body.question,
        fd=fd,
        rr=rr,
        finding_id=body.finding_id,
        category=body.category,
    )

    # Persist interaction in database
    try:
        interaction = AIInteraction(
            user_id=current_user.id,
            document_id=document_id,
            finding_id=body.finding_id,
            question=body.question,
            answer=ai_result.get("answer", ""),
            model=ai_result.get("model"),
            grounded=bool(ai_result.get("grounded", True)),
        )
        db.add(interaction)
        db.commit()
    except Exception:
        db.rollback()

    return ai_result
