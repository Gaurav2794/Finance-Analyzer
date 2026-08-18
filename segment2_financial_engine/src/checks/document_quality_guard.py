"""
Check 10: Document Quality Guard.

Reads Team 1 frozen metrics from financial_data.json and evaluates
whether the source data quality is sufficient for reliable financial review.

This is the only Phase 2 module that consumes team1_metrics directly —
it is a consumer, not a re-implementer, of Phase 1 work.

Thresholds:
  extraction_completeness_pct < 80  → CRITICAL gate failure
  extraction_completeness_pct < 90  → HIGH quality concern
  source_page_accuracy_pct    < 90  → REVIEW
  missing_sections            > 0   → REVIEW per section
No LLM. Pure rule-based evaluation.
"""

from typing import Any, Dict, List
from ..loader import get_team1_metrics


COMPLETENESS_CRITICAL = 80.0
COMPLETENESS_HIGH     = 90.0
SOURCE_ACCURACY_REVIEW = 90.0


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    t1 = get_team1_metrics(data)
    if not t1:
        return _skip("team1_metrics not found in financial_data.json")

    dq = t1.get("document_quality", {})
    rag = t1.get("rag", {})

    completeness_pct   = dq.get("extraction_completeness_pct", 0.0)
    data_quality_status = dq.get("data_quality_status", "UNKNOWN")
    missing_sections   = dq.get("missing_sections", [])
    missing_values     = dq.get("missing_values", 0)
    source_accuracy_pct = rag.get("source_page_accuracy_pct", 0.0)

    issues: List[str] = []

    # Gate 1: Extraction completeness
    if completeness_pct < COMPLETENESS_CRITICAL:
        issues.append(
            f"CRITICAL: Extraction completeness {completeness_pct}% is below {COMPLETENESS_CRITICAL}% threshold"
        )
    elif completeness_pct < COMPLETENESS_HIGH:
        issues.append(
            f"HIGH: Extraction completeness {completeness_pct}% is below {COMPLETENESS_HIGH}% threshold"
        )

    # Gate 2: Missing sections
    for sec in missing_sections:
        issues.append(f"REVIEW: Required section missing — {sec}")

    # Gate 3: Source page accuracy
    if source_accuracy_pct < SOURCE_ACCURACY_REVIEW:
        issues.append(
            f"REVIEW: Source/page accuracy {source_accuracy_pct}% below {SOURCE_ACCURACY_REVIEW}%"
        )

    # Determine required_statement_availability
    extraction = t1.get("extraction", {})
    bs_count = extraction.get("balance_sheet_values", {}).get("count", 0)
    is_count = extraction.get("income_statement_values", {}).get("count", 0)
    cf_count = extraction.get("cash_flow_values", {}).get("count", 0)

    if bs_count > 0 and is_count > 0 and cf_count > 0:
        stmt_availability = "ALL_PRESENT"
    elif bs_count > 0 or is_count > 0:
        stmt_availability = "PARTIAL"
    else:
        stmt_availability = "NONE"
        issues.append("CRITICAL: No financial statements could be extracted")

    score  = completeness_pct
    status = "PASSED" if not issues else (
        "CRITICAL" if any("CRITICAL" in i for i in issues) else "REVIEW"
    )

    return {
        "score":  round(score, 1),
        "status": status,
        "extraction_completeness_pct":     completeness_pct,
        "required_statement_availability": stmt_availability,
        "missing_critical_values_count":   missing_values,
        "missing_sections":                missing_sections,
        "source_coverage_pct":             source_accuracy_pct,
        "data_quality_status":             data_quality_status,
        "issues": issues,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {
        "score": 0.0, "status": "SKIPPED", "reason": reason,
        "extraction_completeness_pct": 0.0,
        "required_statement_availability": "UNKNOWN",
    }
