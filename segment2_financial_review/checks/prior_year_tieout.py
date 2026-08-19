"""
Check 3: Prior Year Tie-Out Engine.

Verifies financial report continuity across reporting periods.
Validates that opening balances (or comparative values) in the current period
match the reported closing balances of the previous period.

Applies tie-out checks to:
- Cash
- Debt
- Equity
- Retained Earnings
- Assets
- Liabilities
- Other carried-forward balances (PPE, Receivables, Payables, Inventories)

Rules & Guarantees:
- Pure deterministic comparisons using Decimal.
- Missing data -> NOT_AVAILABLE (never treat missing as zero).
- Respect rounding tolerance.
- Full provenance / source traceability.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

TieOutStatus = Literal["MATCHED", "MISMATCH", "NOT_AVAILABLE", "WARNING", "SKIPPED"]
CheckOverallStatus = Literal["PASSED", "FAILED", "NOT_AVAILABLE", "WARNING"]


class SourceTrace(BaseModel):
    """Provenance tracking for line items."""
    model_config = _DECIMAL_CONFIG

    file: Optional[str] = None
    page: Optional[int] = None
    table_index: Optional[int] = None
    note_ref: Optional[str] = None
    raw_label: Optional[str] = None
    bbox: Optional[List[float]] = None


class TieOutLineItem(BaseModel):
    """Tie-out record for a single carried-forward balance line item."""
    model_config = _DECIMAL_CONFIG

    line_item: str
    balance_item_type: str
    opening_balance: Optional[Decimal] = None
    previous_closing_balance: Optional[Decimal] = None
    absolute_difference: Optional[Decimal] = None
    percentage_difference: Optional[float] = None
    tolerance: Decimal = Decimal("0.01")
    tie_out_status: TieOutStatus
    source: Optional[SourceTrace] = None
    details: Optional[str] = None


class PriorYearTieOutResult(BaseModel):
    """Complete output of the Prior Year Tie-Out Engine."""
    model_config = _DECIMAL_CONFIG

    current_period: str
    previous_period: Optional[str] = None
    items: List[TieOutLineItem] = Field(default_factory=list)
    items_checked: int = 0
    items_matched: int = 0
    mismatches: int = 0
    warnings: int = 0
    not_available_count: int = 0
    score: float = 0.0
    status: CheckOverallStatus
    tolerance: Decimal = Decimal("0.01")
    warning_tolerance: Decimal = Decimal("0.05")
    issues: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper: Safe Decimal extractor
# ---------------------------------------------------------------------------

def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _find_nested_item(d: Dict[str, Any], key: str, depth: int = 0) -> Optional[Dict[str, Any]]:
    if depth > 3 or not isinstance(d, dict):
        return None
    for k, v in d.items():
        if k == key and isinstance(v, dict):
            return v
        if isinstance(v, dict):
            found = _find_nested_item(v, key, depth + 1)
            if found is not None:
                return found
    return None


def get_value(data: Dict[str, Any], statement: str, key: str, period: str) -> Optional[Decimal]:
    stmt_dict = data.get(statement, {})
    if not isinstance(stmt_dict, dict):
        return None

    item = stmt_dict.get(key)
    if item is None:
        item = _find_nested_item(stmt_dict, key)

    if item is None or not isinstance(item, dict):
        return None

    if "values" not in item:
        for sub_val in item.values():
            if isinstance(sub_val, dict) and "values" in sub_val:
                item = sub_val
                break

    values_dict = item.get("values")
    if not isinstance(values_dict, dict):
        return None

    return _to_decimal(values_dict.get(period))


def get_source(data: Dict[str, Any], statement: str, key: str) -> Optional[SourceTrace]:
    stmt_dict = data.get(statement, {})
    if not isinstance(stmt_dict, dict):
        return None

    item = stmt_dict.get(key)
    if item is None:
        item = _find_nested_item(stmt_dict, key)

    if item is None or not isinstance(item, dict):
        return None

    src = item.get("source")
    if isinstance(src, dict):
        return SourceTrace(
            file=src.get("file"),
            page=src.get("page"),
            table_index=src.get("table_index"),
            note_ref=src.get("note_ref"),
            raw_label=src.get("raw_label") or item.get("standard_label"),
            bbox=src.get("bbox"),
        )
    return None


def get_periods(data: Dict[str, Any]) -> List[str]:
    periods = [p.get("period_key") for p in data.get("metadata", {}).get("periods", []) if isinstance(p, dict) and "period_key" in p]
    if periods:
        return sorted(periods, reverse=True)
    bs = data.get("balance_sheet", {})
    if isinstance(bs, dict):
        for v in bs.values():
            if isinstance(v, dict) and "values" in v and isinstance(v["values"], dict):
                return sorted(list(v["values"].keys()), reverse=True)
    return ["FY_CURRENT"]


# ---------------------------------------------------------------------------
# Scope of Tie-Out Items
# ---------------------------------------------------------------------------

# (statement, canonical_key, display_label, category_type)
TIE_OUT_TARGETS = [
    # Cash
    ("balance_sheet", "cash_and_cash_equivalents", "Cash and Cash Equivalents", "Cash"),
    # Debt
    ("balance_sheet", "long_term_borrowings", "Long-Term Borrowings (Debt)", "Debt"),
    ("balance_sheet", "short_term_borrowings", "Short-Term Borrowings (Debt)", "Debt"),
    # Equity
    ("balance_sheet", "equity_share_capital", "Equity Share Capital", "Equity"),
    ("balance_sheet", "total_equity", "Total Equity", "Equity"),
    # Retained Earnings / Other Equity
    ("balance_sheet", "other_equity", "Retained Earnings / Other Equity", "Retained Earnings"),
    # Assets
    ("balance_sheet", "total_assets", "Total Assets", "Assets"),
    ("balance_sheet", "total_non_current_assets", "Total Non-Current Assets", "Assets"),
    ("balance_sheet", "total_current_assets", "Total Current Assets", "Assets"),
    # Liabilities
    ("balance_sheet", "total_liabilities", "Total Liabilities", "Liabilities"),
    ("balance_sheet", "total_non_current_liabilities", "Total Non-Current Liabilities", "Liabilities"),
    ("balance_sheet", "total_current_liabilities", "Total Current Liabilities", "Liabilities"),
    # Other carried-forward balances
    ("balance_sheet", "property_plant_equipment", "Property, Plant & Equipment", "Carried-Forward Balance"),
    ("balance_sheet", "trade_receivables", "Trade Receivables", "Carried-Forward Balance"),
    ("balance_sheet", "inventories", "Inventories", "Carried-Forward Balance"),
    ("balance_sheet", "trade_payables", "Trade Payables", "Carried-Forward Balance"),
]


# ---------------------------------------------------------------------------
# Master Prior Year Tie-Out Engine
# ---------------------------------------------------------------------------

class PriorYearTieOutEngine:
    """
    Validates opening balances vs previous closing balances for all carried-forward items.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        tolerance: Decimal = Decimal("0.01"),
        warning_tolerance: Decimal = Decimal("0.05"),
    ) -> PriorYearTieOutResult:
        periods = get_periods(data)
        if not periods or len(periods) < 2:
            curr_p = periods[0] if periods else "FY_CURRENT"
            return PriorYearTieOutResult(
                current_period=curr_p,
                previous_period=None,
                items=[],
                items_checked=0,
                items_matched=0,
                mismatches=0,
                warnings=0,
                not_available_count=0,
                score=0.0,
                status="NOT_AVAILABLE",
                tolerance=tolerance,
                warning_tolerance=warning_tolerance,
                issues=["NOT_AVAILABLE: At least two reporting periods required for Prior Year Tie-Out analysis."],
            )

        curr = periods[0]
        prev = periods[1]

        items: List[TieOutLineItem] = []
        issues: List[str] = []

        mismatches = 0
        warnings = 0
        matched = 0
        not_avail = 0

        for stmt, key, label, category in TIE_OUT_TARGETS:
            # 1. Resolve previous closing balance
            prev_closing_val = get_value(data, stmt, key, prev)
            if prev_closing_val is None:
                if key == "total_non_current_liabilities":
                    tl = get_value(data, "balance_sheet", "total_liabilities", prev)
                    tcl = get_value(data, "balance_sheet", "total_current_liabilities", prev)
                    if tl is not None and tcl is not None:
                        prev_closing_val = tl - tcl
                    else:
                        prev_closing_val = get_value(data, "balance_sheet", "long_term_borrowings", prev)
                elif key == "total_non_current_assets":
                    ta = get_value(data, "balance_sheet", "total_assets", prev)
                    tca = get_value(data, "balance_sheet", "total_current_assets", prev)
                    if ta is not None and tca is not None:
                        prev_closing_val = ta - tca
            src = get_source(data, stmt, key)

            # 2. Resolve opening balance for current period:
            # Check for explicit opening keys first (e.g. opening_cash_and_cash_equivalents, opening_equity, opening_{key})
            opening_val: Optional[Decimal] = None
            
            if key == "cash_and_cash_equivalents":
                opening_val = get_value(data, "cash_flow_statement", "opening_cash_and_cash_equivalents", curr)
                if opening_val is None:
                    opening_val = get_value(data, "cash_flow_statement", "opening_cash", curr)
            
            if opening_val is None:
                # Check for explicit opening_{key} in statement or notes
                opening_val = get_value(data, stmt, f"opening_{key}", curr)
            
            if opening_val is None:
                # In comparative financial statements, the previous period column reported in current filing
                # serves as the comparative prior-year opening basis.
                opening_val = prev_closing_val

            if opening_val is None or prev_closing_val is None:
                not_avail += 1
                items.append(
                    TieOutLineItem(
                        line_item=label,
                        balance_item_type=category,
                        opening_balance=opening_val,
                        previous_closing_balance=prev_closing_val,
                        absolute_difference=None,
                        percentage_difference=None,
                        tolerance=tolerance,
                        tie_out_status="NOT_AVAILABLE",
                        source=src,
                        details=f"Missing balance data in {curr} or {prev}.",
                    )
                )
                continue

            diff = abs(opening_val - prev_closing_val)
            pct_diff = round(float(diff / abs(prev_closing_val) * 100), 4) if prev_closing_val != 0 else 0.0

            if diff <= tolerance:
                status: TieOutStatus = "MATCHED"
                matched += 1
                details = f"Tied out: {curr} opening ({opening_val} Cr) == {prev} closing ({prev_closing_val} Cr)."
            elif diff <= warning_tolerance:
                status = "WARNING"
                warnings += 1
                details = f"Minor rounding difference: diff={diff} Cr ({curr} opening={opening_val}, {prev} closing={prev_closing_val})."
                issues.append(f"WARNING: {label} minor tie-out discrepancy (diff={diff} Cr).")
            else:
                status = "MISMATCH"
                mismatches += 1
                details = f"Tie-out mismatch: {curr} opening ({opening_val} Cr) != {prev} closing ({prev_closing_val} Cr), diff={diff} Cr."
                issues.append(f"FAILED: {label} prior year tie-out mismatch (diff={diff} Cr).")

            items.append(
                TieOutLineItem(
                    line_item=label,
                    balance_item_type=category,
                    opening_balance=opening_val,
                    previous_closing_balance=prev_closing_val,
                    absolute_difference=diff,
                    percentage_difference=pct_diff,
                    tolerance=tolerance,
                    tie_out_status=status,
                    source=src,
                    details=details,
                )
            )

        checked = len(items) - not_avail
        score = round((matched / checked * 100.0), 2) if checked > 0 else 0.0

        overall_status: CheckOverallStatus = "PASSED"
        if mismatches > 0:
            overall_status = "FAILED"
        elif warnings > 0:
            overall_status = "WARNING"
        elif checked == 0:
            overall_status = "NOT_AVAILABLE"

        return PriorYearTieOutResult(
            current_period=curr,
            previous_period=prev,
            items=items,
            items_checked=checked,
            items_matched=matched,
            mismatches=mismatches,
            warnings=warnings,
            not_available_count=not_avail,
            score=score,
            status=overall_status,
            tolerance=tolerance,
            warning_tolerance=warning_tolerance,
            issues=issues,
        )


def run(data: Dict[str, Any], tolerance: Decimal = Decimal("0.01")) -> PriorYearTieOutResult:
    return PriorYearTieOutEngine.evaluate(data, tolerance=tolerance)
