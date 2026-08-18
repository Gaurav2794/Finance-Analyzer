"""
backend/services/evidence_service.py

Resolves source evidence for a finding from Team 1 and Team 2 data.
Does NOT build a new RAG engine. Reads existing source traces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def resolve_evidence(
    finding_id: str,
    fd: Dict[str, Any],
    rr: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve evidence for a finding_id from existing Team 1/2 source metadata.

    Returns a structured evidence block. If the exact passage is unavailable
    (RAG chunks not populated), the source metadata is still returned so the
    reviewer knows which document / page / note to consult.
    """
    # ── Step 1: Find the finding in Team 2 output ─────────────────────────────
    finding = _find_detail(rr, finding_id)

    if finding is None:
        return {
            "finding_id": finding_id,
            "status": "NOT_FOUND",
            "message": f"Finding '{finding_id}' not found in review result.",
            "source": None,
            "passage": None,
        }

    source_meta = finding.get("source") or {}

    # ── Step 2: Try to locate the source value in Team 1 balance/income/cf ────
    passage = None
    statement_evidence = _lookup_source_in_financial_data(source_meta, fd)

    # ── Step 3: Try RAG chunks if available ──────────────────────────────────
    rag_passage = _lookup_rag_chunk(fd, finding_id, finding)

    passage = rag_passage or statement_evidence

    return {
        "finding_id": finding_id,
        "status": "AVAILABLE" if passage else "METADATA_ONLY",
        "finding": {
            "id": finding.get("id") or finding.get("finding_id"),
            "finding_id": finding.get("finding_id") or finding.get("id"),
            "severity": finding.get("severity"),
            "category": finding.get("category"),
            "title": finding.get("title"),
            "description": finding.get("description"),
            "previous_value": finding.get("previous_value"),
            "current_value": finding.get("current_value"),
            "change_pct": finding.get("change_pct"),
            "threshold_pct": finding.get("threshold_pct"),
        },
        "source": source_meta if source_meta else None,
        "passage": passage,
        "message": (
            None if passage else
            "Exact passage not available — source metadata shown. "
            "Refer to the document at the page/note reference indicated."
        ),
    }


def _find_detail(rr: Dict[str, Any], finding_id: str) -> Optional[Dict[str, Any]]:
    """Locate a finding by finding_id or id in review_result.json findings.details."""
    try:
        details = rr["findings"]["details"]
        if isinstance(details, list):
            for f in details:
                if isinstance(f, dict):
                    if f.get("finding_id") == finding_id or f.get("id") == finding_id:
                        return f
    except (KeyError, TypeError):
        pass
    return None


def _lookup_source_in_financial_data(
    source_meta: Dict[str, Any],
    fd: Dict[str, Any],
) -> Optional[str]:
    """
    Given a source trace from Team 2, find the matching value in Team 1 data
    and format it as a human-readable evidence passage.
    """
    if not source_meta:
        return None

    raw_label = source_meta.get("raw_label")
    page = source_meta.get("page")
    note_ref = source_meta.get("note_ref")

    matches: List[str] = []
    for stmt_name, stmt in [
        ("Balance Sheet", fd.get("balance_sheet", {})),
        ("Income Statement", fd.get("income_statement", {})),
        ("Cash Flow Statement", fd.get("cash_flow_statement", {})),
    ]:
        for key, entry in stmt.items():
            if not isinstance(entry, dict):
                continue
            labels = entry.get("raw_labels", [])
            std_label = entry.get("standard_label", "")
            entry_source = entry.get("source", {}) or {}

            label_match = raw_label and (
                raw_label in labels or raw_label == std_label
            )
            page_match = page and entry_source.get("page") == page

            if label_match or page_match:
                values = entry.get("values", {})
                val_str = ", ".join(
                    f"{p}: {v}" for p, v in values.items()
                )
                matches.append(
                    f"{stmt_name} — {std_label}: {val_str} "
                    f"(Source: {entry_source.get('file', '?')}, "
                    f"Page {entry_source.get('page', '?')}"
                    + (f", {note_ref}" if note_ref else "") + ")"
                )

    return "\n".join(matches) if matches else None


def _lookup_rag_chunk(
    fd: Dict[str, Any],
    finding_id: str,
    finding: Dict[str, Any],
) -> Optional[str]:
    """
    Try to find a relevant RAG chunk from Team 1 rag_chunks.
    Returns None if RAG chunks are empty (common for Excel/CSV inputs).
    """
    chunks = fd.get("rag_chunks", [])
    if not chunks:
        return None

    title_words = set((finding.get("title") or "").lower().split())
    best = None
    best_score = 0

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        text = chunk.get("text", "")
        score = sum(1 for w in title_words if w in text.lower())
        if score > best_score:
            best_score = score
            best = chunk

    if best and best_score > 0:
        src = best.get("source", {}) or {}
        return (
            f"{best.get('text', '')}\n\n"
            f"(Source: {src.get('file', '?')}, Page {src.get('page', '?')})"
        )
    return None
