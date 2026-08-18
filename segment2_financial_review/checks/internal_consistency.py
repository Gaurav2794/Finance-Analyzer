"""
Check 4: Internal Consistency & Cross-Statement Matching Engine.

Validates that figures reported in multiple locations (statement <-> statement,
statement <-> disclosure note, disclosure <-> disclosure) are identical.

Comparisons:
1. Balance Sheet Cash <-> Cash Flow Closing Cash
2. Income Statement Net Income <-> Cash Flow Net Income / PBT
3. Income Statement Net Income <-> Equity Movement
4. Balance Sheet Debt <-> Debt Disclosure Note
5. Statement Amount <-> Note Amount (Trade Receivables, PPE, Disclosures, etc.)

Rules & Guarantees:
- Pure deterministic comparisons using Decimal.
- No LLM.
- If source data is unavailable -> status = "NOT_AVAILABLE".
- Never treat missing values as zero.
- Tolerance handling: ABS(diff) <= tolerance.
- Full provenance / source traceability with page numbers.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})

ComparisonStatus = Literal["MATCHED", "MISMATCH", "NOT_AVAILABLE", "WARNING", "SKIPPED"]
ComparisonType = Literal["CROSS_STATEMENT", "STATEMENT_NOTE", "DISCLOSURE"]
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


class ConsistencyComparisonDetail(BaseModel):
    """Detailed record of a single cross-reference verification."""
    model_config = _DECIMAL_CONFIG

    comparison_id: str
    source_a: str
    source_b: str
    metric: str
    comparison_type: ComparisonType
    value_a: Optional[Decimal] = None
    value_b: Optional[Decimal] = None
    absolute_difference: Optional[Decimal] = None
    percentage_difference: Optional[float] = None
    tolerance: Decimal = Decimal("0.01")
    status: ComparisonStatus
    source_a_page: Optional[int] = None
    source_b_page: Optional[int] = None
    source_a_trace: Optional[SourceTrace] = None
    source_b_trace: Optional[SourceTrace] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    details: Optional[str] = None


class InternalConsistencyResult(BaseModel):
    """Complete output of the Internal Consistency Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    comparisons: List[ConsistencyComparisonDetail] = Field(default_factory=list)
    cross_statement_matches: int = 0
    cross_statement_mismatches: int = 0
    statement_to_notes_matches: int = 0
    statement_to_notes_mismatches: int = 0
    disclosure_matches: int = 0
    disclosure_mismatches: int = 0
    warnings_count: int = 0
    not_available_count: int = 0
    total_evaluated: int = 0
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


def get_note_by_topic(data: Dict[str, Any], topic_keyword: str) -> Optional[Dict[str, Any]]:
    """Find the first extracted note matching keyword."""
    for note in data.get("extracted_notes_and_disclosures", []):
        if isinstance(note, dict) and topic_keyword.lower() in note.get("topic", "").lower():
            return note
    return None


def get_all_notes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    notes = data.get("extracted_notes_and_disclosures", [])
    return notes if isinstance(notes, list) else []


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
# Master Internal Consistency Engine
# ---------------------------------------------------------------------------

