"""
backend/routes/documents.py

Authenticated Upload, pipeline execution, document listing, status, and management.
Enforces per-user ownership: all documents belong to the authenticated user.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user, get_user_document
from backend.config import SUPPORTED_EXTENSIONS
from backend.db.database import SessionLocal, get_db
from backend.db.models import Document, Finding, User
from backend.services.storage_service import (
    JobStatus,
    create_job,
    financial_data_path,
    get_job,
    load_json,
    output_dir,
    review_result_path,
    update_job,
    upload_path,
)

log = logging.getLogger("team3.routes.documents")
router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class DocumentSummaryResponse(BaseModel):
    id: str
    filename: str
    company_name: Optional[str] = None
    period: Optional[str] = None
    current_period: Optional[str] = None
    previous_period: Optional[str] = None
    currency: Optional[str] = None
    scale: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    overall_status: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# ── Background pipeline runner ────────────────────────────────────────────────

def _persist_completed_results(doc_id: str, user_id: str, fin_path: str, rev_path: str) -> None:
    """
    Helper to safely persist document metadata and finding records to DB
    once Segment 1 & Segment 2 finish successfully.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        fd = load_json(Path(fin_path)) or {}
        rr = load_json(Path(rev_path)) or {}

        # Extract metadata from Segment 1
        meta = fd.get("metadata", {})
        company_name = meta.get("company", {}).get("name") or rr.get("run_metadata", {}).get("company") or "Financial Statement"
        periods = meta.get("periods", [])
        curr_period = periods[0].get("period_key") if periods and isinstance(periods[0], dict) else None
        prev_period = periods[1].get("period_key") if len(periods) > 1 and isinstance(periods[1], dict) else None
        currency = meta.get("company", {}).get("currency") or "INR"
        scale = meta.get("company", {}).get("scale") or "Millions"

        # Extract scores from Segment 2
        overall_score = rr.get("overall_score")
        overall_status = rr.get("overall_status", "COMPLETED")

        # Update Document record
        doc.company_name = company_name
        doc.current_period = curr_period
        doc.previous_period = prev_period
        doc.currency = currency
        doc.scale = scale
        doc.overall_score = float(overall_score) if overall_score is not None else None
        doc.overall_status = overall_status
        doc.status = "COMPLETED"
        doc.financial_data_path = fin_path
        doc.review_result_path = rev_path

        # Persist findings summary to database
        raw_findings = rr.get("findings", {}).get("details", [])
        for f in raw_findings:
            if isinstance(f, dict):
                src = f.get("source") or f.get("source_ref") or {}
                if isinstance(src, dict):
                    src_ref = src.get("note_ref") or (f"Page {src.get('page')}" if src.get("page") else None)
                elif isinstance(src, str):
                    src_ref = src
                else:
                    src_ref = None

                finding_db = Finding(
                    document_id=doc_id,
                    finding_id=f.get("finding_id") or f.get("id") or "FND",
                    category=f.get("category", "GENERAL"),
                    check_name=f.get("title", "Audit Check"),
                    severity=f.get("severity", "REVIEW"),
                    status=f.get("status", "CLOSED"),
                    description=f.get("description") or f.get("explanation"),
                    expected_value=str(f.get("expected_value")) if f.get("expected_value") is not None else None,
                    actual_value=str(f.get("current_value")) if f.get("current_value") is not None else None,
                    difference=str(f.get("change")) if f.get("change") is not None else None,
                    source_reference=src_ref,
                )
                db.add(finding_db)

        db.commit()
        log.info("[%s] Persisted metadata and %d findings to database.", doc_id, len(raw_findings))
    except Exception as exc:
        log.exception("[%s] Failed to persist completion metadata: %s", doc_id, exc)
        db.rollback()
    finally:
        db.close()


