"""
Phase 2 Financial Data Loader.

Reads financial_data.json produced by Phase 1 (Segment 1).
Provides safe field accessors and period resolution helpers.

RULES:
- NEVER modifies input data.
- All accessors return None (not raise) when a field is absent.
- All derivations are clearly labelled so callers know what is real vs computed.
"""

import json
from typing import Any, Dict, List, Optional, Tuple


# Rounding tolerance in Crores for equality checks in math verification.
TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load(path: str) -> Dict[str, Any]:
    """Load financial_data.json from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Period resolution
# ---------------------------------------------------------------------------

def get_periods(data: Dict[str, Any]) -> List[str]:
    """Return period keys sorted descending (most recent first)."""
    periods = [p["period_key"] for p in data.get("metadata", {}).get("periods", [])]
    return sorted(periods, reverse=True)


def current_and_previous(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (current_period, previous_period, base_period) or None for absent ones."""
    periods = get_periods(data)
    current  = periods[0] if len(periods) > 0 else None
    previous = periods[1] if len(periods) > 1 else None
    base     = periods[2] if len(periods) > 2 else None
    return current, previous, base


# ---------------------------------------------------------------------------
# Core value accessor
# ---------------------------------------------------------------------------

def get_value(
    data: Dict[str, Any],
    statement: str,
    key: str,
    period: str,
    default: Optional[float] = None,
) -> Optional[float]:
    """
    Safely retrieve a numeric value from a statement line item.

    Handles two income_statement layouts:
      - FLAT   (real output): income_statement.finance_costs.values
      - NESTED (sample)     : income_statement.expenses.finance_costs.values

    Args:
        statement : 'balance_sheet' | 'income_statement' | 'cash_flow_statement'
        key       : canonical snake_case key, e.g. 'trade_receivables'
        period    : e.g. 'FY2024'
        default   : returned when field is absent (never raises)
    """
    stmt_dict = data.get(statement, {})

    # 1. Try flat key at top level
    item = stmt_dict.get(key)

    # 2. If absent, walk one level of nesting (sample data: expenses.*, tax_expense.*)
    if item is None:
        for sub_val in stmt_dict.values():
            if isinstance(sub_val, dict) and "values" not in sub_val:
                candidate = sub_val.get(key)
                if candidate is not None and isinstance(candidate, dict):
                    item = candidate
                    break

    if item is None:
        return default

    # 3. Handle objects whose first child carries 'values'
    if "values" not in item and isinstance(item, dict):
        for sub in item.values():
            if isinstance(sub, dict) and "values" in sub:
                item = sub
                break

    val = item.get("values", {}).get(period)
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default



def get_source(data: Dict[str, Any], statement: str, key: str) -> Optional[Dict[str, Any]]:
    """Return the source provenance dict for a line item, or None."""
    item = data.get(statement, {}).get(key)
    if item is None:
        return None
    return item.get("source")


# ---------------------------------------------------------------------------
# Derived field helpers (Phase 2 internal — never written back to JSON)
# ---------------------------------------------------------------------------

def derive_total_liabilities(data: Dict[str, Any], period: str) -> Optional[float]:
    """
    total_liabilities = total_assets - total_equity
    Uses explicit key if present; falls back to derivation.
    """
    val = get_value(data, "balance_sheet", "total_liabilities", period)
    if val is not None:
        return val
    assets = get_value(data, "balance_sheet", "total_assets", period)
    equity = get_value(data, "balance_sheet", "total_equity", period)
    if assets is not None and equity is not None:
        return round(assets - equity, 4)
    return None


def derive_gross_profit(data: Dict[str, Any], period: str) -> Optional[float]:
    """
    gross_profit = revenue_from_operations - cost_of_materials_consumed
    Uses explicit key if present; falls back to derivation.
    """
    val = get_value(data, "income_statement", "gross_profit", period)
    if val is not None:
        return val
    rev  = get_value(data, "income_statement", "revenue_from_operations", period)
    cogs = get_value(data, "income_statement", "cost_of_materials_consumed", period)
    if rev is not None and cogs is not None:
        return round(rev - cogs, 4)
    return None


def derive_opening_cash(
    data: Dict[str, Any],
    current_period: str,
    previous_period: Optional[str],
) -> Optional[float]:
    """
    Opening cash for current_period.
    Priority: explicit CFS key → BS cash of previous period → CFS closing of previous period.
    """
    val = get_value(data, "cash_flow_statement", "opening_cash_and_cash_equivalents", current_period)
    if val is not None:
        return val
    if previous_period:
        val = get_value(data, "balance_sheet", "cash_and_cash_equivalents", previous_period)
        if val is not None:
            return val
        val = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", previous_period)
        if val is not None:
            return val
    return None


def get_total_debt(data: Dict[str, Any], period: str) -> float:
    """Long-term borrowings + short-term borrowings."""
    lt = get_value(data, "balance_sheet", "long_term_borrowings",  period) or 0.0
    st = get_value(data, "balance_sheet", "short_term_borrowings", period) or 0.0
    return round(lt + st, 4)


# ---------------------------------------------------------------------------
# Notes / disclosure helpers
# ---------------------------------------------------------------------------

def get_note_by_topic(data: Dict[str, Any], topic_keyword: str) -> Optional[Dict[str, Any]]:
    """Find the first note whose topic contains the keyword (case-insensitive)."""
    for note in data.get("extracted_notes_and_disclosures", []):
        if topic_keyword.lower() in note.get("topic", "").lower():
            return note
    return None


def get_all_notes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return data.get("extracted_notes_and_disclosures", [])


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def get_company_info(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("metadata", {}).get("company", {})


def get_team1_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    return data.get("team1_metrics", {})


# ---------------------------------------------------------------------------
# Arithmetic utility
# ---------------------------------------------------------------------------

def pct_change(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Safe YoY percentage change. Returns None on missing inputs or zero base."""
    if current is None or previous is None:
        return None
    if previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 2)


def safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safe division. Returns None instead of ZeroDivisionError."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator, 4)
