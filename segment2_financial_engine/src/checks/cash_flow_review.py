"""
Check 2: Cash Flow Statement Reconciliation.

Verifies:
  Opening Cash + CFO + CFI + CFF = Closing Cash (CF statement)
  BS Cash (closing) == CF Cash (closing)

Opening cash is derived from previous period BS/CF if the explicit key is absent.
No LLM. Pure arithmetic.
"""

from typing import Any, Dict
from ..loader import (
    TOLERANCE, current_and_previous,
    derive_opening_cash, get_value, get_source,
)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, prev, _ = current_and_previous(data)
    if not curr:
        return _skip("No periods found in metadata")

    cfo = get_value(data, "cash_flow_statement", "net_cash_from_operating_activities",  curr)
    cfi = get_value(data, "cash_flow_statement", "net_cash_from_investing_activities",  curr)
    cff = get_value(data, "cash_flow_statement", "net_cash_from_financing_activities",  curr)

    # Reported closing cash from CFS
    cf_closing = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", curr)

    # Reported closing cash from Balance Sheet
    bs_closing = get_value(data, "balance_sheet", "cash_and_cash_equivalents", curr)

    # Derive opening cash
    opening = derive_opening_cash(data, curr, prev)

    issues = []

    # ------------------------------------------------------------------
    # Check A: Opening + CFO + CFI + CFF = Closing
    # ------------------------------------------------------------------
    cash_reconciliation_status = "SKIPPED"
    expected_closing            = None
    cash_difference             = None

    if all(v is not None for v in [opening, cfo, cfi, cff]):
        expected_closing = round(opening + cfo + cfi + cff, 4)
        reported_closing = cf_closing if cf_closing is not None else bs_closing

        if reported_closing is not None:
            cash_difference = round(abs(expected_closing - reported_closing), 4)
            cash_reconciliation_status = "RECONCILED" if cash_difference <= TOLERANCE else "MISMATCH"
            if cash_difference > TOLERANCE:
                issues.append(
                    f"Cash flow does not reconcile: expected {expected_closing}, "
                    f"reported {reported_closing}, Δ={cash_difference} Cr"
                )
        else:
            cash_reconciliation_status = "SKIPPED"
    else:
        missing = [
            name for name, v in [
                ("opening_cash", opening),
                ("CFO", cfo), ("CFI", cfi), ("CFF", cff),
            ] if v is None
        ]
        cash_reconciliation_status = "SKIPPED"

    # ------------------------------------------------------------------
    # Check B: BS Cash == CF Closing Cash
    # ------------------------------------------------------------------
    bs_cf_status = "SKIPPED"
    if bs_closing is not None and cf_closing is not None:
        diff_bs_cf = round(abs(bs_closing - cf_closing), 4)
        bs_cf_status = "MATCHED" if diff_bs_cf <= TOLERANCE else "MISMATCH"
        if diff_bs_cf > TOLERANCE:
            issues.append(
                f"BS cash ({bs_closing}) ≠ CF closing cash ({cf_closing}), Δ={diff_bs_cf} Cr"
            )
    elif bs_closing is not None and cf_closing is None:
        bs_cf_status = "SKIPPED"

    score  = 100.0 if not issues else max(0.0, 100.0 - len(issues) * 50.0)
    status = "PASSED" if not issues and cash_reconciliation_status not in ("SKIPPED", "MISMATCH") else (
        "SKIPPED" if cash_reconciliation_status == "SKIPPED" else "FAILED"
    )
    if not issues and cash_reconciliation_status == "RECONCILED":
        status = "PASSED"

    return {
        "score": score,
        "status": status,
        "opening_cash": opening,
        "operating_cash_flow": cfo,
        "investing_cash_flow": cfi,
        "financing_cash_flow": cff,
        "expected_closing_cash": expected_closing,
        "reported_closing_cash": cf_closing or bs_closing,
        "cash_difference": cash_difference,
        "cash_reconciliation_status": cash_reconciliation_status,
        "bs_cash_vs_cf_cash_status": bs_cf_status,
        "issues": issues,
    }


def _skip(reason: str) -> Dict[str, Any]:
    return {
        "score": 0.0, "status": "SKIPPED", "reason": reason,
        "cash_reconciliation_status": "SKIPPED", "bs_cash_vs_cf_cash_status": "SKIPPED",
    }
