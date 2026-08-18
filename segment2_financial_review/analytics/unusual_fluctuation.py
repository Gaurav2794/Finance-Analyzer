"""
Check 5: Unusual Fluctuation Scanner.

Performs an exhaustive YoY sweep of 15 key financial metrics:
1. Revenue
2. Expense
3. COGS
4. Gross Profit
5. Operating Profit
6. Net Profit
7. Assets
8. Liabilities
9. Equity
10. Cash
11. Debt
12. Other Income
13. Gross Margin
14. Operating Margin
15. Net Margin

Thresholds are configuration-driven from `segment2_financial_review.config`.
Calculates: Current, Previous, Change %, Threshold, Severity, Direction.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from segment2_financial_review.config import (
    DEFAULT_FLUCTUATION_THRESHOLDS,
    HIGH_SEVERITY_MULTIPLIER,
)


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

Severity = Literal["CRITICAL", "HIGH", "REVIEW", "PASSED", "NOT_AVAILABLE"]
Direction = Literal["INCREASE", "DECREASE", "NO_CHANGE", "NOT_AVAILABLE"]
CheckOverallStatus = Literal["PASSED", "FAILED", "NOT_AVAILABLE", "WARNING"]


class UnusualFluctuationItem(BaseModel):
    """Scan result for a single financial line item."""
    model_config = _DECIMAL_CONFIG

    metric: str
    canonical_key: str
    current_value: Optional[Decimal] = None
    previous_value: Optional[Decimal] = None
    change_pct: Optional[float] = None
    threshold_pct: float
    severity: Severity
    direction: Direction
    note: Optional[str] = None


class UnusualFluctuationResult(BaseModel):
    """Complete output of the Unusual Fluctuation Scanner."""
    model_config = _DECIMAL_CONFIG

    period: str
    items: List[UnusualFluctuationItem] = Field(default_factory=list)
    total_items_scanned: int = 0
    high_severity_count: int = 0
    review_severity_count: int = 0
    flagged_count: int = 0
    score: float = 0.0
    status: CheckOverallStatus
    thresholds_applied: Dict[str, float] = Field(default_factory=dict)
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
# Metric Value Resolvers for the 15 Target Metrics
# ---------------------------------------------------------------------------

def _resolve_raw_metric(data: Dict[str, Any], canonical_key: str, period: str) -> Optional[Decimal]:
    if canonical_key == "revenue":
        v = get_value(data, "income_statement", "revenue_from_operations", period)
        if v is None:
            v = get_value(data, "income_statement", "revenue", period)
        return v

    elif canonical_key == "expense":
        v = get_value(data, "income_statement", "total_expenses", period)
        if v is None:
            v = get_value(data, "income_statement", "total_operating_expenses", period)
        return v

    elif canonical_key == "cogs":
        v = get_value(data, "income_statement", "cost_of_materials_consumed", period)
        if v is None:
            v = get_value(data, "income_statement", "cogs", period)
        if v is None:
            v = get_value(data, "income_statement", "cost_of_goods_sold", period)
        return v

    elif canonical_key == "gross_profit":
        v = get_value(data, "income_statement", "gross_profit", period)
        if v is None:
            rev = _resolve_raw_metric(data, "revenue", period)
            cogs = _resolve_raw_metric(data, "cogs", period)
            if rev is not None and cogs is not None:
                v = rev - cogs
        return v

    elif canonical_key == "operating_profit":
        v = get_value(data, "income_statement", "operating_profit", period)
        if v is None:
            v = get_value(data, "income_statement", "operating_income", period)
        return v

    elif canonical_key == "net_profit":
        v = get_value(data, "income_statement", "profit_for_the_period", period)
        if v is None:
            v = get_value(data, "income_statement", "net_profit", period)
        return v

    elif canonical_key == "assets":
        return get_value(data, "balance_sheet", "total_assets", period)

    elif canonical_key == "liabilities":
        v = get_value(data, "balance_sheet", "total_liabilities", period)
        if v is None:
            nc = get_value(data, "balance_sheet", "total_non_current_liabilities", period)
            c = get_value(data, "balance_sheet", "total_current_liabilities", period)
            if nc is not None and c is not None:
                v = nc + c
        return v

    elif canonical_key == "equity":
        return get_value(data, "balance_sheet", "total_equity", period)

    elif canonical_key == "cash":
        v = get_value(data, "balance_sheet", "cash_and_cash_equivalents", period)
        if v is None:
            v = get_value(data, "balance_sheet", "cash", period)
        return v

    elif canonical_key == "debt":
        lt = get_value(data, "balance_sheet", "long_term_borrowings", period)
        st = get_value(data, "balance_sheet", "short_term_borrowings", period)
        if lt is not None and st is not None:
            return lt + st
        elif lt is not None:
            return lt
        return get_value(data, "balance_sheet", "total_debt", period)

    elif canonical_key == "other_income":
        return get_value(data, "income_statement", "other_income", period)

    # Margin metrics (calculated as ratios in %)
    elif canonical_key == "gross_margin":
        gp = _resolve_raw_metric(data, "gross_profit", period)
        rev = _resolve_raw_metric(data, "revenue", period)
        if gp is not None and rev is not None and rev != 0:
            return (gp / rev) * Decimal("100")
        return None

    elif canonical_key == "operating_margin":
        op = _resolve_raw_metric(data, "operating_profit", period)
        rev = _resolve_raw_metric(data, "revenue", period)
        if op is not None and rev is not None and rev != 0:
            return (op / rev) * Decimal("100")
        return None

    elif canonical_key == "net_margin":
        pat = _resolve_raw_metric(data, "net_profit", period)
        rev = _resolve_raw_metric(data, "revenue", period)
        if pat is not None and rev is not None and rev != 0:
            return (pat / rev) * Decimal("100")
        return None

    return None


METRIC_TARGETS = [
    ("Revenue", "revenue"),
    ("Expense", "expense"),
    ("COGS", "cogs"),
    ("Gross Profit", "gross_profit"),
    ("Operating Profit", "operating_profit"),
    ("Net Profit", "net_profit"),
    ("Assets", "assets"),
    ("Liabilities", "liabilities"),
    ("Equity", "equity"),
    ("Cash", "cash"),
    ("Debt", "debt"),
    ("Other Income", "other_income"),
    ("Gross Margin", "gross_margin"),
    ("Operating Margin", "operating_margin"),
    ("Net Margin", "net_margin"),
]


# ---------------------------------------------------------------------------
# Master Unusual Fluctuation Scanner
# ---------------------------------------------------------------------------

class UnusualFluctuationScanner:
    """
    Evaluates fluctuations against configuration-driven thresholds.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        thresholds: Optional[Dict[str, float]] = None,
        period: Optional[str] = None,
    ) -> UnusualFluctuationResult:
        active_thresholds = dict(DEFAULT_FLUCTUATION_THRESHOLDS)
        if thresholds:
            active_thresholds.update(thresholds)

        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")
        prev = periods[1] if len(periods) > 1 else None

        items: List[UnusualFluctuationItem] = []
        issues: List[str] = []

        high_count = 0
        review_count = 0
        total_scanned = 0

        for label, canonical_key in METRIC_TARGETS:
            total_scanned += 1
            threshold = active_thresholds.get(canonical_key, 20.0)

            curr_val = _resolve_raw_metric(data, canonical_key, curr)
            prev_val = _resolve_raw_metric(data, canonical_key, prev) if prev else None

            if curr_val is None or prev_val is None:
                items.append(
                    UnusualFluctuationItem(
                        metric=label,
                        canonical_key=canonical_key,
                        current_value=curr_val,
                        previous_value=prev_val,
                        change_pct=None,
                        threshold_pct=threshold,
                        severity="NOT_AVAILABLE",
                        direction="NOT_AVAILABLE",
                        note=f"Insufficient data for {label} across {curr} and {prev}.",
                    )
                )
                continue

            # Calculate change %
            # For margins: difference in percentage points
            is_margin = "margin" in canonical_key
            if is_margin:
                change = float(curr_val - prev_val)
                change_pct = round(change, 2)
            else:
                if prev_val != 0:
                    change_pct = round(float((curr_val - prev_val) / abs(prev_val) * 100), 2)
                else:
                    change_pct = 100.0 if curr_val != 0 else 0.0

            # Direction
            diff = curr_val - prev_val
            if diff > 0:
                direction: Direction = "INCREASE"
            elif diff < 0:
                direction = "DECREASE"
            else:
                direction = "NO_CHANGE"

            # Severity classification
            abs_change = abs(change_pct)
            high_threshold = threshold * HIGH_SEVERITY_MULTIPLIER

            if abs_change >= high_threshold:
                severity: Severity = "HIGH"
                high_count += 1
                note = f"High fluctuation: {label} changed by {change_pct:+.2f}% (Threshold: {threshold}%, High trigger: {high_threshold}%)."
                issues.append(f"HIGH: {label} fluctuated by {change_pct:+.2f}% ({curr_val} vs {prev_val} Cr).")
            elif abs_change >= threshold:
                severity = "REVIEW"
                review_count += 1
                note = f"Elevated fluctuation: {label} changed by {change_pct:+.2f}% (Threshold: {threshold}%)."
                issues.append(f"REVIEW: {label} fluctuated by {change_pct:+.2f}% ({curr_val} vs {prev_val} Cr).")
            else:
                severity = "PASSED"
                note = f"Normal fluctuation: {label} changed by {change_pct:+.2f}% within threshold ({threshold}%)."

            items.append(
                UnusualFluctuationItem(
                    metric=label,
                    canonical_key=canonical_key,
                    current_value=curr_val,
                    previous_value=prev_val,
                    change_pct=change_pct,
                    threshold_pct=threshold,
                    severity=severity,
                    direction=direction,
                    note=note,
                )
            )

        flagged_count = high_count + review_count
        evaluated = sum(1 for i in items if i.severity != "NOT_AVAILABLE")
        score = round(max(0.0, 100.0 - (high_count * 15.0 + review_count * 5.0)), 2) if evaluated > 0 else 0.0

        overall_status: CheckOverallStatus = "PASSED"
        if high_count > 0:
            overall_status = "WARNING"
        elif review_count > 0:
            overall_status = "WARNING"
        elif evaluated == 0:
            overall_status = "NOT_AVAILABLE"

        return UnusualFluctuationResult(
            period=curr,
            items=items,
            total_items_scanned=total_scanned,
            high_severity_count=high_count,
            review_severity_count=review_count,
            flagged_count=flagged_count,
            score=score,
            status=overall_status,
            thresholds_applied=active_thresholds,
            issues=issues,
        )


def run(
    data: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
    period: Optional[str] = None,
) -> UnusualFluctuationResult:
    return UnusualFluctuationScanner.evaluate(data, thresholds=thresholds, period=period)
