"""
Weighted Scorer.

Computes the overall review score (0-100) from the 10 individual check scores
using the weights defined in the architecture plan.

Checks that are SKIPPED are excluded from the denominator so they don't
unfairly penalise documents with limited data (e.g. no disclosure notes).
"""

from typing import Any, Dict, Optional

# (check_key_in_result, weight)
WEIGHTS: Dict[str, float] = {
    "mathematical_accuracy":    0.20,
    "cash_flow_reconciliation": 0.15,
    "prior_year_tieout":        0.10,
    "internal_consistency":     0.10,
    "analytical_metrics":       0.10,
    "financial_ratios":         0.10,
    "unusual_fluctuations":     0.10,
    "unusual_gain_analysis":    0.05,
    "related_disclosure":       0.05,
    "document_quality":         0.05,
}


def compute(check_results: Dict[str, Any]) -> float:
    """
    Returns a weighted overall score 0-100.
    SKIPPED checks are excluded from the weighted average.
    """
    weighted_sum  = 0.0
    active_weight = 0.0

    for key, weight in WEIGHTS.items():
        result = check_results.get(key, {})
        status = result.get("status", "SKIPPED")
        score  = result.get("score")

        if status == "SKIPPED" or score is None:
            continue  # exclude from denominator

        weighted_sum  += score * weight
        active_weight += weight

    if active_weight == 0:
        return 0.0

    raw = weighted_sum / active_weight
    return round(raw, 1)
