"""
Analytical Comparison & YoY Growth Engine.

Calculates Year-over-Year (YoY) growth for all major financial KPIs:
- Revenue
- COGS
- Operating Expenses
- Gross Profit
- Operating Profit
- Net Profit
- Assets
- Liabilities
- Equity
- Cash
- Debt

Formulas:
  Absolute Change = Current - Previous
  Percentage Change = (Current - Previous) / ABS(Previous) * 100

Directions:
  INCREASE, DECREASE, NO_CHANGE, NOT_AVAILABLE

Rules:
- Pure deterministic calculations using Decimal.
- Safe handling of zero and missing previous values.
- Never assumes missing is zero.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

Direction = Literal["INCREASE", "DECREASE", "NO_CHANGE", "NOT_AVAILABLE"]
GrowthStatus = Literal["COMPUTED", "NOT_AVAILABLE", "ZERO_BASE"]


class SourceTrace(BaseModel):
    """Provenance tracking for line items."""
    model_config = _DECIMAL_CONFIG

    file: Optional[str] = None
    page: Optional[int] = None
    table_index: Optional[int] = None
    note_ref: Optional[str] = None
    raw_label: Optional[str] = None
    bbox: Optional[List[float]] = None


class MetricGrowthDetail(BaseModel):
    """YoY growth record for a single financial metric."""
    model_config = _DECIMAL_CONFIG

    metric_name: str
    canonical_key: str
    current_value: Optional[Decimal] = None
    previous_value: Optional[Decimal] = None
    absolute_change: Optional[Decimal] = None
    percentage_change: Optional[float] = None
    direction: Direction
    status: GrowthStatus
    source: Optional[SourceTrace] = None
    details: Optional[str] = None


class AnalyticalComparisonResult(BaseModel):
    """Master output of the Analytical Comparison Engine."""
    model_config = _DECIMAL_CONFIG

    current_period: str
    previous_period: Optional[str] = None
    metrics: Dict[str, MetricGrowthDetail] = Field(default_factory=dict)
    growth_rates: Dict[str, Optional[float]] = Field(default_factory=dict)
    total_metrics_evaluated: int = 0
    metrics_computed: int = 0
    status: Literal["COMPUTED", "PARTIAL", "NOT_AVAILABLE"]


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
# Metric Value Resolvers (handling canonical aliases & derivations)
# ---------------------------------------------------------------------------

def _resolve_metric(data: Dict[str, Any], canonical_key: str, period: str) -> Tuple[Optional[Decimal], Optional[SourceTrace]]:
    """Resolves value and provenance for each of the 11 major metrics."""
    if canonical_key == "revenue":
        v = get_value(data, "income_statement", "revenue_from_operations", period)
        if v is None:
            v = get_value(data, "income_statement", "revenue", period)
        src = get_source(data, "income_statement", "revenue_from_operations") or get_source(data, "income_statement", "revenue")
        return v, src

    elif canonical_key == "cogs":
        v = get_value(data, "income_statement", "cost_of_materials_consumed", period)
        if v is None:
            v = get_value(data, "income_statement", "cogs", period)
        if v is None:
            v = get_value(data, "income_statement", "cost_of_goods_sold", period)
        src = get_source(data, "income_statement", "cost_of_materials_consumed") or get_source(data, "income_statement", "cogs")
        return v, src

    elif canonical_key == "operating_expenses":
        v = get_value(data, "income_statement", "total_operating_expenses", period)
        src = get_source(data, "income_statement", "total_operating_expenses")
        if v is None:
            emp = get_value(data, "income_statement", "employee_benefit_expenses", period)
            other_opex = get_value(data, "income_statement", "other_operating_expenses", period)
            da = get_value(data, "income_statement", "depreciation_and_amortization", period)
            if emp is not None and other_opex is not None and da is not None:
                v = emp + other_opex + da
                src = get_source(data, "income_statement", "employee_benefit_expenses")
        return v, src

    elif canonical_key == "gross_profit":
        v = get_value(data, "income_statement", "gross_profit", period)
        src = get_source(data, "income_statement", "gross_profit")
        if v is None:
            rev, _ = _resolve_metric(data, "revenue", period)
            cogs, _ = _resolve_metric(data, "cogs", period)
            if rev is not None and cogs is not None:
                v = rev - cogs
        return v, src

    elif canonical_key == "operating_profit":
        v = get_value(data, "income_statement", "operating_profit", period)
        if v is None:
            v = get_value(data, "income_statement", "operating_income", period)
        src = get_source(data, "income_statement", "operating_profit") or get_source(data, "income_statement", "operating_income")
        return v, src

    elif canonical_key == "net_profit":
        v = get_value(data, "income_statement", "profit_for_the_period", period)
        if v is None:
            v = get_value(data, "income_statement", "net_profit", period)
        src = get_source(data, "income_statement", "profit_for_the_period") or get_source(data, "income_statement", "net_profit")
        return v, src

    elif canonical_key == "assets":
        v = get_value(data, "balance_sheet", "total_assets", period)
        src = get_source(data, "balance_sheet", "total_assets")
        return v, src

    elif canonical_key == "liabilities":
        v = get_value(data, "balance_sheet", "total_liabilities", period)
        src = get_source(data, "balance_sheet", "total_liabilities")
        if v is None:
            nc = get_value(data, "balance_sheet", "total_non_current_liabilities", period)
            c = get_value(data, "balance_sheet", "total_current_liabilities", period)
            if nc is not None and c is not None:
                v = nc + c
                src = get_source(data, "balance_sheet", "total_current_liabilities")
        return v, src

    elif canonical_key == "equity":
        v = get_value(data, "balance_sheet", "total_equity", period)
        src = get_source(data, "balance_sheet", "total_equity")
        return v, src

    elif canonical_key == "cash":
        v = get_value(data, "balance_sheet", "cash_and_cash_equivalents", period)
        if v is None:
            v = get_value(data, "balance_sheet", "cash", period)
        src = get_source(data, "balance_sheet", "cash_and_cash_equivalents")
        return v, src

    elif canonical_key == "debt":
        lt = get_value(data, "balance_sheet", "long_term_borrowings", period)
        st = get_value(data, "balance_sheet", "short_term_borrowings", period)
        src = get_source(data, "balance_sheet", "long_term_borrowings")
        if lt is not None and st is not None:
            return lt + st, src
        elif lt is not None:
            return lt, src
        v = get_value(data, "balance_sheet", "total_debt", period)
        return v, src

    return None, None


# ---------------------------------------------------------------------------
# Master Analytical Comparison Engine
# ---------------------------------------------------------------------------

TARGET_GROWTH_METRICS = [
    ("Revenue", "revenue"),
    ("COGS", "cogs"),
    ("Operating Expenses", "operating_expenses"),
    ("Gross Profit", "gross_profit"),
    ("Operating Profit", "operating_profit"),
    ("Net Profit", "net_profit"),
    ("Assets", "assets"),
    ("Liabilities", "liabilities"),
    ("Equity", "equity"),
    ("Cash", "cash"),
    ("Debt", "debt"),
]


class AnalyticalComparisonEngine:
    """
    Computes YoY growth, absolute change, percentage change, and direction for all 11 major metrics.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        current_period: Optional[str] = None,
        previous_period: Optional[str] = None,
    ) -> AnalyticalComparisonResult:
        periods = get_periods(data)
        curr = current_period or (periods[0] if periods else "FY_CURRENT")
        prev = previous_period or (periods[1] if len(periods) > 1 else None)

        metrics: Dict[str, MetricGrowthDetail] = {}
        growth_rates: Dict[str, Optional[float]] = {}

        computed_count = 0

        for label, canonical_key in TARGET_GROWTH_METRICS:
            curr_val, src = _resolve_metric(data, canonical_key, curr)
            prev_val = _resolve_metric(data, canonical_key, prev)[0] if prev else None

            # Calculate change
            abs_change: Optional[Decimal] = None
            pct_change: Optional[float] = None
            direction: Direction = "NOT_AVAILABLE"
            status: GrowthStatus = "NOT_AVAILABLE"
            details: Optional[str] = None

            if curr_val is not None and prev_val is not None:
                abs_change = curr_val - prev_val
                status = "COMPUTED"
                computed_count += 1

                if prev_val != 0:
                    pct_change = round(float((curr_val - prev_val) / abs(prev_val) * 100), 2)
                    if abs_change > 0:
                        direction = "INCREASE"
                    elif abs_change < 0:
                        direction = "DECREASE"
                    else:
                        direction = "NO_CHANGE"
                    details = f"{label} changed from {prev_val} to {curr_val} ({pct_change}%)."
                else:
                    # Previous value is zero
                    status = "ZERO_BASE"
                    if curr_val > 0:
                        direction = "INCREASE"
                        details = f"{label} increased from 0.00 to {curr_val} (zero base)."
                    elif curr_val < 0:
                        direction = "DECREASE"
                        details = f"{label} decreased from 0.00 to {curr_val} (zero base)."
                    else:
                        direction = "NO_CHANGE"
                        pct_change = 0.0
                        details = f"{label} remained flat at 0.00."
            elif curr_val is not None and prev_val is None:
                details = f"{label} current value is {curr_val}; previous period value is unavailable."
            elif curr_val is None and prev_val is not None:
                details = f"{label} previous value was {prev_val}; current period value is unavailable."
            else:
                details = f"{label} data unavailable in current and previous periods."

            record = MetricGrowthDetail(
                metric_name=label,
                canonical_key=canonical_key,
                current_value=curr_val,
                previous_value=prev_val,
                absolute_change=abs_change,
                percentage_change=pct_change,
                direction=direction,
                status=status,
                source=src,
                details=details,
            )
            metrics[canonical_key] = record
            growth_rates[f"{canonical_key}_growth_pct"] = pct_change

        overall_status: Literal["COMPUTED", "PARTIAL", "NOT_AVAILABLE"] = "COMPUTED"
        if computed_count == 0:
            overall_status = "NOT_AVAILABLE"
        elif computed_count < len(TARGET_GROWTH_METRICS):
            overall_status = "PARTIAL"

        return AnalyticalComparisonResult(
            current_period=curr,
            previous_period=prev,
            metrics=metrics,
            growth_rates=growth_rates,
            total_metrics_evaluated=len(TARGET_GROWTH_METRICS),
            metrics_computed=computed_count,
            status=overall_status,
        )


def run(data: Dict[str, Any], current_period: Optional[str] = None, previous_period: Optional[str] = None) -> AnalyticalComparisonResult:
    return AnalyticalComparisonEngine.evaluate(data, current_period=current_period, previous_period=previous_period)
