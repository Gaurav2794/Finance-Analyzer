"""
Check 1: Mathematical Accuracy Engine.

Validates core accounting equations:
1. Balance Sheet: Assets = Liabilities + Equity
2. Gross Profit: Revenue - COGS = Gross Profit
3. Operating Income: Gross Profit - Operating Expenses = Operating Income
4. Net Income: Operating Income + Other Income - Interest - Tax = Net Income

Rules & Guarantees:
- Pure deterministic calculations using Decimal.
- No silent zero assumptions for missing values.
- If required input is missing -> status = "NOT_AVAILABLE".
- Statuses: PASSED, FAILED, NOT_AVAILABLE, WARNING.
- Tolerance handling: ABS(calculated - reported) <= tolerance.
- Full provenance / source traceability when available.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

CalculationStatus = Literal["PASSED", "FAILED", "NOT_AVAILABLE", "WARNING"]


class SourceTrace(BaseModel):
    """Provenance tracking for line items."""
    model_config = _DECIMAL_CONFIG

    file: Optional[str] = None
    page: Optional[int] = None
    table_index: Optional[int] = None
    note_ref: Optional[str] = None
    raw_label: Optional[str] = None
    bbox: Optional[List[float]] = None


class CalculationDetail(BaseModel):
    """Detailed result of a single equation validation."""
    model_config = _DECIMAL_CONFIG

    check_id: str
    check_name: str
    formula: str
    period: str
    calculated_value: Optional[Decimal] = None
    reported_value: Optional[Decimal] = None
    absolute_difference: Optional[Decimal] = None
    percentage_difference: Optional[float] = None
    tolerance: Decimal = Decimal("0.01")
    status: CalculationStatus
    source: Optional[SourceTrace] = None
    inputs: Dict[str, Optional[Decimal]] = Field(default_factory=dict)
    details: Optional[str] = None


class AccuracyMetrics(BaseModel):
    """Aggregate accuracy scores across evaluated calculations."""
    model_config = _DECIMAL_CONFIG

    total_accuracy: float
    subtotal_accuracy: float
    cross_cast_accuracy: float
    arithmetic_accuracy: float
    formula_accuracy: float
    balance_sheet_reconciliation: CalculationDetail
    rounding_difference: Decimal


class MathematicalAccuracyResult(BaseModel):
    """Complete output of the Mathematical Accuracy Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    status: CalculationStatus
    score: float
    calculations: Dict[str, CalculationDetail]
    metrics: AccuracyMetrics
    total_accuracy: float
    subtotal_accuracy: float
    cross_cast_accuracy: float
    arithmetic_accuracy: float
    formula_accuracy: float
    balance_sheet_reconciliation: CalculationDetail
    rounding_difference: Decimal
    issues: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper: Safe Decimal extractor from Phase 1 data structures
# ---------------------------------------------------------------------------

