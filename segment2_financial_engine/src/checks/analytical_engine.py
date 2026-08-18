"""
Check 5: Analytical Comparison & Year-Over-Year Growth Engine.

Computes YoY % growth for all major financial KPIs.
Also flags unusual fluctuations inline (>30% = HIGH, 20-30% = REVIEW).
Requires at least two periods; gracefully skips with one.
No LLM. Pure arithmetic.
"""

from typing import Any, Dict, List, Optional
from ..loader import current_and_previous, get_value, pct_change, derive_gross_profit


# (display_label, statement, canonical_key)
GROWTH_ITEMS: List[tuple] = [
    ("Revenue",         "income_statement",  "revenue_from_operations"),
    ("COGS",            "income_statement",  "cost_of_materials_consumed"),
    ("Total Expenses",  "income_statement",  "total_expenses"),
    ("Gross Profit",    "income_statement",  "gross_profit"),          # may be absent
    ("Operating Profit","income_statement",  "operating_profit"),
    ("Net Profit (PAT)","income_statement",  "profit_for_the_period"),
    ("Other Income",    "income_statement",  "other_income"),
    ("Total Assets",    "balance_sheet",     "total_assets"),
    ("Total Liabilities","balance_sheet",    "total_liabilities"),     # may be absent
    ("Total Equity",    "balance_sheet",     "total_equity"),
    ("Cash & Equivalents","balance_sheet",   "cash_and_cash_equivalents"),
    ("Trade Receivables","balance_sheet",    "trade_receivables"),
    ("Inventories",     "balance_sheet",     "inventories"),
    ("Long-Term Debt",  "balance_sheet",     "long_term_borrowings"),
    ("CFO",             "cash_flow_statement","net_cash_from_operating_activities"),
]

# key name mapping (display → snake for output key)
_DISPLAY_TO_KEY = {
    "Revenue":             "revenue_growth_pct",
    "COGS":                "cogs_growth_pct",
    "Total Expenses":      "expense_growth_pct",
    "Gross Profit":        "gross_profit_growth_pct",
    "Operating Profit":    "operating_profit_growth_pct",
    "Net Profit (PAT)":    "net_profit_growth_pct",
    "Other Income":        "other_income_growth_pct",
    "Total Assets":        "asset_growth_pct",
    "Total Liabilities":   "liability_growth_pct",
    "Total Equity":        "equity_growth_pct",
    "Cash & Equivalents":  "cash_growth_pct",
    "Trade Receivables":   "receivables_growth_pct",
    "Inventories":         "inventory_growth_pct",
    "Long-Term Debt":      "debt_growth_pct",
    "CFO":                 "cfo_growth_pct",
}

HIGH_THRESHOLD   = 30.0   # % absolute change → HIGH severity
REVIEW_THRESHOLD = 20.0   # % absolute change → REVIEW severity


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, prev, _ = current_and_previous(data)
    if not curr or not prev:
        return _skip("Need at least two periods for YoY analysis")

    growth_rates:        Dict[str, Optional[float]] = {}
    unusual_fluctuations: List[Dict[str, Any]]       = []

    for label, stmt, key in GROWTH_ITEMS:
        curr_val = get_value(data, stmt, key, curr)
        prev_val = get_value(data, stmt, key, prev)

        # Fallback for derived fields
        if curr_val is None and label == "Gross Profit":
            curr_val = derive_gross_profit(data, curr)
            prev_val = derive_gross_profit(data, prev)

        pct = pct_change(curr_val, prev_val)
        out_key = _DISPLAY_TO_KEY.get(label, label.lower().replace(" ", "_") + "_pct")
        growth_rates[out_key] = pct

        # Fluctuation flagging
        if pct is not None and curr_val is not None and prev_val is not None:
            abs_pct    = abs(pct)
            direction  = "INCREASE" if pct > 0 else "DECREASE"
            if abs_pct > HIGH_THRESHOLD:
                severity = "HIGH"
            elif abs_pct > REVIEW_THRESHOLD:
                severity = "REVIEW"
            else:
                severity = "PASSED"

            if severity in ("HIGH", "REVIEW"):
                unusual_fluctuations.append({
                    "metric":         label,
                    "current_value":  curr_val,
                    "previous_value": prev_val,
                    "change_pct":     pct,
                    "threshold_pct":  HIGH_THRESHOLD if severity == "HIGH" else REVIEW_THRESHOLD,
                    "severity":       severity,
                    "direction":      direction,
                })

    computed = sum(1 for v in growth_rates.values() if v is not None)
    score    = round((computed / len(growth_rates) * 100) if growth_rates else 0.0, 1)

    return {
        "score":                score,
        "status":               "PASSED",
        "periods_analyzed":     [curr, prev],
        "growth_rates":         growth_rates,
        "unusual_fluctuations": unusual_fluctuations,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {
        "score": 0.0, "status": "SKIPPED", "reason": reason,
        "growth_rates": {}, "unusual_fluctuations": [],
    }
