"""
Check 8: Unusual Gain & Non-Operational Revenue Divergence Detector.

Detects when net profit grows significantly faster than operating revenue —
a common indicator of one-time or non-operational gains inflating the bottom line.

Metrics computed:
  - Revenue growth %  vs  Profit growth %
  - Divergence (pp)  = profit_growth_pct - revenue_growth_pct
  - Other income growth % and ratio to revenue
  - Composition: investment gains, asset disposal gains, one-time gains (from notes)
  - Trigger status: ELEVATED (>8pp) / NORMAL

No LLM. Pure arithmetic.
"""

from typing import Any, Dict, Optional
from ..loader import (
    current_and_previous, get_value, pct_change, get_note_by_topic, safe_div,
)

DIVERGENCE_THRESHOLD_PP = 8.0   # percentage points


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, prev, _ = current_and_previous(data)
    if not curr or not prev:
        return _skip("Need at least two periods")

    rev_curr = get_value(data, "income_statement", "revenue_from_operations", curr)
    rev_prev = get_value(data, "income_statement", "revenue_from_operations", prev)
    pat_curr = get_value(data, "income_statement", "profit_for_the_period",   curr)
    pat_prev = get_value(data, "income_statement", "profit_for_the_period",   prev)
    oi_curr  = get_value(data, "income_statement", "other_income",            curr)
    oi_prev  = get_value(data, "income_statement", "other_income",            prev)

    revenue_growth_pct = pct_change(rev_curr, rev_prev)
    profit_growth_pct  = pct_change(pat_curr, pat_prev)
    oi_growth_pct      = pct_change(oi_curr,  oi_prev)

    divergence_pp: Optional[float] = None
    if revenue_growth_pct is not None and profit_growth_pct is not None:
        divergence_pp = round(profit_growth_pct - revenue_growth_pct, 2)

    oi_to_rev_pct: Optional[float] = None
    if oi_curr is not None and rev_curr is not None and rev_curr != 0:
        oi_to_rev_pct = round(oi_curr / rev_curr * 100, 2)

    # Attempt to decompose other income from notes
    investment_gain   = 0.0
    asset_disposal_gain = 0.0
    one_time_gain     = 0.0
    total_gain_amount = 0.0

    # Heuristic: if other income is explicitly available use it as proxy for gain
    if oi_curr is not None and oi_prev is not None:
        incremental_oi = oi_curr - oi_prev
        if incremental_oi > 0:
            investment_gain   = round(incremental_oi, 2)
            total_gain_amount = round(incremental_oi, 2)

    gain_to_profit_pct: Optional[float] = None
    if pat_curr and pat_curr != 0:
        gain_to_profit_pct = round(total_gain_amount / pat_curr * 100, 2)

    # Trigger determination
    if divergence_pp is not None:
        trigger_status = "ELEVATED" if abs(divergence_pp) > DIVERGENCE_THRESHOLD_PP else "NORMAL"
    else:
        trigger_status = "INSUFFICIENT_DATA"

    score  = 100.0 if trigger_status == "NORMAL" else (70.0 if trigger_status == "ELEVATED" else 0.0)
    status = "PASSED" if trigger_status == "NORMAL" else "REVIEW"

    return {
        "score":  score,
        "status": status,
        "profit_growth_pct":               profit_growth_pct,
        "revenue_growth_pct":              revenue_growth_pct,
        "profit_vs_revenue_divergence_pp": divergence_pp,
        "other_income_growth_pct":         oi_growth_pct,
        "other_income_to_revenue_pct":     oi_to_rev_pct,
        "total_gain_amount":               total_gain_amount,
        "gain_to_profit_pct":             gain_to_profit_pct,
        "investment_gain":                investment_gain,
        "asset_disposal_gain":            asset_disposal_gain,
        "one_time_gain":                  one_time_gain,
        "divergence_trigger_status":      trigger_status,
        "divergence_threshold_pp":        DIVERGENCE_THRESHOLD_PP,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {
        "score": 0.0, "status": "SKIPPED", "reason": reason,
        "divergence_trigger_status": "INSUFFICIENT_DATA",
    }
