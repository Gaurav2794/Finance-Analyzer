"""
Check 7: Unusual Fluctuation & Severity Classifier.

Scans all major line items for YoY absolute % changes that breach thresholds:
  > 30%  → HIGH
  20-30% → REVIEW
  ≤ 20%  → PASSED

This is a standalone, exhaustive sweep (broader than the inline flags in
analytical_engine.py) covering all three statement sections.
Requires at least two periods.
No LLM. Pure arithmetic.
"""

from typing import Any, Dict, List, Optional
from ..loader import current_and_previous, get_value, pct_change


HIGH_THRESHOLD   = 30.0
REVIEW_THRESHOLD = 20.0

# (display_label, statement, key, note for context)
SCAN_ITEMS: List[tuple] = [
    # Income Statement
    ("Revenue from Operations",     "income_statement",   "revenue_from_operations",           ""),
    ("Other Income",                "income_statement",   "other_income",                      "Non-operational income"),
    ("Total Income",                "income_statement",   "total_income",                      ""),
    ("COGS / Materials",            "income_statement",   "cost_of_materials_consumed",         ""),
    ("Employee Benefit Expenses",   "income_statement",   "employee_benefit_expenses",          ""),
    ("Finance Costs",               "income_statement",   "finance_costs",                     "Interest & borrowing charges"),
    ("Depreciation & Amortization", "income_statement",   "depreciation_and_amortization",      ""),
    ("Other Operating Expenses",    "income_statement",   "other_operating_expenses",           ""),
    ("Total Expenses",              "income_statement",   "total_expenses",                    ""),
    ("Operating Profit",            "income_statement",   "operating_profit",                  ""),
    ("Profit Before Tax",           "income_statement",   "profit_before_tax",                 ""),
    ("Tax Expense",                 "income_statement",   "total_tax_expense",                 ""),
    ("Net Profit (PAT)",            "income_statement",   "profit_for_the_period",             ""),
    # Balance Sheet — Assets
    ("Trade Receivables",           "balance_sheet",      "trade_receivables",                 ""),
    ("Inventories",                 "balance_sheet",      "inventories",                       ""),
    ("Cash & Equivalents",          "balance_sheet",      "cash_and_cash_equivalents",         ""),
    ("Current Investments",         "balance_sheet",      "current_investments",               ""),
    ("Total Current Assets",        "balance_sheet",      "total_current_assets",              ""),
    ("Total Non-Current Assets",    "balance_sheet",      "total_non_current_assets",          ""),
    ("Total Assets",                "balance_sheet",      "total_assets",                      ""),
    # Balance Sheet — Liabilities & Equity
    ("Long-Term Borrowings",        "balance_sheet",      "long_term_borrowings",              "Debt trend"),
    ("Short-Term Borrowings",       "balance_sheet",      "short_term_borrowings",             ""),
    ("Trade Payables",              "balance_sheet",      "trade_payables",                    ""),
    ("Other Current Liabilities",   "balance_sheet",      "other_current_liabilities",         "Unearned / advance billing"),
    ("Total Current Liabilities",   "balance_sheet",      "total_current_liabilities",         ""),
    ("Total Equity",                "balance_sheet",      "total_equity",                      ""),
    # Cash Flow
    ("CFO",                         "cash_flow_statement","net_cash_from_operating_activities", ""),
    ("CFI",                         "cash_flow_statement","net_cash_from_investing_activities", ""),
    ("CFF",                         "cash_flow_statement","net_cash_from_financing_activities", ""),
]


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, prev, _ = current_and_previous(data)
    if not curr or not prev:
        return _skip("Need at least two periods for fluctuation analysis")

    results: List[Dict[str, Any]] = []
    high_count   = 0
    review_count = 0

    for label, stmt, key, note in SCAN_ITEMS:
        curr_val: Optional[float] = get_value(data, stmt, key, curr)
        prev_val: Optional[float] = get_value(data, stmt, key, prev)

        if curr_val is None or prev_val is None:
            continue

        pct = pct_change(curr_val, prev_val)
        if pct is None:
            continue

        abs_pct   = abs(pct)
        direction = "INCREASE" if pct >= 0 else "DECREASE"

        if abs_pct > HIGH_THRESHOLD:
            severity    = "HIGH"
            threshold   = HIGH_THRESHOLD
            high_count += 1
        elif abs_pct > REVIEW_THRESHOLD:
            severity     = "REVIEW"
            threshold    = REVIEW_THRESHOLD
            review_count += 1
        else:
            severity  = "PASSED"
            threshold = REVIEW_THRESHOLD

        entry: Dict[str, Any] = {
            "metric":         label,
            "current_value":  curr_val,
            "previous_value": prev_val,
            "change_pct":     pct,
            "threshold_pct":  threshold,
            "severity":       severity,
            "direction":      direction,
        }
        if note:
            entry["note"] = note
        results.append(entry)

    total_flagged = high_count + review_count
    score = max(0.0, round(100.0 - (high_count * 10) - (review_count * 3), 1))
    status = "PASSED" if high_count == 0 else "REVIEW_REQUIRED"

    return {
        "score":                 score,
        "status":                status,
        "total_items_scanned":   len(results),
        "high_severity_count":   high_count,
        "review_severity_count": review_count,
        "flagged_count":         total_flagged,
        "items":                 results,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {"score": 0.0, "status": "SKIPPED", "reason": reason, "items": []}
