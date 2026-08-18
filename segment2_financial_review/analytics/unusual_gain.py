"""
Check 6: Unusual Gain & Non-Operating Income Divergence Engine.

Calculates:
- Profit Growth %
- Revenue Growth %
- Profit vs Revenue Divergence (Profit Growth % - Revenue Growth %)
- Other Income Growth %
- Other Income / Revenue %
- Gain Amount
- Gain / Profit %
- Investment Gain
- Asset Disposal Gain
- One-Time Gain

Core Formula:
  Profit vs Revenue Divergence = Profit Growth % - Revenue Growth %

Identifies cases where profit surge is driven by one-off gains rather than operational growth.
Thresholds are configuration-driven.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from segment2_financial_review.config import (
    DEFAULT_DIVERGENCE_THRESHOLD_PP,
    DEFAULT_OTHER_INCOME_GROWTH_THRESHOLD,
    DEFAULT_OTHER_INCOME_TO_REVENUE_THRESHOLD,
)


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

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


class UnusualGainResult(BaseModel):
    """Complete output of the Unusual Gain Analysis Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    profit_growth_pct: Optional[float] = None
    revenue_growth_pct: Optional[float] = None
    profit_vs_revenue_divergence_pp: Optional[float] = None
    other_income_growth_pct: Optional[float] = None
    other_income_to_revenue_pct: Optional[float] = None
    gain_amount: Optional[Decimal] = None
    gain_to_profit_pct: Optional[float] = None
    investment_gain: Optional[Decimal] = None
    asset_disposal_gain: Optional[Decimal] = None
    one_time_gain: Optional[Decimal] = None
    divergence_trigger_status: str   # "ELEVATED" | "NORMAL" | "INSUFFICIENT_DATA"
    divergence_threshold_pp: float = DEFAULT_DIVERGENCE_THRESHOLD_PP
    score: float = 100.0
    status: CheckOverallStatus
    source: Optional[SourceTrace] = None
    issues: List[str] = Field(default_factory=list)
    details: Optional[str] = None


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
# Master Unusual Gain Analysis Engine
# ---------------------------------------------------------------------------

