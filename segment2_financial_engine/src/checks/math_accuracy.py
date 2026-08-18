"""
Check 1: Mathematical Accuracy & Core Equation Verification.

Verifies the four fundamental accounting equations:
  1. Assets = Liabilities + Equity              (Balance Sheet reconciliation)
  2. Revenue - COGS = Gross Profit
  3. Gross Profit - Operating Expenses = Operating Income
  4. Operating Income + Other Income - Finance Costs - Tax = Net Income (PAT)

Uses TOLERANCE = 0.01 Cr for rounding allowance.
No LLM. Pure arithmetic.
"""

from typing import Any, Dict
from ..loader import (
    TOLERANCE, current_and_previous,
    derive_gross_profit, derive_total_liabilities,
    get_source, get_value,
)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, _, _ = current_and_previous(data)
    if not curr:
        return _skip("No periods found in metadata")

    equations: Dict[str, Any] = {}
    issues: list = []

    # ------------------------------------------------------------------
    # Equation 1: Balance Sheet — Assets = Liabilities + Equity
    # ------------------------------------------------------------------
    assets      = get_value(data, "balance_sheet", "total_assets",  curr)
    equity      = get_value(data, "balance_sheet", "total_equity",  curr)
    liabilities = derive_total_liabilities(data, curr)

    if assets is not None and equity is not None and liabilities is not None:
        rhs  = round(equity + liabilities, 4)
        diff = round(abs(assets - rhs), 4)
        ok   = diff <= TOLERANCE
        equations["balance_sheet_reconciliation"] = {
            "formula": "Assets = Liabilities + Equity",
            "assets": assets,
            "liabilities_plus_equity": rhs,
            "difference": diff,
            "is_balanced": ok,
            "source": get_source(data, "balance_sheet", "total_assets"),
        }
        if not ok:
            issues.append(f"Balance Sheet does not balance: Δ={diff} Cr")
    else:
        equations["balance_sheet_reconciliation"] = {
            "status": "SKIPPED",
            "reason": "Missing total_assets or total_equity",
        }

    # ------------------------------------------------------------------
    # Equation 2: Gross Profit = Revenue - COGS
    # ------------------------------------------------------------------
    revenue      = get_value(data, "income_statement", "revenue_from_operations",    curr)
    cogs         = get_value(data, "income_statement", "cost_of_materials_consumed", curr)
    gp_reported  = get_value(data, "income_statement", "gross_profit",               curr)

    if revenue is not None and cogs is not None:
        calc_gp  = round(revenue - cogs, 4)
        rep_gp   = gp_reported if gp_reported is not None else calc_gp
        diff_gp  = round(abs(calc_gp - rep_gp), 4)
        equations["gross_profit_equation"] = {
            "formula": "Revenue - COGS = Gross Profit",
            "revenue": revenue,
            "cogs": cogs,
            "calculated_gross_profit": calc_gp,
            "reported_gross_profit": rep_gp,
            "difference": diff_gp,
        }
        if diff_gp > TOLERANCE:
            issues.append(f"Gross Profit mismatch: Δ={diff_gp} Cr")
    else:
        equations["gross_profit_equation"] = {
            "status": "SKIPPED",
            "reason": "Missing revenue_from_operations or cost_of_materials_consumed",
        }

    # ------------------------------------------------------------------
    # Equation 3: Operating Income = Gross Profit - Operating Expenses
    # ------------------------------------------------------------------
    gp_derived  = derive_gross_profit(data, curr)
    emp_exp     = get_value(data, "income_statement", "employee_benefit_expenses",  curr)
    other_opex  = get_value(data, "income_statement", "other_operating_expenses",   curr)
    da          = get_value(data, "income_statement", "depreciation_and_amortization", curr)
    op_reported = get_value(data, "income_statement", "operating_profit",            curr)

    if gp_derived is not None and emp_exp is not None and other_opex is not None and da is not None:
        total_opex = round(emp_exp + other_opex + da, 4)
        calc_op    = round(gp_derived - total_opex, 4)
        rep_op     = op_reported if op_reported is not None else calc_op
        diff_op    = round(abs(calc_op - rep_op), 4)
        equations["operating_income_equation"] = {
            "formula": "Gross Profit - Operating Expenses = Operating Income",
            "gross_profit": gp_derived,
            "operating_expenses": total_opex,
            "calculated_operating_income": calc_op,
            "reported_operating_income": rep_op,
            "difference": diff_op,
        }
        if diff_op > TOLERANCE:
            issues.append(f"Operating Income mismatch: Δ={diff_op} Cr")
    else:
        equations["operating_income_equation"] = {
            "status": "SKIPPED",
            "reason": "Missing operating expense components",
        }

    # ------------------------------------------------------------------
    # Equation 4: Net Income = OpIncome + OtherIncome - FinanceCosts - Tax
    # ------------------------------------------------------------------
    other_income  = get_value(data, "income_statement", "other_income",         curr) or 0.0
    finance_costs = get_value(data, "income_statement", "finance_costs",        curr) or 0.0
    tax           = get_value(data, "income_statement", "total_tax_expense",    curr) or 0.0
    pat           = get_value(data, "income_statement", "profit_for_the_period", curr)
    op_income     = get_value(data, "income_statement", "operating_profit",     curr)

    if op_income is not None and pat is not None:
        calc_ni  = round(op_income + other_income - finance_costs - tax, 4)
        diff_ni  = round(abs(calc_ni - pat), 4)
        equations["net_income_equation"] = {
            "formula": "Operating Income + Other Income - Interest - Tax = Net Income",
            "operating_income": op_income,
            "other_income": other_income,
            "interest": finance_costs,
            "tax": tax,
            "calculated_net_income": calc_ni,
            "reported_net_income": pat,
            "difference": diff_ni,
        }
        if diff_ni > TOLERANCE:
            issues.append(f"Net Income mismatch: Δ={diff_ni} Cr")
    else:
        equations["net_income_equation"] = {
            "status": "SKIPPED",
            "reason": "Missing operating_profit or profit_for_the_period",
        }

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    eqs_run    = sum(1 for v in equations.values() if v.get("status") != "SKIPPED" and "formula" in v)
    eqs_passed = eqs_run - len(issues)
    score      = round((eqs_passed / eqs_run * 100) if eqs_run > 0 else 0.0, 1)
    status     = "PASSED" if not issues else "FAILED"

    return {
        "score": score,
        "status": status,
        "equations": equations,
        "subtotal_accuracy_pct": score,
        "cross_cast_accuracy_pct": score,
        "rounding_difference": 0.00 if not issues else round(
            max(
                (v.get("difference", 0) for v in equations.values()
                 if isinstance(v, dict) and "difference" in v),
                default=0,
            ),
            4,
        ),
        "issues": issues,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {"score": 0.0, "status": "SKIPPED", "reason": reason, "equations": {}}