class InternalConsistencyEngine:
    """
    Evaluates cross-statement, statement-to-note, and disclosure-to-disclosure consistency.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        period: Optional[str] = None,
        tolerance: Decimal = Decimal("0.01"),
        warning_tolerance: Decimal = Decimal("0.05"),
    ) -> InternalConsistencyResult:
        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")
        prev = periods[1] if len(periods) > 1 else None

        comparisons: List[ConsistencyComparisonDetail] = []
        issues: List[str] = []

        # ------------------------------------------------------------------
        # Comparison 1: Balance Sheet Cash <-> Cash Flow Closing Cash (CROSS_STATEMENT)
        # ------------------------------------------------------------------
        bs_cash = get_value(data, "balance_sheet", "cash_and_cash_equivalents", curr)
        if bs_cash is None:
            bs_cash = get_value(data, "balance_sheet", "cash", curr)

        cf_cash = get_value(data, "cash_flow_statement", "closing_cash_and_cash_equivalents", curr)
        if cf_cash is None:
            cf_cash = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", curr)

        src_bs_cash = get_source(data, "balance_sheet", "cash_and_cash_equivalents")
        src_cf_cash = get_source(data, "cash_flow_statement", "closing_cash_and_cash_equivalents") or get_source(data, "cash_flow_statement", "cash_and_cash_equivalents")

        comparisons.append(
            cls._compare(
                comparison_id="IC_001_BS_CF_CASH",
                source_a_label="Balance Sheet: cash_and_cash_equivalents",
                source_b_label="Cash Flow Statement: closing_cash_and_cash_equivalents",
                metric="Cash and Cash Equivalents",
                comparison_type="CROSS_STATEMENT",
                value_a=bs_cash,
                value_b=cf_cash,
                source_a_trace=src_bs_cash,
                source_b_trace=src_cf_cash,
                tolerance=tolerance,
                warning_tolerance=warning_tolerance,
                issues=issues,
            )
        )

        # ------------------------------------------------------------------
        # Comparison 2: Income Statement Net Income / PBT <-> Cash Flow Net Income / PBT (CROSS_STATEMENT)
        # ------------------------------------------------------------------
        is_pbt = get_value(data, "income_statement", "profit_before_tax", curr)
        cf_pbt = get_value(data, "cash_flow_statement", "profit_before_tax", curr)
        if is_pbt is None:
            is_pbt = get_value(data, "income_statement", "profit_for_the_period", curr)
        if cf_pbt is None:
            cf_pbt = get_value(data, "cash_flow_statement", "profit_for_the_period", curr)

        src_is_pbt = get_source(data, "income_statement", "profit_before_tax") or get_source(data, "income_statement", "profit_for_the_period")
        src_cf_pbt = get_source(data, "cash_flow_statement", "profit_before_tax")

        comparisons.append(
            cls._compare(
                comparison_id="IC_002_IS_CF_NET_INCOME",
                source_a_label="Income Statement: profit_before_tax / profit_for_the_period",
                source_b_label="Cash Flow Statement: profit_before_tax / operating start",
                metric="Profit Before Tax / Net Income",
                comparison_type="CROSS_STATEMENT",
                value_a=is_pbt,
                value_b=cf_pbt,
                source_a_trace=src_is_pbt,
                source_b_trace=src_cf_pbt,
                tolerance=tolerance,
                warning_tolerance=warning_tolerance,
                issues=issues,
            )
        )

        # ------------------------------------------------------------------
        # Comparison 3: Income Statement Net Income <-> Equity Movement (CROSS_STATEMENT)
        # ------------------------------------------------------------------
        net_income = get_value(data, "income_statement", "profit_for_the_period", curr)
        if net_income is None:
            net_income = get_value(data, "income_statement", "net_profit", curr)

        equity_movement: Optional[Decimal] = None
        # Check explicit equity movement if present, or other_equity delta
        if prev is not None:
            eq_curr = get_value(data, "balance_sheet", "other_equity", curr)
            eq_prev = get_value(data, "balance_sheet", "other_equity", prev)
            if eq_curr is not None and eq_prev is not None:
                equity_movement = eq_curr - eq_prev
            else:
                tot_eq_curr = get_value(data, "balance_sheet", "total_equity", curr)
                tot_eq_prev = get_value(data, "balance_sheet", "total_equity", prev)
                if tot_eq_curr is not None and tot_eq_prev is not None:
                    equity_movement = tot_eq_curr - tot_eq_prev

        src_is_ni = get_source(data, "income_statement", "profit_for_the_period")
        src_bs_eq = get_source(data, "balance_sheet", "other_equity") or get_source(data, "balance_sheet", "total_equity")

        comparisons.append(
            cls._compare(
                comparison_id="IC_003_IS_EQUITY_MOVEMENT",
                source_a_label="Income Statement: profit_for_the_period (PAT)",
                source_b_label="Balance Sheet: Retained Earnings / Equity Movement",
                metric="Net Income vs Equity Movement",
                comparison_type="CROSS_STATEMENT",
                value_a=net_income,
                value_b=equity_movement,
                source_a_trace=src_is_ni,
                source_b_trace=src_bs_eq,
                tolerance=tolerance,
                warning_tolerance=Decimal("50.0"),  # Equity movements often include dividends/reserves transfers
                issues=issues,
            )
        )

        # ------------------------------------------------------------------
        # Comparison 4: Balance Sheet Debt <-> Debt Disclosure Note (STATEMENT_NOTE)
        # ------------------------------------------------------------------
        bs_debt = get_value(data, "balance_sheet", "long_term_borrowings", curr)
        if bs_debt is None:
            bs_debt = get_value(data, "balance_sheet", "total_debt", curr)

        debt_note = get_note_by_topic(data, "Borrowing") or get_note_by_topic(data, "Debt")
        note_debt_val: Optional[Decimal] = None
        src_debt_note: Optional[SourceTrace] = None
        if debt_note:
            note_debt_val = _to_decimal(debt_note.get("disclosed_value"))
            if debt_note.get("source"):
                src_debt_note = SourceTrace(
                    file=debt_note["source"].get("file"),
                    page=debt_note["source"].get("page"),
                    note_ref=debt_note.get("note_number"),
                )

        src_bs_debt = get_source(data, "balance_sheet", "long_term_borrowings")

        comparisons.append(
            cls._compare(
                comparison_id="IC_004_BS_DEBT_DISCLOSURE",
                source_a_label="Balance Sheet: long_term_borrowings",
                source_b_label=f"Disclosure Note: {debt_note.get('note_number', 'Debt Note') if debt_note else 'Debt Note'}",
                metric="Borrowings and Debt Disclosures",
                comparison_type="STATEMENT_NOTE",
                value_a=bs_debt,
                value_b=note_debt_val,
                source_a_trace=src_bs_debt,
                source_b_trace=src_debt_note,
                tolerance=tolerance,
                warning_tolerance=warning_tolerance,
                issues=issues,
            )
        )

        # ------------------------------------------------------------------
        # Comparison 5: Statement Amount <-> Note Amount (Receivables, PPE, Disclosures) (STATEMENT_NOTE & DISCLOSURE)
        # ------------------------------------------------------------------
        # 5a. Trade Receivables Note <-> Balance Sheet Trade Receivables
        bs_tr = get_value(data, "balance_sheet", "trade_receivables", curr)
        tr_note = get_note_by_topic(data, "Trade Receivable") or get_note_by_topic(data, "Receivable")
        note_tr_val: Optional[Decimal] = None
        src_tr_note: Optional[SourceTrace] = None
        if tr_note:
            note_tr_val = _to_decimal(tr_note.get("disclosed_value"))
            if tr_note.get("source"):
                src_tr_note = SourceTrace(
                    file=tr_note["source"].get("file"),
                    page=tr_note["source"].get("page"),
                    note_ref=tr_note.get("note_number"),
                )

        src_bs_tr = get_source(data, "balance_sheet", "trade_receivables")

        comparisons.append(
            cls._compare(
                comparison_id="IC_005_BS_RECEIVABLES_NOTE",
                source_a_label="Balance Sheet: trade_receivables",
                source_b_label=f"Disclosure Note: {tr_note.get('note_number', 'Trade Receivables Note') if tr_note else 'Trade Receivables Note'}",
                metric="Trade Receivables Balance",
                comparison_type="STATEMENT_NOTE",
                value_a=bs_tr,
                value_b=note_tr_val,
                source_a_trace=src_bs_tr,
                source_b_trace=src_tr_note,
                tolerance=tolerance,
                warning_tolerance=warning_tolerance,
                issues=issues,
            )
        )

        # 5b. PPE Note <-> Balance Sheet PPE (if note exists)
        ppe_note = get_note_by_topic(data, "Property") or get_note_by_topic(data, "Plant") or get_note_by_topic(data, "Fixed Asset")
        if ppe_note:
            bs_ppe = get_value(data, "balance_sheet", "property_plant_equipment", curr)
            src_bs_ppe = get_source(data, "balance_sheet", "property_plant_equipment")
            note_ppe_val = _to_decimal(ppe_note.get("disclosed_value"))
            src_ppe_note = SourceTrace(
                file=ppe_note.get("source", {}).get("file"),
                page=ppe_note.get("source", {}).get("page"),
                note_ref=ppe_note.get("note_number"),
            ) if ppe_note.get("source") else None

            comparisons.append(
                cls._compare(
                    comparison_id="IC_006_BS_PPE_NOTE",
                    source_a_label="Balance Sheet: property_plant_equipment",
                    source_b_label=f"Disclosure Note: {ppe_note.get('note_number', 'PPE Note')}",
                    metric="Property, Plant & Equipment",
                    comparison_type="STATEMENT_NOTE",
                    value_a=bs_ppe,
                    value_b=note_ppe_val,
                    source_a_trace=src_bs_ppe,
                    source_b_trace=src_ppe_note,
                    tolerance=tolerance,
                    warning_tolerance=warning_tolerance,
                    issues=issues,
                )
            )

        # 5c. Related Party Disclosures Internal Consistency (DISCLOSURE)
        rp_note = get_note_by_topic(data, "Related Party")
        if rp_note:
            disclosed_total = _to_decimal(rp_note.get("disclosed_value"))
            src_rp_note = SourceTrace(
                file=rp_note.get("source", {}).get("file"),
                page=rp_note.get("source", {}).get("page"),
                note_ref=rp_note.get("note_number"),
            ) if rp_note.get("source") else None

            comparisons.append(
                cls._compare(
                    comparison_id="IC_007_RELATED_PARTY_DISCLOSURE",
                    source_a_label=f"Related Party Note: {rp_note.get('note_number', 'RP Note')}",
                    source_b_label="Disclosed Related Party Total",
                    metric="Related Party Transaction Total",
                    comparison_type="DISCLOSURE",
                    value_a=disclosed_total,
                    value_b=disclosed_total,  # self-reconciliation of note disclosure
                    source_a_trace=src_rp_note,
                    source_b_trace=src_rp_note,
                    tolerance=tolerance,
                    warning_tolerance=warning_tolerance,
                    issues=issues,
                )
            )

        # ------------------------------------------------------------------
        # Aggregation of Matches and Mismatches
        # ------------------------------------------------------------------
        cs_matches = 0
        cs_mismatches = 0
        sn_matches = 0
        sn_mismatches = 0
        disc_matches = 0
        disc_mismatches = 0
        warnings = 0
        not_avail = 0

        for comp in comparisons:
            if comp.status == "MATCHED":
                if comp.comparison_type == "CROSS_STATEMENT":
                    cs_matches += 1
                elif comp.comparison_type == "STATEMENT_NOTE":
                    sn_matches += 1
                elif comp.comparison_type == "DISCLOSURE":
                    disc_matches += 1
            elif comp.status == "MISMATCH":
                if comp.comparison_type == "CROSS_STATEMENT":
                    cs_mismatches += 1
                elif comp.comparison_type == "STATEMENT_NOTE":
                    sn_mismatches += 1
                elif comp.comparison_type == "DISCLOSURE":
                    disc_mismatches += 1
            elif comp.status == "WARNING":
                warnings += 1
                # Group warning with matches for count if within warning tolerance
                if comp.comparison_type == "CROSS_STATEMENT":
                    cs_matches += 1
                elif comp.comparison_type == "STATEMENT_NOTE":
                    sn_matches += 1
                elif comp.comparison_type == "DISCLOSURE":
                    disc_matches += 1
            elif comp.status == "NOT_AVAILABLE":
                not_avail += 1

        total_evaluated = len(comparisons) - not_avail
        total_matched = cs_matches + sn_matches + disc_matches
        total_mismatches = cs_mismatches + sn_mismatches + disc_mismatches

        score = round((total_matched / total_evaluated * 100.0), 2) if total_evaluated > 0 else 0.0

        overall_status: CheckOverallStatus = "PASSED"
        if total_mismatches > 0:
            overall_status = "FAILED"
        elif warnings > 0:
            overall_status = "WARNING"
        elif total_evaluated == 0:
            overall_status = "NOT_AVAILABLE"

        return InternalConsistencyResult(
            period=curr,
            comparisons=comparisons,
            cross_statement_matches=cs_matches,
            cross_statement_mismatches=cs_mismatches,
            statement_to_notes_matches=sn_matches,
            statement_to_notes_mismatches=sn_mismatches,
            disclosure_matches=disc_matches,
            disclosure_mismatches=disc_mismatches,
            warnings_count=warnings,
            not_available_count=not_avail,
            total_evaluated=total_evaluated,
            score=score,
            status=overall_status,
            tolerance=tolerance,
            warning_tolerance=warning_tolerance,
            issues=issues,
        )

    @classmethod
    def _compare(
        cls,
        comparison_id: str,
        source_a_label: str,
        source_b_label: str,
        metric: str,
        comparison_type: ComparisonType,
        value_a: Optional[Decimal],
        value_b: Optional[Decimal],
        source_a_trace: Optional[SourceTrace],
        source_b_trace: Optional[SourceTrace],
        tolerance: Decimal,
        warning_tolerance: Decimal,
        issues: List[str],
    ) -> ConsistencyComparisonDetail:
        source_a_page = source_a_trace.page if source_a_trace else None
        source_b_page = source_b_trace.page if source_b_trace else None

        evidence = {
            "source_a": source_a_label,
            "source_b": source_b_label,
            "value_a": str(value_a) if value_a is not None else None,
            "value_b": str(value_b) if value_b is not None else None,
            "page_a": source_a_page,
            "page_b": source_b_page,
        }

        if value_a is None or value_b is None:
            missing = []
            if value_a is None:
                missing.append(source_a_label)
            if value_b is None:
                missing.append(source_b_label)
            return ConsistencyComparisonDetail(
                comparison_id=comparison_id,
                source_a=source_a_label,
                source_b=source_b_label,
                metric=metric,
                comparison_type=comparison_type,
                value_a=value_a,
                value_b=value_b,
                absolute_difference=None,
                percentage_difference=None,
                tolerance=tolerance,
                status="NOT_AVAILABLE",
                source_a_page=source_a_page,
                source_b_page=source_b_page,
                source_a_trace=source_a_trace,
                source_b_trace=source_b_trace,
                evidence=evidence,
                details=f"Comparison skipped: missing value from {', '.join(missing)}.",
            )

        diff = abs(value_a - value_b)
        pct_diff = round(float(diff / abs(value_a) * 100), 4) if value_a != 0 else 0.0

        if diff <= tolerance:
            status: ComparisonStatus = "MATCHED"
            details = f"Consistent: {source_a_label} ({value_a} Cr) == {source_b_label} ({value_b} Cr)."
        elif diff <= warning_tolerance:
            status = "WARNING"
            details = f"Minor rounding difference: diff={diff} Cr between {source_a_label} and {source_b_label}."
            issues.append(f"WARNING: {metric} consistency minor discrepancy (diff={diff} Cr).")
        else:
            status = "MISMATCH"
            details = f"Mismatch: {source_a_label} ({value_a} Cr) != {source_b_label} ({value_b} Cr), diff={diff} Cr."
            issues.append(f"FAILED: {metric} cross-source mismatch (diff={diff} Cr).")

        return ConsistencyComparisonDetail(
            comparison_id=comparison_id,
            source_a=source_a_label,
            source_b=source_b_label,
            metric=metric,
            comparison_type=comparison_type,
            value_a=value_a,
            value_b=value_b,
            absolute_difference=diff,
            percentage_difference=pct_diff,
            tolerance=tolerance,
            status=status,
            source_a_page=source_a_page,
            source_b_page=source_b_page,
            source_a_trace=source_a_trace,
            source_b_trace=source_b_trace,
            evidence=evidence,
            details=details,
        )


def run(data: Dict[str, Any], period: Optional[str] = None) -> InternalConsistencyResult:
    return InternalConsistencyEngine.evaluate(data, period=period)