class UnusualGainEngine:
    """
    Analyzes profit vs revenue divergence and non-operating gain contributions.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        divergence_threshold_pp: float = DEFAULT_DIVERGENCE_THRESHOLD_PP,
        period: Optional[str] = None,
    ) -> UnusualGainResult:
        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")
        prev = periods[1] if len(periods) > 1 else None

        # Extract values
        rev_curr = get_value(data, "income_statement", "revenue_from_operations", curr)
        if rev_curr is None:
            rev_curr = get_value(data, "income_statement", "revenue", curr)

        rev_prev = get_value(data, "income_statement", "revenue_from_operations", prev) if prev else None
        if rev_prev is None and prev:
            rev_prev = get_value(data, "income_statement", "revenue", prev)

        pat_curr = get_value(data, "income_statement", "profit_for_the_period", curr)
        if pat_curr is None:
            pat_curr = get_value(data, "income_statement", "net_profit", curr)

        pat_prev = get_value(data, "income_statement", "profit_for_the_period", prev) if prev else None
        if pat_prev is None and prev:
            pat_prev = get_value(data, "income_statement", "net_profit", prev)

        oi_curr = get_value(data, "income_statement", "other_income", curr)
        oi_prev = get_value(data, "income_statement", "other_income", prev) if prev else None

        # Scan for specific gain itemizations if present
        inv_gain = get_value(data, "income_statement", "investment_gain", curr)
        disposal_gain = get_value(data, "income_statement", "asset_disposal_gain", curr)
        one_time_gain = get_value(data, "income_statement", "exceptional_items", curr)

        # Fallback gain amount is total other income if specific items are not separate
        gain_amount = oi_curr
        if inv_gain is not None or disposal_gain is not None or one_time_gain is not None:
            items = [g for g in (inv_gain, disposal_gain, one_time_gain) if g is not None]
            gain_amount = sum(items)

        src = get_source(data, "income_statement", "other_income") or get_source(data, "income_statement", "profit_for_the_period")

        issues: List[str] = []

        # 1. Growth Rates
        rev_growth: Optional[float] = None
        pat_growth: Optional[float] = None
        oi_growth: Optional[float] = None
        divergence_pp: Optional[float] = None

        if rev_curr is not None and rev_prev is not None and rev_prev != 0:
            rev_growth = round(float((rev_curr - rev_prev) / abs(rev_prev) * 100), 2)

        if pat_curr is not None and pat_prev is not None and pat_prev != 0:
            pat_growth = round(float((pat_curr - pat_prev) / abs(pat_prev) * 100), 2)

        if oi_curr is not None and oi_prev is not None and oi_prev != 0:
            oi_growth = round(float((oi_curr - oi_prev) / abs(oi_prev) * 100), 2)

        # 2. Divergence = Profit Growth % - Revenue Growth %
        trigger_status = "INSUFFICIENT_DATA"
        if pat_growth is not None and rev_growth is not None:
            divergence_pp = round(pat_growth - rev_growth, 2)
            if divergence_pp >= divergence_threshold_pp:
                trigger_status = "ELEVATED"
                issues.append(
                    f"ELEVATED: Profit growth ({pat_growth}%) exceeds revenue growth ({rev_growth}%) by {divergence_pp} pp (threshold: {divergence_threshold_pp} pp)."
                )
            else:
                trigger_status = "NORMAL"

        # 3. Ratios: Other Income / Revenue % and Gain / Profit %
        oi_to_rev_pct: Optional[float] = None
        if oi_curr is not None and rev_curr is not None and rev_curr != 0:
            oi_to_rev_pct = round(float((oi_curr / rev_curr) * 100), 2)
            if oi_to_rev_pct >= DEFAULT_OTHER_INCOME_TO_REVENUE_THRESHOLD:
                issues.append(f"WARNING: Other Income represents {oi_to_rev_pct}% of Revenue (threshold: {DEFAULT_OTHER_INCOME_TO_REVENUE_THRESHOLD}%).")

        gain_to_pat_pct: Optional[float] = None
        if gain_amount is not None and pat_curr is not None and pat_curr != 0:
            gain_to_pat_pct = round(float((gain_amount / pat_curr) * 100), 2)

        # 4. Status & Score
        overall_status: CheckOverallStatus = "PASSED"
        score = 100.0

        if trigger_status == "ELEVATED":
            overall_status = "WARNING"
            score = 80.0
        elif trigger_status == "INSUFFICIENT_DATA":
            overall_status = "NOT_AVAILABLE"
            score = 0.0

        details = (
            f"Profit growth={pat_growth}%, Revenue growth={rev_growth}%, Divergence={divergence_pp} pp. "
            f"Other Income={oi_curr} Cr ({oi_to_rev_pct}% of revenue). Trigger status: {trigger_status}."
        )

        return UnusualGainResult(
            period=curr,
            profit_growth_pct=pat_growth,
            revenue_growth_pct=rev_growth,
            profit_vs_revenue_divergence_pp=divergence_pp,
            other_income_growth_pct=oi_growth,
            other_income_to_revenue_pct=oi_to_rev_pct,
            gain_amount=gain_amount,
            gain_to_profit_pct=gain_to_pat_pct,
            investment_gain=inv_gain,
            asset_disposal_gain=disposal_gain,
            one_time_gain=one_time_gain,
            divergence_trigger_status=trigger_status,
            divergence_threshold_pp=divergence_threshold_pp,
            score=score,
            status=overall_status,
            source=src,
            issues=issues,
            details=details,
        )


def run(
    data: Dict[str, Any],
    divergence_threshold_pp: float = DEFAULT_DIVERGENCE_THRESHOLD_PP,
    period: Optional[str] = None,
) -> UnusualGainResult:
    return UnusualGainEngine.evaluate(data, divergence_threshold_pp=divergence_threshold_pp, period=period)
