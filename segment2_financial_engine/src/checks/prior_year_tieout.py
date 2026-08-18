"""
Check 3: Prior Year Tie-Out.

Verifies that opening balances of the current period match closing balances
of the previous period for key continuity line items across all three statements.

"Tie-out" is a standard audit procedure confirming financial report continuity.
No LLM. Pure comparison with TOLERANCE.
"""

from typing import Any, Dict, List
from ..loader import TOLERANCE, current_and_previous, get_value


# Key items to tie out: (statement, canonical_key, display_label)
TIE_OUT_ITEMS: List[tuple] = [
    ("balance_sheet",     "cash_and_cash_equivalents",    "Cash and Cash Equivalents"),
    ("balance_sheet",     "equity_share_capital",          "Share Capital"),
    ("balance_sheet",     "total_equity",                  "Total Equity"),
    ("balance_sheet",     "total_non_current_assets",      "Total Non-Current Assets"),
    ("balance_sheet",     "total_assets",                  "Total Assets"),
    ("balance_sheet",     "total_liabilities",             "Total Liabilities"),
    ("balance_sheet",     "long_term_borrowings",          "Long-Term Borrowings"),
    ("balance_sheet",     "trade_receivables",             "Trade Receivables"),
]


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, prev, _ = current_and_previous(data)
    if not curr or not prev:
        return _skip("Need at least two periods for prior year tie-out")

    items: List[Dict[str, Any]] = []
    mismatches = 0

    for stmt, key, label in TIE_OUT_ITEMS:
        opening_curr = get_value(data, stmt, key, curr)  # opening of current period
        closing_prev = get_value(data, stmt, key, prev)  # closing of previous period

        if opening_curr is None or closing_prev is None:
            items.append({
                "line_item": label,
                "opening_balance_current": opening_curr,
                "reported_closing_previous": closing_prev,
                "difference": None,
                "tie_out_status": "SKIPPED",
            })
            continue

        diff   = round(abs(opening_curr - closing_prev), 4)
        status = "MATCHED" if diff <= TOLERANCE else "MISMATCH"
        if status == "MISMATCH":
            mismatches += 1

        items.append({
            "line_item": label,
            f"opening_balance_{curr.lower()}": opening_curr,
            f"reported_closing_{prev.lower()}": closing_prev,
            "difference": diff,
            "tie_out_status": status,
        })

    checked  = sum(1 for i in items if i["tie_out_status"] != "SKIPPED")
    passed   = checked - mismatches
    score    = round((passed / checked * 100) if checked > 0 else 0.0, 1)
    status   = "PASSED" if mismatches == 0 else "FAILED"

    return {
        "score": score,
        "status": status,
        "items_checked": checked,
        "mismatches": mismatches,
        "items": items,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {"score": 0.0, "status": "SKIPPED", "reason": reason, "items": []}
