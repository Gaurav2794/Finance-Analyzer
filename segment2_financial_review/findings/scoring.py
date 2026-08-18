"""
Scoring Module.

Computes per-category scores and the weighted overall score.

Recommended Category Weights:
    Mathematical Accuracy : 25%
    Cash Flow             : 20%
    Prior-Year Tie-Out    : 15%
    Internal Consistency  : 15%
    Analytical Review     : 10%  (split equally across growth, ratios, unusual fluctuation,
                                   unusual gain — each 2.5%)
    Disclosure Consistency: 10%  (related_disclosure)
    Document Quality      :  5%

Integrity Rule:
    If ANY CRITICAL finding exists => overall_status = "ATTENTION_REQUIRED"
    regardless of the numerical score.

Score Bands:
    95 – 100 : EXCELLENT
    85 –  94 : GOOD
    70 –  84 : ATTENTION_REQUIRED
     < 70    : HIGH_RISK

All arithmetic is performed with Python floats (not Decimal) since scores are
ordinal quality metrics, not monetary figures.
"""

from __future__ import annotations

from typing import Dict, Literal, Optional

OverallStatus = Literal["EXCELLENT", "GOOD", "ATTENTION_REQUIRED", "HIGH_RISK"]

# ---------------------------------------------------------------------------
# Default weights – must sum to 1.0
# ---------------------------------------------------------------------------

DEFAULT_CATEGORY_WEIGHTS: Dict[str, float] = {
    "MATHEMATICAL_ACCURACY":  0.25,
    "CASH_FLOW":              0.20,
    "PRIOR_YEAR_TIEOUT":      0.15,
    "INTERNAL_CONSISTENCY":   0.15,
    "ANALYTICAL_COMPARISON":  0.025,   # sub-component of 10% Analytical Review
    "RATIOS":                 0.025,
    "UNUSUAL_FLUCTUATION":    0.025,
    "UNUSUAL_GAIN":           0.025,
    "RELATED_DISCLOSURE":     0.10,
    "DOCUMENT_QUALITY":       0.05,
}


def compute_overall_score(
    category_scores: Dict[str, Optional[float]],
    has_critical_finding: bool,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """
    Compute the weighted overall score and determine the overall status.

    Parameters
    ----------
    category_scores:
        Dict mapping category name -> score in [0, 100] or None (missing/not evaluated).
        Missing scores are treated as 0 for the weighted sum so they reduce the score
        rather than being silently ignored.
    has_critical_finding:
        If True, overall_status is forced to "ATTENTION_REQUIRED" irrespective of score.
    weights:
        Optional override mapping.  Must cover all expected categories.
        Unrecognised keys are ignored.

    Returns
    -------
    {
        "overall_score":       float,      # 0–100, 2 d.p.
        "overall_status":      str,        # OverallStatus literal
        "category_scores":     dict,       # passed-through for reference
        "weighted_components": dict,       # per-category weighted contribution
        "integrity_override":  bool,       # True if critical finding forced status
    }
    """
    active_weights = dict(DEFAULT_CATEGORY_WEIGHTS)
    if weights:
        active_weights.update(weights)

    weighted_sum = 0.0
    total_weight = 0.0
    components: Dict[str, float] = {}

    for category, weight in active_weights.items():
        raw_score = category_scores.get(category)
        effective_score = float(raw_score) if raw_score is not None else 0.0
        effective_score = max(0.0, min(100.0, effective_score))
        contribution = weight * effective_score
        weighted_sum += contribution
        total_weight += weight
        components[category] = round(contribution, 4)

    # Normalise in case weights don't perfectly sum to 1.0
    overall_score: float = round((weighted_sum / total_weight) * 100.0 / 100.0, 2) if total_weight else 0.0
    overall_score = max(0.0, min(100.0, round(weighted_sum, 2)))

    # Determine band
    if has_critical_finding:
        status: OverallStatus = "ATTENTION_REQUIRED"
        integrity_override = True
    elif overall_score >= 95.0:
        status = "EXCELLENT"
        integrity_override = False
    elif overall_score >= 85.0:
        status = "GOOD"
        integrity_override = False
    elif overall_score >= 70.0:
        status = "ATTENTION_REQUIRED"
        integrity_override = False
    else:
        status = "HIGH_RISK"
        integrity_override = False

    return {
        "overall_score":       overall_score,
        "overall_status":      status,
        "category_scores":     category_scores,
        "weighted_components": components,
        "integrity_override":  integrity_override,
    }