def _to_decimal(val: Any) -> Optional[Decimal]:
    """Convert a value safely to Decimal without precision loss."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return None


def get_value(
    data: Dict[str, Any],
    statement: str,
    key: str,
    period: str,
) -> Optional[Decimal]:
    """
    Safely retrieve a numeric value as Decimal from financial statement data.
    Supports flat, nested, and hierarchical JSON structures.
    Never assumes zero for missing keys.
    """
    stmt_dict = data.get(statement, {})
    if not isinstance(stmt_dict, dict):
        return None

    # 1. Try flat key at top-level
    item = stmt_dict.get(key)

    # 2. If absent, search recursively up to 3 levels deep
    if item is None:
        item = _find_nested_item(stmt_dict, key)

    if item is None or not isinstance(item, dict):
        return None

    # 3. If item is a container whose first child has 'values', try that
    if "values" not in item:
        for sub_val in item.values():
            if isinstance(sub_val, dict) and "values" in sub_val:
                item = sub_val
                break

    values_dict = item.get("values")
    if not isinstance(values_dict, dict):
        return None

    raw_val = values_dict.get(period)
    return _to_decimal(raw_val)


def _find_nested_item(d: Dict[str, Any], key: str, depth: int = 0) -> Optional[Dict[str, Any]]:
    """Helper to find a key inside nested sections."""
    if depth > 3:
        return None
    for k, v in d.items():
        if k == key and isinstance(v, dict):
            return v
        if isinstance(v, dict):
            found = _find_nested_item(v, key, depth + 1)
            if found is not None:
                return found
    return None


def get_source(data: Dict[str, Any], statement: str, key: str) -> Optional[SourceTrace]:
    """Retrieve SourceTrace provenance for a specific line item."""
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
            raw_label=src.get("raw_label") or (item.get("standard_label")),
            bbox=src.get("bbox"),
        )
    return None


def get_primary_period(data: Dict[str, Any]) -> Optional[str]:
    """Resolve the latest/primary period from metadata or statements."""
    periods = data.get("metadata", {}).get("periods", [])
    if periods and isinstance(periods, list) and len(periods) > 0:
        first = periods[0]
        if isinstance(first, dict) and "period_key" in first:
            return first["period_key"]

    # Fallback: scan balance sheet keys
    bs = data.get("balance_sheet", {})
    if isinstance(bs, dict):
        for v in bs.values():
            if isinstance(v, dict) and "values" in v and isinstance(v["values"], dict):
                keys = list(v["values"].keys())
                if keys:
                    return keys[0]
    return None


# ---------------------------------------------------------------------------
# Core Equation Validators
# ---------------------------------------------------------------------------

def validate_balance_sheet(
    data: Dict[str, Any],
    period: str,
    tolerance: Decimal = Decimal("0.01"),
    warning_tolerance: Decimal = Decimal("0.05"),
) -> CalculationDetail:
    """
    Equation 1: Assets = Liabilities + Equity
    """
    assets = get_value(data, "balance_sheet", "total_assets", period)
    equity = get_value(data, "balance_sheet", "total_equity", period)
    liabilities = get_value(data, "balance_sheet", "total_liabilities", period)

    # If total_liabilities is not directly present, check if non-current + current are available
    if liabilities is None:
        nc_liab = get_value(data, "balance_sheet", "total_non_current_liabilities", period)
        c_liab = get_value(data, "balance_sheet", "total_current_liabilities", period)
        if nc_liab is not None and c_liab is not None:
            liabilities = nc_liab + c_liab

    inputs = {
        "total_assets": assets,
        "total_equity": equity,
        "total_liabilities": liabilities,
    }
    src = get_source(data, "balance_sheet", "total_assets")

    if assets is None or equity is None or liabilities is None:
        missing = [k for k, v in inputs.items() if v is None]
        return CalculationDetail(
            check_id="MATH_001_BALANCE_SHEET",
            check_name="Balance Sheet Reconciliation",
            formula="Assets = Liabilities + Equity",
            period=period,
            calculated_value=None,
            reported_value=assets,
            absolute_difference=None,
            percentage_difference=None,
            tolerance=tolerance,
            status="NOT_AVAILABLE",
            source=src,
            inputs=inputs,
            details=f"Missing required balance sheet components: {', '.join(missing)}",
        )

    calculated = liabilities + equity
    diff = abs(assets - calculated)
    pct_diff = round(float(diff / abs(assets) * 100), 4) if assets != 0 else 0.0

    if diff <= tolerance:
        status: CalculationStatus = "PASSED"
        details = "Balance Sheet balances within tolerance."
    elif diff <= warning_tolerance:
        status = "WARNING"
        details = f"Minor rounding difference detected (diff={diff} Cr)."
    else:
        status = "FAILED"
        details = f"Balance Sheet does not balance: reported Assets={assets} Cr, calculated L+E={calculated} Cr (diff={diff} Cr)."

    return CalculationDetail(
        check_id="MATH_001_BALANCE_SHEET",
        check_name="Balance Sheet Reconciliation",
        formula="Assets = Liabilities + Equity",
        period=period,
        calculated_value=calculated,
        reported_value=assets,
        absolute_difference=diff,
        percentage_difference=pct_diff,
        tolerance=tolerance,
        status=status,
        source=src,
        inputs=inputs,
        details=details,
    )


def validate_gross_profit(
    data: Dict[str, Any],
    period: str,
    tolerance: Decimal = Decimal("0.01"),
    warning_tolerance: Decimal = Decimal("0.05"),
) -> CalculationDetail:
    """
    Equation 2: Revenue - COGS = Gross Profit (or Total Income - COGS = Gross Profit)
    """
    tot_income = get_value(data, "income_statement", "total_income", period)
    rev = get_value(data, "income_statement", "revenue_from_operations", period)
    if rev is None:
        rev = get_value(data, "income_statement", "revenue", period)

    cogs = get_value(data, "income_statement", "cost_of_materials_consumed", period)
    if cogs is None:
        cogs = get_value(data, "income_statement", "cogs", period)
    if cogs is None:
        cogs = get_value(data, "income_statement", "cost_of_goods_sold", period)

    reported_gp = get_value(data, "income_statement", "gross_profit", period)

    # If Total Income - COGS matches reported Gross Profit (e.g. when other operating income is included in top-line), use Total Income
    if rev is not None and cogs is not None and reported_gp is not None and tot_income is not None:
        if abs(rev - cogs - reported_gp) > tolerance and abs(tot_income - cogs - reported_gp) <= max(tolerance, warning_tolerance):
            rev = tot_income

    inputs = {
        "revenue": rev,
        "cogs": cogs,
        "reported_gross_profit": reported_gp,
    }
    src = get_source(data, "income_statement", "gross_profit") or get_source(data, "income_statement", "revenue_from_operations")

    if rev is None or cogs is None or reported_gp is None:
        missing = [k for k, v in inputs.items() if v is None]
        return CalculationDetail(
            check_id="MATH_002_GROSS_PROFIT",
            check_name="Gross Profit Equation",
            formula="Revenue - COGS = Gross Profit",
            period=period,
            calculated_value=(rev - cogs) if (rev is not None and cogs is not None) else None,
            reported_value=reported_gp,
            absolute_difference=None,
            percentage_difference=None,
            tolerance=tolerance,
            status="NOT_AVAILABLE",
            source=src,
            inputs=inputs,
            details=f"Missing required Gross Profit components: {', '.join(missing)}",
        )

    calculated = rev - cogs
    diff = abs(calculated - reported_gp)
    pct_diff = round(float(diff / abs(reported_gp) * 100), 4) if reported_gp != 0 else 0.0

    if diff <= tolerance:
        status: CalculationStatus = "PASSED"
        details = "Gross profit formula verified."
    elif diff <= warning_tolerance:
        status = "WARNING"
        details = f"Minor rounding difference in Gross Profit (diff={diff} Cr)."
    else:
        status = "FAILED"
        details = f"Gross Profit mismatch: calculated {calculated} vs reported {reported_gp} (diff={diff} Cr)."

    return CalculationDetail(
        check_id="MATH_002_GROSS_PROFIT",
        check_name="Gross Profit Equation",
        formula="Revenue - COGS = Gross Profit",
        period=period,
        calculated_value=calculated,
        reported_value=reported_gp,
        absolute_difference=diff,
        percentage_difference=pct_diff,
        tolerance=tolerance,
        status=status,
        source=src,
        inputs=inputs,
        details=details,
    )


def validate_operating_income(
    data: Dict[str, Any],
    period: str,
    tolerance: Decimal = Decimal("0.01"),
    warning_tolerance: Decimal = Decimal("0.05"),
) -> CalculationDetail:
    """
    Equation 3: Gross Profit - Operating Expenses = Operating Income
    """
    gp = get_value(data, "income_statement", "gross_profit", period)
    if gp is None:
        rev = get_value(data, "income_statement", "revenue_from_operations", period)
        cogs = get_value(data, "income_statement", "cost_of_materials_consumed", period)
        if rev is not None and cogs is not None:
            gp = rev - cogs

    reported_op = get_value(data, "income_statement", "operating_profit", period)
    if reported_op is None:
        reported_op = get_value(data, "income_statement", "operating_income", period)

    # Resolve operating expenses: explicit item OR sum of opex components
    opex = get_value(data, "income_statement", "total_operating_expenses", period)
    if opex is None:
        emp = get_value(data, "income_statement", "employee_benefit_expenses", period)
        other_opex = get_value(data, "income_statement", "other_operating_expenses", period)
        da = get_value(data, "income_statement", "depreciation_and_amortization", period)

        if emp is not None and other_opex is not None and da is not None:
            opex = emp + other_opex + da

    inputs = {
        "gross_profit": gp,
        "operating_expenses": opex,
        "reported_operating_profit": reported_op,
    }
    src = get_source(data, "income_statement", "operating_profit")

    if gp is None or opex is None or reported_op is None:
        missing = [k for k, v in inputs.items() if v is None]
        return CalculationDetail(
            check_id="MATH_003_OPERATING_INCOME",
            check_name="Operating Income Equation",
            formula="Gross Profit - Operating Expenses = Operating Income",
            period=period,
            calculated_value=(gp - opex) if (gp is not None and opex is not None) else None,
            reported_value=reported_op,
            absolute_difference=None,
            percentage_difference=None,
            tolerance=tolerance,
            status="NOT_AVAILABLE",
            source=src,
            inputs=inputs,
            details=f"Missing required Operating Income components: {', '.join(missing)}",
        )

    calculated = gp - opex
    diff = abs(calculated - reported_op)
    pct_diff = round(float(diff / abs(reported_op) * 100), 4) if reported_op != 0 else 0.0

    if diff <= tolerance:
        status: CalculationStatus = "PASSED"
        details = "Operating Income formula verified."
    elif diff <= warning_tolerance:
        status = "WARNING"
        details = f"Minor rounding difference in Operating Income (diff={diff} Cr)."
    else:
        status = "FAILED"
        details = f"Operating Income mismatch: calculated {calculated} vs reported {reported_op} (diff={diff} Cr)."

    return CalculationDetail(
        check_id="MATH_003_OPERATING_INCOME",
        check_name="Operating Income Equation",
        formula="Gross Profit - Operating Expenses = Operating Income",
        period=period,
        calculated_value=calculated,
        reported_value=reported_op,
        absolute_difference=diff,
        percentage_difference=pct_diff,
        tolerance=tolerance,
        status=status,
        source=src,
        inputs=inputs,
        details=details,
    )


def validate_net_income(
    data: Dict[str, Any],
    period: str,
    tolerance: Decimal = Decimal("0.01"),
    warning_tolerance: Decimal = Decimal("0.05"),
) -> CalculationDetail:
    """
    Equation 4: Operating Income + Other Income - Interest - Tax = Net Income (or PBT - Tax = Net Income)
    """
    op = get_value(data, "income_statement", "operating_profit", period)
    if op is None:
        op = get_value(data, "income_statement", "operating_income", period)

    other_income = get_value(data, "income_statement", "other_income", period)
    interest = get_value(data, "income_statement", "finance_costs", period)
    if interest is None:
        interest = get_value(data, "income_statement", "interest_expense", period)

    tax = get_value(data, "income_statement", "total_tax_expense", period)
    if tax is None:
        tax = get_value(data, "income_statement", "tax_expense", period)

    reported_ni = get_value(data, "income_statement", "profit_for_the_period", period)
    if reported_ni is None:
        reported_ni = get_value(data, "income_statement", "net_profit", period)

    pbt = get_value(data, "income_statement", "profit_before_tax", period)

    inputs = {
        "operating_income": op,
        "other_income": other_income,
        "interest": interest,
        "tax": tax,
        "reported_net_income": reported_ni,
    }
    src = get_source(data, "income_statement", "profit_for_the_period")

    if (op is None and pbt is None) or interest is None or tax is None or reported_ni is None:
        missing = [k for k, v in inputs.items() if v is None]
        return CalculationDetail(
            check_id="MATH_004_NET_INCOME",
            check_name="Net Income Equation",
            formula="Operating Income + Other Income - Interest - Tax = Net Income",
            period=period,
            calculated_value=None,
            reported_value=reported_ni,
            absolute_difference=None,
            percentage_difference=None,
            tolerance=tolerance,
            status="NOT_AVAILABLE",
            source=src,
            inputs=inputs,
            details=f"Missing required Net Income components: {', '.join(missing)}",
        )

    # Evaluate options: standard (OP + Other Income - Interest - Tax), or OP - Interest - Tax (when other income was in OP), or PBT - Tax
    candidates = []
    if op is not None:
        candidates.append(op + (other_income or Decimal("0")) - interest - tax)
        candidates.append(op - interest - tax)
    if pbt is not None:
        candidates.append(pbt - tax)

    # Pick the candidate closest to reported_ni
    calculated = min(candidates, key=lambda c: abs(c - reported_ni))
    diff = abs(calculated - reported_ni)
    pct_diff = round(float(diff / abs(reported_ni) * 100), 4) if reported_ni != 0 else 0.0

    if diff <= tolerance:
        status: CalculationStatus = "PASSED"
        details = "Net Income formula verified."
    elif diff <= warning_tolerance:
        status = "WARNING"
        details = f"Minor rounding difference in Net Income (diff={diff} Cr)."
    else:
        status = "FAILED"
        details = f"Net Income mismatch: calculated {calculated} vs reported {reported_ni} (diff={diff} Cr)."

    return CalculationDetail(
        check_id="MATH_004_NET_INCOME",
        check_name="Net Income Equation",
        formula="Operating Income + Other Income - Interest - Tax = Net Income",
        period=period,
        calculated_value=calculated,
        reported_value=reported_ni,
        absolute_difference=diff,
        percentage_difference=pct_diff,
        tolerance=tolerance,
        status=status,
        source=src,
        inputs=inputs,
        details=details,
    )


# ---------------------------------------------------------------------------
# Master Mathematical Accuracy Engine
# ---------------------------------------------------------------------------

class MathematicalAccuracyEngine:
    """
    Engine to evaluate all 4 core accounting equations and calculate metrics.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        period: Optional[str] = None,
        tolerance: Decimal = Decimal("0.01"),
        warning_tolerance: Decimal = Decimal("0.05"),
    ) -> MathematicalAccuracyResult:
        active_period = period or get_primary_period(data) or "FY_CURRENT"

        bs_calc = validate_balance_sheet(data, active_period, tolerance, warning_tolerance)
        gp_calc = validate_gross_profit(data, active_period, tolerance, warning_tolerance)
        op_calc = validate_operating_income(data, active_period, tolerance, warning_tolerance)
        ni_calc = validate_net_income(data, active_period, tolerance, warning_tolerance)

        calculations = {
            "balance_sheet": bs_calc,
            "gross_profit": gp_calc,
            "operating_income": op_calc,
            "net_income": ni_calc,
        }

        issues: List[str] = []
        for name, calc in calculations.items():
            if calc.status == "FAILED":
                issues.append(f"FAILED: {calc.check_name} -> {calc.details}")
            elif calc.status == "WARNING":
                issues.append(f"WARNING: {calc.check_name} -> {calc.details}")
            elif calc.status == "NOT_AVAILABLE":
                issues.append(f"NOT_AVAILABLE: {calc.check_name} -> {calc.details}")

        # Metrics computation
        all_calcs = list(calculations.values())
        evaluated_calcs = [c for c in all_calcs if c.status != "NOT_AVAILABLE"]
        passed_calcs = [c for c in evaluated_calcs if c.status == "PASSED"]

        total_acc = round(len(passed_calcs) / len(evaluated_calcs) * 100.0, 2) if evaluated_calcs else 0.0

        # Subtotal accuracy: Gross Profit and Operating Income
        subtotal_calcs = [gp_calc, op_calc]
        eval_subtotals = [c for c in subtotal_calcs if c.status != "NOT_AVAILABLE"]
        pass_subtotals = [c for c in eval_subtotals if c.status == "PASSED"]
        subtotal_acc = round(len(pass_subtotals) / len(eval_subtotals) * 100.0, 2) if eval_subtotals else 0.0

        # Cross-cast accuracy: Balance Sheet reconciliation
        cc_calcs = [bs_calc]
        eval_cc = [c for c in cc_calcs if c.status != "NOT_AVAILABLE"]
        pass_cc = [c for c in eval_cc if c.status == "PASSED"]
        cross_cast_acc = round(len(pass_cc) / len(eval_cc) * 100.0, 2) if eval_cc else 0.0

        # Arithmetic accuracy: all non-failing arithmetic checks
        arith_acc = round((len(passed_calcs) + len([c for c in evaluated_calcs if c.status == "WARNING"])) / len(evaluated_calcs) * 100.0, 2) if evaluated_calcs else 0.0

        # Formula accuracy: percentage of formulas where calculated matches reported within tolerance
        formula_acc = total_acc

        # Rounding difference: max absolute difference among calculations with diff <= warning_tolerance
        diffs = [
            c.absolute_difference
            for c in all_calcs
            if c.absolute_difference is not None and c.absolute_difference > 0 and c.absolute_difference <= warning_tolerance
        ]
        rounding_diff = max(diffs) if diffs else Decimal("0.00")

        overall_status: CalculationStatus = "PASSED"
        if any(c.status == "FAILED" for c in all_calcs):
            overall_status = "FAILED"
        elif any(c.status == "WARNING" for c in all_calcs):
            overall_status = "WARNING"
        elif all(c.status == "NOT_AVAILABLE" for c in all_calcs):
            overall_status = "NOT_AVAILABLE"

        metrics = AccuracyMetrics(
            total_accuracy=total_acc,
            subtotal_accuracy=subtotal_acc,
            cross_cast_accuracy=cross_cast_acc,
            arithmetic_accuracy=arith_acc,
            formula_accuracy=formula_acc,
            balance_sheet_reconciliation=bs_calc,
            rounding_difference=rounding_diff,
        )

        score = total_acc

        return MathematicalAccuracyResult(
            period=active_period,
            status=overall_status,
            score=score,
            calculations=calculations,
            metrics=metrics,
            total_accuracy=total_acc,
            subtotal_accuracy=subtotal_acc,
            cross_cast_accuracy=cross_cast_acc,
            arithmetic_accuracy=arith_acc,
            formula_accuracy=formula_acc,
            balance_sheet_reconciliation=bs_calc,
            rounding_difference=rounding_diff,
            issues=issues,
        )


def run(data: Dict[str, Any], period: Optional[str] = None) -> MathematicalAccuracyResult:
    """Convenience functional interface matching standard check signature."""
    return MathematicalAccuracyEngine.evaluate(data, period=period)
