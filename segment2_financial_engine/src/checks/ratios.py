"""
Check 6: Financial Ratios Suite.

Computes all four ratio groups for the current reporting period:
  - Liquidity  : Current Ratio, Quick Ratio, Cash Ratio
  - Leverage   : Debt-to-Equity, Debt Ratio, Interest Coverage
  - Profitability: Gross Margin, Operating Margin, Net Margin, ROA, ROE
  - Efficiency : Asset Turnover, Receivables Turnover, DSO, Inventory Turnover

Each ratio uses safe_div — returns None instead of crashing on zero denominators.
No LLM. Pure arithmetic.
"""

from typing import Any, Dict, Optional
from ..loader import (
    current_and_previous, derive_gross_profit,
    get_total_debt, get_value, safe_div,
)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, _, _ = current_and_previous(data)
    if not curr:
        return _skip("No periods found in metadata")

    # ── Balance Sheet fields ──────────────────────────────────────────
    tca   = get_value(data, "balance_sheet", "total_current_assets",      curr)
    tcl   = get_value(data, "balance_sheet", "total_current_liabilities",  curr)
    cash  = get_value(data, "balance_sheet", "cash_and_cash_equivalents",  curr)
    ci    = get_value(data, "balance_sheet", "current_investments",        curr) or 0.0
    inv   = get_value(data, "balance_sheet", "inventories",                curr)
    tr    = get_value(data, "balance_sheet", "trade_receivables",          curr)
    ta    = get_value(data, "balance_sheet", "total_assets",               curr)
    te    = get_value(data, "balance_sheet", "total_equity",               curr)
    debt  = get_total_debt(data, curr)

    # ── Income Statement fields ───────────────────────────────────────
    rev   = get_value(data, "income_statement", "revenue_from_operations",    curr)
    cogs  = get_value(data, "income_statement", "cost_of_materials_consumed", curr)
    op    = get_value(data, "income_statement", "operating_profit",            curr)
    pat   = get_value(data, "income_statement", "profit_for_the_period",       curr)
    fin   = get_value(data, "income_statement", "finance_costs",               curr)
    gp    = derive_gross_profit(data, curr)

    # ── LIQUIDITY ─────────────────────────────────────────────────────
    current_ratio = safe_div(tca, tcl)
    quick_ratio   = safe_div((tca - inv) if tca is not None and inv is not None else None, tcl)
    cash_ratio    = safe_div((cash + ci) if cash is not None else None, tcl)

    # ── LEVERAGE ──────────────────────────────────────────────────────
    debt_to_equity         = safe_div(debt, te)
    debt_ratio             = safe_div(debt, ta)
    interest_coverage_ratio = safe_div(op, fin)

    # ── PROFITABILITY ─────────────────────────────────────────────────
    def _pct(num: Optional[float], den: Optional[float]) -> Optional[float]:
        val = safe_div(num, den)
        return round(val * 100, 2) if val is not None else None

    gross_profit_margin_pct  = _pct(gp,  rev)
    operating_margin_pct     = _pct(op,  rev)
    net_profit_margin_pct    = _pct(pat, rev)
    return_on_assets_pct     = _pct(pat, ta)
    return_on_equity_pct     = _pct(pat, te)

    # ── EFFICIENCY ────────────────────────────────────────────────────
    asset_turnover_ratio       = safe_div(rev, ta)
    receivables_turnover_ratio = safe_div(rev, tr)
    days_sales_outstanding     = safe_div(365.0, receivables_turnover_ratio) if receivables_turnover_ratio else None
    if days_sales_outstanding:
        days_sales_outstanding = round(days_sales_outstanding, 2)
    inventory_turnover_ratio   = safe_div(cogs, inv)

    # ── Round ratios to 2 dp ──────────────────────────────────────────
    def r2(v: Optional[float]) -> Optional[float]:
        return round(v, 2) if v is not None else None

    computed = sum(1 for v in [
        current_ratio, quick_ratio, cash_ratio,
        debt_to_equity, debt_ratio, interest_coverage_ratio,
        gross_profit_margin_pct, operating_margin_pct, net_profit_margin_pct,
        return_on_assets_pct, return_on_equity_pct,
        asset_turnover_ratio, receivables_turnover_ratio,
        days_sales_outstanding, inventory_turnover_ratio,
    ] if v is not None)

    score = round(computed / 15 * 100, 1)

    return {
        "score":  score,
        "status": "PASSED",
        "period": curr,
        "liquidity": {
            "current_ratio": r2(current_ratio),
            "quick_ratio":   r2(quick_ratio),
            "cash_ratio":    r2(cash_ratio),
        },
        "leverage": {
            "debt_to_equity":          r2(debt_to_equity),
            "debt_ratio":              r2(debt_ratio),
            "interest_coverage_ratio": r2(interest_coverage_ratio),
        },
        "profitability": {
            "gross_profit_margin_pct":  gross_profit_margin_pct,
            "operating_margin_pct":     operating_margin_pct,
            "net_profit_margin_pct":    net_profit_margin_pct,
            "return_on_assets_pct":     return_on_assets_pct,
            "return_on_equity_pct":     return_on_equity_pct,
        },
        "efficiency": {
            "asset_turnover_ratio":       r2(asset_turnover_ratio),
            "receivables_turnover_ratio": r2(receivables_turnover_ratio),
            "days_sales_outstanding":     days_sales_outstanding,
            "inventory_turnover_ratio":   r2(inventory_turnover_ratio),
        },
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {
        "score": 0.0, "status": "SKIPPED", "reason": reason,
        "liquidity": {}, "leverage": {}, "profitability": {}, "efficiency": {},
    }
