"""
Check 2: Cash Flow Statement Reconciliation Engine.

Verifies:
1. Cash Flow Arithmetic:
   Expected Closing Cash = Opening Cash + Operating CF + Investing CF + Financing CF
   Cash Difference = Expected Closing Cash - Reported Closing Cash
2. Cross-Statement Consistency:
   Balance Sheet Cash <-> Cash Flow Closing Cash

Rules & Guarantees:
- Pure deterministic calculations using Decimal.
- No silent zero assumptions for missing values.
- If required inputs are unavailable -> status = "NOT_AVAILABLE".
- Statuses: RECONCILED, MATCHED, MISMATCH, NOT_AVAILABLE, WARNING.
- Tolerance handling: ABS(diff) <= tolerance.
- Full provenance / source traceability when available.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

CashReconciliationStatus = Literal["RECONCILED", "MISMATCH", "NOT_AVAILABLE", "WARNING", "SKIPPED"]
BSCashMatchStatus = Literal["MATCHED", "MISMATCH", "NOT_AVAILABLE", "WARNING", "SKIPPED"]
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


class CashFlowCheckResult(BaseModel):
    """Complete output of the Cash Flow Reconciliation Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    opening_cash: Optional[Decimal] = None
    operating_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    expected_closing_cash: Optional[Decimal] = None
    reported_closing_cash: Optional[Decimal] = None
    cash_difference: Optional[Decimal] = None
    cash_reconciliation_status: CashReconciliationStatus
    balance_sheet_cash: Optional[Decimal] = None
    balance_sheet_cash_difference: Optional[Decimal] = None
    bs_cash_vs_cf_cash_status: BSCashMatchStatus
    tolerance: Decimal = Decimal("0.01")
    warning_tolerance: Decimal = Decimal("0.05")
    score: float
    status: CheckOverallStatus
    source: Optional[SourceTrace] = None
    sources: Dict[str, Optional[SourceTrace]] = Field(default_factory=dict)
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
# Master Cash Flow Review Engine
# ---------------------------------------------------------------------------

