"""
Severity Classification Module.

Maps check outcomes from every Team-2 engine to standardised finding severities.

Severity Levels (most to least serious):
    CRITICAL  - integrity failures that invalidate the report
    HIGH      - material quantitative errors requiring immediate attention
    REVIEW    - moderate anomalies worth investigating
    PASSED    - check completed cleanly without issue

Rules:
    - Deterministic and reproducible.
    - No LLM involvement.
    - Config-driven: callers may override the default classification map.
    - Every classification decision is logged with a human-readable rationale.
"""

from __future__ import annotations
from typing import Dict, Literal, Optional, Tuple

FindingSeverity = Literal["CRITICAL", "HIGH", "REVIEW", "PASSED"]
FindingCategory = Literal[
    "MATHEMATICAL_ACCURACY",
    "CASH_FLOW",
    "PRIOR_YEAR_TIEOUT",
    "INTERNAL_CONSISTENCY",
    "ANALYTICAL_COMPARISON",
    "RATIOS",
    "UNUSUAL_FLUCTUATION",
    "UNUSUAL_GAIN",
    "RELATED_DISCLOSURE",
    "DOCUMENT_QUALITY",
]

# (category, trigger_condition) -> severity
DEFAULT_SEVERITY_MAP: Dict[Tuple[str, str], FindingSeverity] = {
    # Mathematical Accuracy
    ("MATHEMATICAL_ACCURACY", "FAILED"):            "CRITICAL",
    ("MATHEMATICAL_ACCURACY", "WARNING"):           "HIGH",
    ("MATHEMATICAL_ACCURACY", "NOT_AVAILABLE"):     "REVIEW",
    ("MATHEMATICAL_ACCURACY", "PASSED"):            "PASSED",

    # Cash Flow
    ("CASH_FLOW", "MISMATCH"):                      "CRITICAL",
    ("CASH_FLOW", "FAILED"):                        "CRITICAL",
    ("CASH_FLOW", "WARNING"):                       "HIGH",
    ("CASH_FLOW", "NOT_AVAILABLE"):                 "REVIEW",
    ("CASH_FLOW", "PASSED"):                        "PASSED",
    ("CASH_FLOW", "RECONCILED"):                    "PASSED",

    # Prior-Year Tie-Out
    ("PRIOR_YEAR_TIEOUT", "FAILED"):                "HIGH",
    ("PRIOR_YEAR_TIEOUT", "WARNING"):               "REVIEW",
    ("PRIOR_YEAR_TIEOUT", "NOT_AVAILABLE"):         "REVIEW",
    ("PRIOR_YEAR_TIEOUT", "PASSED"):                "PASSED",

    # Internal Consistency
    ("INTERNAL_CONSISTENCY", "FAILED"):             "CRITICAL",
    ("INTERNAL_CONSISTENCY", "WARNING"):            "HIGH",
    ("INTERNAL_CONSISTENCY", "NOT_AVAILABLE"):      "REVIEW",
    ("INTERNAL_CONSISTENCY", "PASSED"):             "PASSED",

    # Analytical Comparison (YoY Growth)
    ("ANALYTICAL_COMPARISON", "WARNING"):           "REVIEW",
    ("ANALYTICAL_COMPARISON", "NOT_AVAILABLE"):     "REVIEW",
    ("ANALYTICAL_COMPARISON", "PASSED"):            "PASSED",

    # Ratios
    ("RATIOS", "WARNING"):                          "REVIEW",
    ("RATIOS", "NOT_AVAILABLE"):                    "REVIEW",
    ("RATIOS", "PASSED"):                           "PASSED",

    # Unusual Fluctuation — per-item severity already computed
    ("UNUSUAL_FLUCTUATION", "HIGH"):                "HIGH",
    ("UNUSUAL_FLUCTUATION", "REVIEW"):              "REVIEW",
    ("UNUSUAL_FLUCTUATION", "WARNING"):             "REVIEW",
    ("UNUSUAL_FLUCTUATION", "NOT_AVAILABLE"):       "REVIEW",
    ("UNUSUAL_FLUCTUATION", "PASSED"):              "PASSED",

    # Unusual Gain
    ("UNUSUAL_GAIN", "ELEVATED"):                   "REVIEW",
    ("UNUSUAL_GAIN", "WARNING"):                    "REVIEW",
    ("UNUSUAL_GAIN", "NOT_AVAILABLE"):              "REVIEW",
    ("UNUSUAL_GAIN", "NORMAL"):                     "PASSED",
    ("UNUSUAL_GAIN", "PASSED"):                     "PASSED",

    # Related Disclosure
    ("RELATED_DISCLOSURE", "WARNING"):              "HIGH",
    ("RELATED_DISCLOSURE", "NOT_AVAILABLE"):        "REVIEW",
    ("RELATED_DISCLOSURE", "PASSED"):               "PASSED",

    # Document Quality
    ("DOCUMENT_QUALITY", "FAILED"):                 "CRITICAL",
    ("DOCUMENT_QUALITY", "WARNING"):                "HIGH",
    ("DOCUMENT_QUALITY", "NOT_AVAILABLE"):          "REVIEW",
    ("DOCUMENT_QUALITY", "PASSED"):                 "PASSED",
}

RECOMMENDED_ACTIONS: Dict[FindingSeverity, str] = {
    "CRITICAL": (
        "Immediately escalate to senior reviewer. Do not proceed with credit or "
        "investment decision until this discrepancy is resolved. Request auditor confirmation."
    ),
    "HIGH": (
        "Obtain clarification from management or auditor. Cross-verify against source "
        "document before forming a view. Flag in the review memo."
    ),
    "REVIEW": (
        "Investigate for context. May be explainable by one-off events, reclassification, "
        "or accounting policy change. Document rationale if accepted."
    ),
    "PASSED": "No further action required for this check.",
}


def classify(
    category: str,
    trigger: str,
    severity_map: Optional[Dict[Tuple[str, str], FindingSeverity]] = None,
) -> Tuple[FindingSeverity, str]:
    """
    Return (severity, recommended_action) for a (category, trigger) pair.

    Falls back to REVIEW for unmapped combinations so no finding is silently dropped.
    """
    active_map: Dict[Tuple[str, str], FindingSeverity] = dict(DEFAULT_SEVERITY_MAP)
    if severity_map:
        active_map.update(severity_map)

    severity = active_map.get((category, trigger))
    if severity is None:
        severity = "REVIEW"  # conservative fallback

    return severity, RECOMMENDED_ACTIONS[severity]
