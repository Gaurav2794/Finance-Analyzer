"""
backend/routes/ai.py
POST /api/documents/{id}/ai
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.storage_service import get_job, JobStatus, financial_data_path, review_result_path, load_json
from backend.services.ai_service import generate_ai_response

router = APIRouter()


class AIRequest(BaseModel):
    finding_id: Optional[str] = None
    question: str = "Why was this flagged?"
    category: Optional[str] = None

AIRequest.model_rebuild()


@router.post("/{document_id}/ai")
async def ask_ai(document_id: str, body: AIRequest):
    """
    POST /api/documents/{id}/ai
    Generate a grounded explanation for a finding or general report review.
    Uses Gemini API when configured, with strict grounding in Team 1 + Team 2 data.
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

    return generate_ai_response(
        question=body.question,
        fd=fd,
        rr=rr,
        finding_id=body.finding_id,
        category=body.category,
    )