class CashFlowEngine:
    """
    Validates Cash Flow Statement internal reconciliation and BS cash tie-out.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        period: Optional[str] = None,
        tolerance: Decimal = Decimal("0.01"),
        warning_tolerance: Decimal = Decimal("0.05"),
    ) -> CashFlowCheckResult:
        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")
        prev = periods[1] if len(periods) > 1 else None

        # 1. Extract Cash Flow Statement components
        cfo = get_value(data, "cash_flow_statement", "net_cash_from_operating_activities", curr)
        if cfo is None:
            cfo = get_value(data, "cash_flow_statement", "operating_cash_flow", curr)

        cfi = get_value(data, "cash_flow_statement", "net_cash_from_investing_activities", curr)
        if cfi is None:
            cfi = get_value(data, "cash_flow_statement", "investing_cash_flow", curr)

        cff = get_value(data, "cash_flow_statement", "net_cash_from_financing_activities", curr)
        if cff is None:
            cff = get_value(data, "cash_flow_statement", "financing_cash_flow", curr)

        # Reported closing cash from Cash Flow Statement
        reported_cf_closing = get_value(data, "cash_flow_statement", "closing_cash_and_cash_equivalents", curr)
        if reported_cf_closing is None:
            reported_cf_closing = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", curr)
        if reported_cf_closing is None:
            reported_cf_closing = get_value(data, "cash_flow_statement", "closing_cash", curr)

        # Reported closing cash from Balance Sheet
        bs_cash = get_value(data, "balance_sheet", "cash_and_cash_equivalents", curr)
        if bs_cash is None:
            bs_cash = get_value(data, "balance_sheet", "cash", curr)

        # Resolve opening cash: explicit CFS key -> previous period BS cash -> previous period CFS closing cash
        opening_cash = get_value(data, "cash_flow_statement", "opening_cash_and_cash_equivalents", curr)
        if opening_cash is None:
            opening_cash = get_value(data, "cash_flow_statement", "opening_cash", curr)
        if opening_cash is None and prev is not None:
            opening_cash = get_value(data, "balance_sheet", "cash_and_cash_equivalents", prev)
            if opening_cash is None:
                opening_cash = get_value(data, "cash_flow_statement", "closing_cash_and_cash_equivalents", prev)
                if opening_cash is None:
                    opening_cash = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", prev)

        sources = {
            "opening_cash": get_source(data, "cash_flow_statement", "opening_cash_and_cash_equivalents"),
            "operating_cash_flow": get_source(data, "cash_flow_statement", "net_cash_from_operating_activities"),
            "investing_cash_flow": get_source(data, "cash_flow_statement", "net_cash_from_investing_activities"),
            "financing_cash_flow": get_source(data, "cash_flow_statement", "net_cash_from_financing_activities"),
            "reported_closing_cash": get_source(data, "cash_flow_statement", "closing_cash_and_cash_equivalents") or get_source(data, "cash_flow_statement", "cash_and_cash_equivalents"),
            "balance_sheet_cash": get_source(data, "balance_sheet", "cash_and_cash_equivalents"),
        }
        main_source = sources["reported_closing_cash"] or sources["balance_sheet_cash"]

        issues: List[str] = []

        # ------------------------------------------------------------------
        # Part A: Expected Closing Cash = Opening + CFO + CFI + CFF
        # ------------------------------------------------------------------
        expected_closing: Optional[Decimal] = None
        cash_diff: Optional[Decimal] = None
        reconcile_status: CashReconciliationStatus = "NOT_AVAILABLE"

        effective_reported_closing = reported_cf_closing if reported_cf_closing is not None else bs_cash

        required_reconcile = [
            ("opening_cash", opening_cash),
            ("operating_cash_flow", cfo),
            ("investing_cash_flow", cfi),
            ("financing_cash_flow", cff),
            ("reported_closing_cash", effective_reported_closing),
        ]
        missing_reconcile = [name for name, val in required_reconcile if val is None]

        if not missing_reconcile:
            expected_closing = opening_cash + cfo + cfi + cff
            cash_diff = abs(expected_closing - effective_reported_closing)

            if cash_diff <= tolerance:
                reconcile_status = "RECONCILED"
            elif cash_diff <= warning_tolerance:
                reconcile_status = "WARNING"
                issues.append(f"WARNING: Cash Flow reconciliation minor rounding difference: diff={cash_diff} Cr (expected {expected_closing}, reported {effective_reported_closing}).")
            else:
                reconcile_status = "MISMATCH"
                issues.append(f"FAILED: Cash Flow does not reconcile: expected {expected_closing} Cr, reported {effective_reported_closing} Cr (diff={cash_diff} Cr).")
        else:
            reconcile_status = "NOT_AVAILABLE"
            issues.append(f"NOT_AVAILABLE: Missing required Cash Flow components: {', '.join(missing_reconcile)}.")

        # ------------------------------------------------------------------
        # Part B: Balance Sheet Cash <-> Cash Flow Closing Cash
        # ------------------------------------------------------------------
        bs_cash_diff: Optional[Decimal] = None
        bs_cf_status: BSCashMatchStatus = "NOT_AVAILABLE"

        if bs_cash is not None and reported_cf_closing is not None:
            bs_cash_diff = abs(bs_cash - reported_cf_closing)
            if bs_cash_diff <= tolerance:
                bs_cf_status = "MATCHED"
            elif bs_cash_diff <= warning_tolerance:
                bs_cf_status = "WARNING"
                issues.append(f"WARNING: Balance Sheet Cash vs CFS Cash minor rounding difference: diff={bs_cash_diff} Cr.")
            else:
                bs_cf_status = "MISMATCH"
                issues.append(f"FAILED: Balance Sheet Cash ({bs_cash} Cr) does not match Cash Flow Closing Cash ({reported_cf_closing} Cr), diff={bs_cash_diff} Cr.")
        elif bs_cash is not None and reported_cf_closing is None:
            bs_cf_status = "NOT_AVAILABLE"
            issues.append("NOT_AVAILABLE: Cash Flow closing cash is absent to compare with Balance Sheet cash.")
        elif bs_cash is None and reported_cf_closing is not None:
            bs_cf_status = "NOT_AVAILABLE"
            issues.append("NOT_AVAILABLE: Balance Sheet cash is absent to compare with Cash Flow closing cash.")

        # ------------------------------------------------------------------
        # Overall Status & Score
        # ------------------------------------------------------------------
        if reconcile_status == "MISMATCH" or bs_cf_status == "MISMATCH":
            overall_status: CheckOverallStatus = "FAILED"
        elif reconcile_status == "WARNING" or bs_cf_status == "WARNING":
            overall_status = "WARNING"
        elif reconcile_status == "NOT_AVAILABLE":
            overall_status = "NOT_AVAILABLE"
        elif reconcile_status == "RECONCILED" and bs_cf_status in ("MATCHED", "NOT_AVAILABLE", "SKIPPED"):
            overall_status = "PASSED"
        else:
            overall_status = "NOT_AVAILABLE"

        # Score computation
        if overall_status == "PASSED":
            score = 100.0
        elif overall_status == "WARNING":
            score = 85.0
        elif overall_status == "FAILED":
            mismatches = sum(1 for s in [reconcile_status, bs_cf_status] if s == "MISMATCH")
            score = max(0.0, 100.0 - mismatches * 50.0)
        else:
            score = 0.0

        details_parts = []
        if reconcile_status == "RECONCILED":
            details_parts.append("Cash Flow statement arithmetic reconciled successfully.")
        elif reconcile_status == "MISMATCH":
            details_parts.append(f"Cash Flow arithmetic mismatch (diff={cash_diff} Cr).")
        if bs_cf_status == "MATCHED":
            details_parts.append("Balance Sheet cash matches Cash Flow closing cash.")
        elif bs_cf_status == "MISMATCH":
            details_parts.append(f"BS Cash != CF Cash (diff={bs_cash_diff} Cr).")
        details = " ".join(details_parts) if details_parts else "Cash flow evaluation completed."

        return CashFlowCheckResult(
            period=curr,
            opening_cash=opening_cash,
            operating_cash_flow=cfo,
            investing_cash_flow=cfi,
            financing_cash_flow=cff,
            expected_closing_cash=expected_closing,
            reported_closing_cash=effective_reported_closing,
            cash_difference=cash_diff,
            cash_reconciliation_status=reconcile_status,
            balance_sheet_cash=bs_cash,
            balance_sheet_cash_difference=bs_cash_diff,
            bs_cash_vs_cf_cash_status=bs_cf_status,
            tolerance=tolerance,
            warning_tolerance=warning_tolerance,
            score=score,
            status=overall_status,
            source=main_source,
            sources=sources,
            issues=issues,
            details=details,
        )


def run(data: Dict[str, Any], period: Optional[str] = None) -> CashFlowCheckResult:
    return CashFlowEngine.evaluate(data, period=period)
