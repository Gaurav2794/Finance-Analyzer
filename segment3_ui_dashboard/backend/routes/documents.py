"""
backend/routes/documents.py

Upload, pipeline execution, and status endpoints.
"""
from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File

from backend.config import SUPPORTED_EXTENSIONS
from backend.services.storage_service import (
    JobStatus,
    create_job,
    get_job,
    financial_data_path,
    review_result_path,
    upload_path,
    load_json,
    update_job,
)

log = logging.getLogger("team3.routes.documents")
router = APIRouter()


# ── Background pipeline runner ────────────────────────────────────────────────

def _run_pipeline(doc_id: str, saved_file: str) -> None:
    """
    Background task: run S1 then S2.
    Updates job status at each stage.
    Never modifies Team 1 or Team 2 code.
    """
    from backend.services.pipeline_service import run_segment1, run_segment2

    fin_path = str(financial_data_path(doc_id))
    rev_path = str(review_result_path(doc_id))

    try:
        # Stage 1: Segment 1
        update_job(doc_id, JobStatus.EXTRACTING, "Document Extraction — Segment 1 running")
        log.info("[%s] Invoking Segment 1", doc_id)
        run_segment1(input_path=saved_file, output_path=fin_path)

        # Verify output
        if not Path(fin_path).exists():
            raise RuntimeError("Segment 1 did not produce financial_data.json")
        update_job(doc_id, JobStatus.EXTRACTED, "Financial Data Extracted")
        log.info("[%s] Segment 1 complete", doc_id)

        # Stage 2: Segment 2
        update_job(doc_id, JobStatus.REVIEWING, "Financial Review — Segment 2 running")
        log.info("[%s] Invoking Segment 2", doc_id)
        run_segment2(input_path=fin_path, output_path=rev_path)

        # Verify output
        if not Path(rev_path).exists():
            raise RuntimeError("Segment 2 did not produce review_result.json")

        # Sanity-parse to make sure the JSON is valid
        result = load_json(Path(rev_path))
        if result is None:
            raise RuntimeError("review_result.json could not be parsed")

        update_job(doc_id, JobStatus.COMPLETED, "Dashboard Ready")
        log.info("[%s] Pipeline complete — COMPLETED", doc_id)

    except Exception as exc:
        log.exception("[%s] Pipeline FAILED: %s", doc_id, exc)
        update_job(doc_id, JobStatus.FAILED, "Pipeline failed", error=str(exc))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    POST /api/documents/upload
    Accept a financial document, validate it, save it,
    and kick off the Segment 1 → Segment 2 pipeline in the background.
    """
    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type: '{suffix}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    # Create job
    doc_id = create_job(file.filename or "unknown")

    # Save upload
    dest = upload_path(doc_id, file.filename or f"upload{suffix}")
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc

    log.info("[%s] Saved upload to %s", doc_id, dest)

    # Start pipeline in background
    background_tasks.add_task(_run_pipeline, doc_id, str(dest))

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": JobStatus.UPLOADED,
        "message": "Document uploaded. Pipeline started.",
    }


@router.get("/{document_id}/status")
async def get_status(document_id: str):
    """
    GET /api/documents/{document_id}/status
    Returns the real pipeline status — never simulated.
    """
    job = get_job(document_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return {
        "document_id": document_id,
        "status": job["status"],
        "step": job["step"],
        "error": job.get("error"),
        "source_filename": job.get("source_filename"),
    }
