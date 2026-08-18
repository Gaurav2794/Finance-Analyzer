"""
backend/services/pipeline_service.py

Calls Segment 1 and Segment 2 using their existing Python APIs.
This service DOES NOT contain any financial logic — it is a pure integration layer.

Team 1 API:  DocumentProcessingPipeline.process_file_or_directory()
Team 2 API:  run_pipeline(input_path, output_path)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger("team3.pipeline")

# ── Ensure repo root is on sys.path so segment1/2 imports resolve ─────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def run_segment1(
    input_path: str,
    output_path: str,
    company_name: str | None = None,
    industry: str | None = None,
) -> Dict[str, Any]:
    """
    Invoke the existing Segment 1 pipeline.
    DO NOT duplicate or modify Segment 1 logic.
    """
    from segment1_document_processing.src.pipeline import DocumentProcessingPipeline  # type: ignore

    log.info("[S1] Starting — input=%s, output=%s", input_path, output_path)
    result = DocumentProcessingPipeline.process_file_or_directory(
        input_path=input_path,
        company_name=company_name,
        industry=industry,
    )
    DocumentProcessingPipeline.save_output(result, output_path)
    log.info("[S1] Completed — output written to %s", output_path)
    return result


def run_segment2(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Invoke the existing Segment 2 pipeline.
    DO NOT duplicate or modify Segment 2 logic.
    """
    from segment2_financial_review.engine import run_pipeline  # type: ignore

    log.info("[S2] Starting — input=%s, output=%s", input_path, output_path)
    result = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        verbosity=logging.INFO,
    )
    log.info("[S2] Completed — output written to %s", output_path)
    return result