def _run_pipeline(doc_id: str, saved_file: str, user_id: str) -> None:
    """
    Background task: run S1 then S2, then record persistence in database.
    Never modifies Team 1 or Team 2 code.
    """
    from backend.services.pipeline_service import run_segment1, run_segment2

    fin_path = str(financial_data_path(doc_id))
    rev_path = str(review_result_path(doc_id))

    try:
        # Stage 1: Segment 1
        update_job(doc_id, JobStatus.EXTRACTING, "Document Extraction — Segment 1 running")
        log.info("[%s] Invoking Segment 1 for user %s", doc_id, user_id)
        run_segment1(input_path=saved_file, output_path=fin_path)

        if not Path(fin_path).exists():
            raise RuntimeError("Segment 1 did not produce financial_data.json")
        update_job(doc_id, JobStatus.EXTRACTED, "Financial Data Extracted")
        log.info("[%s] Segment 1 complete", doc_id)

        # Stage 2: Segment 2
        update_job(doc_id, JobStatus.REVIEWING, "Financial Review — Segment 2 running")
        log.info("[%s] Invoking Segment 2 for user %s", doc_id, user_id)
        run_segment2(input_path=fin_path, output_path=rev_path)

        if not Path(rev_path).exists():
            raise RuntimeError("Segment 2 did not produce review_result.json")

        result = load_json(Path(rev_path))
        if result is None:
            raise RuntimeError("review_result.json could not be parsed")

        update_job(doc_id, JobStatus.COMPLETED, "Dashboard Ready")
        log.info("[%s] Pipeline complete — COMPLETED", doc_id)

        # Persist results in DB
        _persist_completed_results(doc_id, user_id, fin_path, rev_path)

    except Exception as exc:
        log.exception("[%s] Pipeline FAILED: %s", doc_id, exc)
        update_job(doc_id, JobStatus.FAILED, "Pipeline failed", error=str(exc))
        
        # Update database with failed status
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "FAILED"
                doc.error_message = str(exc)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    POST /api/documents/upload
    Accept financial document, create user-owned Document DB record, save file,
    and kick off Segment 1 → Segment 2 pipeline.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type: '{suffix}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    # Create in-memory job
    doc_id = create_job(file.filename or "unknown")

    # Save upload to disk
    dest = upload_path(doc_id, file.filename or f"upload{suffix}")
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc

    log.info("[%s] Saved upload to %s for user %s", doc_id, dest, current_user.email)

    # Create user-owned Document record in Database
    doc_record = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename or "document",
        status="UPLOADED",
        upload_path=str(dest),
    )
    db.add(doc_record)
    db.commit()

    # Start pipeline in background
    background_tasks.add_task(_run_pipeline, doc_id, str(dest), current_user.id)

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": JobStatus.UPLOADED,
        "message": "Document uploaded. Pipeline started.",
    }


@router.get("", response_model=List[DocumentSummaryResponse])
async def list_user_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    GET /api/documents
    Return audit history belonging exclusively to the authenticated user.
    """
    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

    results = []
    for d in docs:
        period_label = None
        if d.current_period and d.previous_period:
            period_label = f"{d.current_period} vs {d.previous_period}"
        elif d.current_period:
            period_label = d.current_period

        results.append(DocumentSummaryResponse(
            id=d.id,
            filename=d.filename,
            company_name=d.company_name or "Financial Statement",
            period=period_label,
            current_period=d.current_period,
            previous_period=d.previous_period,
            currency=d.currency,
            scale=d.scale,
            status=d.status,
            overall_score=d.overall_score,
            overall_status=d.overall_status,
            created_at=d.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ))
    return results


@router.get("/{document_id}", response_model=DocumentSummaryResponse)
async def get_document_metadata(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    GET /api/documents/{document_id}
    Retrieves metadata for a specific document with strict ownership verification.
    """
    d = get_user_document(document_id, db, current_user)
    period_label = f"{d.current_period} vs {d.previous_period}" if d.current_period and d.previous_period else d.current_period
    return DocumentSummaryResponse(
        id=d.id,
        filename=d.filename,
        company_name=d.company_name or "Financial Statement",
        period=period_label,
        current_period=d.current_period,
        previous_period=d.previous_period,
        currency=d.currency,
        scale=d.scale,
        status=d.status,
        overall_score=d.overall_score,
        overall_status=d.overall_status,
        created_at=d.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    DELETE /api/documents/{document_id}
    Deletes user's document record and removes associated storage directories.
    """
    doc = get_user_document(document_id, db, current_user)

    # Delete database record (cascades findings & ai_interactions)
    db.delete(doc)
    db.commit()

    # Remove storage files safely
    try:
        u_dir = upload_path(document_id, "").parent
        if u_dir.exists():
            shutil.rmtree(u_dir, ignore_errors=True)
        o_dir = output_dir(document_id)
        if o_dir.exists():
            shutil.rmtree(o_dir, ignore_errors=True)
    except Exception as exc:
        log.warning("[%s] Error cleaning storage: %s", document_id, exc)

    return {"status": "ok", "message": f"Document '{document_id}' deleted successfully."}


@router.get("/{document_id}/status")
async def get_status(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    GET /api/documents/{document_id}/status
    Returns the real pipeline status with ownership verification.
    """
    get_user_document(document_id, db, current_user)
    job = get_job(document_id)
    if not job:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            return {
                "document_id": document_id,
                "status": doc.status,
                "step": "Completed" if doc.status == "COMPLETED" else doc.status,
                "error": doc.error_message,
                "source_filename": doc.filename,
            }
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return {
        "document_id": document_id,
        "status": job["status"],
        "step": job["step"],
        "error": job.get("error"),
        "source_filename": job.get("source_filename"),
    }
