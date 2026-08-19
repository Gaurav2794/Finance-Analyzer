"""
Finding Engine — Team 2 Master Orchestrator.

Runs all check and analytics engines against a structured financial data dict,
converts every failed / warning check into a standardised Finding, and returns
the canonical Team 2 output contract:

{
    "checks":             { ... },   # GROUP 1 – CHECK RESULTS
    "financial_metrics":  { ... },   # GROUP 2 – FINANCIAL METRICS (raw engine output)
    "analytical_metrics": { ... },   # GROUP 3 – ANALYTICAL METRICS
    "findings": {                    # GROUP 4 – FINDINGS + SCORE
        "critical": 0,
        "high":     0,
        "review":   0,
        "passed":   0,
        "details":  []
    },
    "overall_score":  0.0,
    "overall_status": ""
}

Rules:
    - Deterministic and reproducible.
    - No LLM calls.
    - A high score cannot hide a CRITICAL finding.
    - Missing engine data -> NOT_AVAILABLE; never assumed zero.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from segment2_financial_review.findings.severity import classify, FindingSeverity
from segment2_financial_review.findings.scoring import compute_overall_score


_DECIMAL_CONFIG = ConfigDict(json_encoders={Decimal: str})


# ─────────────────────────────────────────────────────────────────────────────
# Finding Schema
# ─────────────────────────────────────────────────────────────────────────────

class Finding(BaseModel):
    """Standardised finding produced from any failed or warning check."""
    model_config = _DECIMAL_CONFIG

    finding_id:         str
    category:           str
    severity:           FindingSeverity
    title:              str
    description:        str
    metric:             Optional[str]           = None
    current_value:      Optional[Decimal]       = None
    previous_value:     Optional[Decimal]       = None
    change:             Optional[Decimal]       = None
    change_percentage:  Optional[float]         = None
    threshold:          Optional[float]         = None
    financial_impact:   Optional[str]           = None
    source:             Optional[str]           = None
    page:               Optional[int]           = None
    evidence:           Optional[str]           = None
    recommended_action: str                     = ""
    status:             str                     = "OPEN"   # OPEN | ACCEPTED | CLOSED


class FindingsSummary(BaseModel):
    """GROUP 4 — FINDINGS + SCORE."""
    model_config = _DECIMAL_CONFIG

    critical: int                       = 0
    high:     int                       = 0
    review:   int                       = 0
    passed:   int                       = 0
    details:  List[Finding]             = Field(default_factory=list)


def _new_id(prefix: str = "F") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _decimal_or_none(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Individual finding builders (one per engine)
# ─────────────────────────────────────────────────────────────────────────────

def _findings_from_mathematical_accuracy(result: Any) -> Tuple[List[Finding], float]:
    """Convert MathematicalAccuracyResult -> findings, category_score."""
    findings: List[Finding] = []

    if result is None:
        sev, action = classify("MATHEMATICAL_ACCURACY", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("MA"),
            category="MATHEMATICAL_ACCURACY",
            severity=sev,
            title="Mathematical Accuracy Data Unavailable",
            description="Mathematical accuracy checks could not be performed — engine returned no result.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0
    status_str = str(getattr(result, "status", "NOT_AVAILABLE")).upper()

    # Drill into individual calculations
    calculations = getattr(result, "calculations", {}) or {}
    for calc_id, detail in calculations.items():
        d_status = str(getattr(detail, "status", "NOT_AVAILABLE")).upper()
        if d_status in ("PASSED", "NOT_AVAILABLE"):
            # Emit a PASSED finding for PASSED; skip NOT_AVAILABLE silently
            if d_status == "PASSED":
                sev, action = classify("MATHEMATICAL_ACCURACY", "PASSED")
                findings.append(Finding(
                    finding_id=_new_id("MA"),
                    category="MATHEMATICAL_ACCURACY",
                    severity=sev,
                    title=f"[PASSED] {getattr(detail, 'check_name', calc_id)}",
                    description=getattr(detail, "details", "") or f"{getattr(detail, 'check_name', calc_id)} verified.",
                    metric=calc_id,
                    current_value=_decimal_or_none(getattr(detail, "calculated_value", None)),
                    recommended_action=action,
                    status="CLOSED",
                ))
            continue

        trigger = d_status  # "FAILED" or "WARNING"
        sev, action = classify("MATHEMATICAL_ACCURACY", trigger)

        abs_diff = _decimal_or_none(getattr(detail, "absolute_difference", None))
        pct_diff = getattr(detail, "percentage_difference", None)

        findings.append(Finding(
            finding_id=_new_id("MA"),
            category="MATHEMATICAL_ACCURACY",
            severity=sev,
            title=f"[{sev}] {getattr(detail, 'check_name', calc_id)} — {d_status}",
            description=(
                getattr(detail, "details", None) or
                f"Equation '{getattr(detail, 'formula', calc_id)}' failed. "
                f"Calculated: {getattr(detail, 'calculated_value', 'N/A')}, "
                f"Reported: {getattr(detail, 'reported_value', 'N/A')}, "
                f"Difference: {abs_diff}."
            ),
            metric=getattr(detail, "check_name", calc_id),
            current_value=_decimal_or_none(getattr(detail, "reported_value", None)),
            change=abs_diff,
            change_percentage=float(pct_diff) if pct_diff is not None else None,
            evidence=getattr(detail, "formula", None),
            recommended_action=action,
        ))

    if not findings:
        sev, action = classify("MATHEMATICAL_ACCURACY", status_str)
        findings.append(Finding(
            finding_id=_new_id("MA"),
            category="MATHEMATICAL_ACCURACY",
            severity=sev,
            title=f"Mathematical Accuracy — {status_str}",
            description=f"Overall status: {status_str}. Score: {score:.1f}.",
            recommended_action=action,
        ))

    return findings, float(score)


def _findings_from_cash_flow(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("CASH_FLOW", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("CF"),
            category="CASH_FLOW",
            severity=sev,
            title="Cash Flow Data Unavailable",
            description="Cash flow reconciliation could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0

    # CFS arithmetic reconciliation
    cf_status = str(getattr(result, "cash_reconciliation_status", "NOT_AVAILABLE")).upper()
    cash_diff = _decimal_or_none(getattr(result, "cash_difference", None))

    if cf_status in ("MISMATCH", "WARNING"):
        trigger = "MISMATCH" if cf_status == "MISMATCH" else "WARNING"
        sev, action = classify("CASH_FLOW", trigger)
        findings.append(Finding(
            finding_id=_new_id("CF"),
            category="CASH_FLOW",
            severity=sev,
            title=f"[{sev}] Cash Flow Arithmetic Mismatch",
            description=(
                f"Expected Closing Cash does not reconcile with Reported Closing Cash. "
                f"Difference: {cash_diff} Cr. "
                f"Formula: Opening + CFO + CFI + CFF = Expected Closing."
            ),
            metric="cash_reconciliation",
            change=cash_diff,
            recommended_action=action,
        ))
    else:
        sev, action = classify("CASH_FLOW", "PASSED")
        findings.append(Finding(
            finding_id=_new_id("CF"),
            category="CASH_FLOW",
            severity=sev,
            title="[PASSED] Cash Flow Arithmetic Reconciled",
            description="Opening + CFO + CFI + CFF = Reported Closing Cash — verified.",
            metric="cash_reconciliation",
            status="CLOSED",
            recommended_action=action,
        ))

    # BS cash vs CFS cash cross-check
    bs_cf_status = str(getattr(result, "bs_cash_vs_cf_cash_status", "NOT_AVAILABLE")).upper()
    bs_diff = _decimal_or_none(getattr(result, "balance_sheet_cash_difference", None))

    if bs_cf_status in ("MISMATCH", "WARNING"):
        trigger = "MISMATCH" if bs_cf_status == "MISMATCH" else "WARNING"
        sev, action = classify("CASH_FLOW", trigger)
        findings.append(Finding(
            finding_id=_new_id("CF"),
            category="CASH_FLOW",
            severity=sev,
            title=f"[{sev}] Balance Sheet Cash vs Cash Flow Statement Mismatch",
            description=(
                f"Cash reported on the Balance Sheet differs from the Closing Cash "
                f"on the Cash Flow Statement by {bs_diff} Cr."
            ),
            metric="bs_vs_cf_cash",
            change=bs_diff,
            recommended_action=action,
        ))

    return findings, float(score)


def _findings_from_prior_year_tieout(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("PRIOR_YEAR_TIEOUT", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("PY"),
            category="PRIOR_YEAR_TIEOUT",
            severity=sev,
            title="Prior Year Tie-Out Data Unavailable",
            description="Prior year tie-out checks could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0

    items = getattr(result, "items", []) or []
    for item in items:
        item_status = str(getattr(item, "tie_out_status", "NOT_AVAILABLE")).upper()
        if item_status in ("NOT_AVAILABLE", "SKIPPED"):
            continue
        if item_status in ("MISMATCH", "WARNING"):
            trigger = "FAILED" if item_status == "MISMATCH" else "WARNING"
            sev, action = classify("PRIOR_YEAR_TIEOUT", trigger)
            abs_diff = _decimal_or_none(getattr(item, "absolute_difference", None))
            pct_diff = getattr(item, "percentage_difference", None)
            findings.append(Finding(
                finding_id=_new_id("PY"),
                category="PRIOR_YEAR_TIEOUT",
                severity=sev,
                title=f"[{sev}] Prior Year Tie-Out — {getattr(item, 'line_item', 'Unknown')} Mismatch",
                description=(
                    f"Opening balance for '{getattr(item, 'line_item', 'Unknown')}' "
                    f"({getattr(item, 'opening_balance', 'N/A')} Cr) does not match prior year "
                    f"closing ({getattr(item, 'previous_closing_balance', 'N/A')} Cr). "
                    f"Difference: {abs_diff} Cr ({pct_diff:.2f}%)."
                    if pct_diff is not None else
                    f"Opening balance for '{getattr(item, 'line_item', 'Unknown')}' "
                    f"does not match prior year closing. Difference: {abs_diff} Cr."
                ),
                metric=getattr(item, "line_item", None),
                current_value=_decimal_or_none(getattr(item, "opening_balance", None)),
                previous_value=_decimal_or_none(getattr(item, "previous_closing_balance", None)),
                change=abs_diff,
                change_percentage=float(pct_diff) if pct_diff is not None else None,
                recommended_action=action,
            ))
        elif item_status == "MATCHED":
            sev, action = classify("PRIOR_YEAR_TIEOUT", "PASSED")
            findings.append(Finding(
                finding_id=_new_id("PY"),
                category="PRIOR_YEAR_TIEOUT",
                severity=sev,
                title=f"[PASSED] Prior Year Tie-Out — {getattr(item, 'line_item', 'Unknown')}",
                description=f"Opening balance ties out with prior year closing.",
                metric=getattr(item, "line_item", None),
                status="CLOSED",
                recommended_action=action,
            ))

    if not findings:
        overall_status = str(getattr(result, "status", "NOT_AVAILABLE")).upper()
        sev, action = classify("PRIOR_YEAR_TIEOUT", overall_status if overall_status in ("PASSED", "FAILED", "WARNING", "NOT_AVAILABLE") else "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("PY"),
            category="PRIOR_YEAR_TIEOUT",
            severity=sev,
            title=f"Prior Year Tie-Out — {overall_status}",
            description=f"Overall status: {overall_status}. Score: {score:.1f}.",
            recommended_action=action,
            status="CLOSED" if sev == "PASSED" else "OPEN",
        ))

    return findings, float(score)


def _findings_from_internal_consistency(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("INTERNAL_CONSISTENCY", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("IC"),
            category="INTERNAL_CONSISTENCY",
            severity=sev,
            title="Internal Consistency Data Unavailable",
            description="Internal consistency checks could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0

    comparisons = getattr(result, "comparisons", []) or []
    for comp in comparisons:
        c_status = str(getattr(comp, "status", "NOT_AVAILABLE")).upper()
        if c_status in ("NOT_AVAILABLE", "SKIPPED"):
            continue
        if c_status in ("MISMATCH", "WARNING"):
            trigger = "FAILED" if c_status == "MISMATCH" else "WARNING"
            sev, action = classify("INTERNAL_CONSISTENCY", trigger)
            abs_diff = _decimal_or_none(getattr(comp, "absolute_difference", None))
            pct_diff = getattr(comp, "percentage_difference", None)
            src_a = getattr(comp, "source_a", "Source A")
            src_b = getattr(comp, "source_b", "Source B")
            metric = getattr(comp, "metric", "Unknown")
            findings.append(Finding(
                finding_id=_new_id("IC"),
                category="INTERNAL_CONSISTENCY",
                severity=sev,
                title=f"[{sev}] Cross-Statement Mismatch — {metric}",
                description=(
                    f"'{metric}' value in {src_a} "
                    f"({getattr(comp, 'value_a', 'N/A')} Cr) does not match "
                    f"{src_b} ({getattr(comp, 'value_b', 'N/A')} Cr). "
                    f"Difference: {abs_diff} Cr."
                ),
                metric=metric,
                current_value=_decimal_or_none(getattr(comp, "value_a", None)),
                previous_value=_decimal_or_none(getattr(comp, "value_b", None)),
                change=abs_diff,
                change_percentage=float(pct_diff) if pct_diff is not None else None,
                source=src_a,
                page=getattr(comp, "source_a_page", None),
                evidence=f"{src_a} vs {src_b}",
                recommended_action=action,
            ))
        elif c_status == "MATCHED":
            sev, action = classify("INTERNAL_CONSISTENCY", "PASSED")
            metric = getattr(comp, "metric", "Unknown")
            findings.append(Finding(
                finding_id=_new_id("IC"),
                category="INTERNAL_CONSISTENCY",
                severity=sev,
                title=f"[PASSED] Cross-Statement Match — {metric}",
                description=f"'{metric}' values are consistent across sources.",
                metric=metric,
                status="CLOSED",
                recommended_action=action,
            ))

    if not findings:
        overall_status = str(getattr(result, "status", "NOT_AVAILABLE")).upper()
        sev, action = classify("INTERNAL_CONSISTENCY", overall_status if overall_status in ("PASSED", "FAILED", "WARNING", "NOT_AVAILABLE") else "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("IC"),
            category="INTERNAL_CONSISTENCY",
            severity=sev,
            title=f"Internal Consistency — {overall_status}",
            description=f"Overall status: {overall_status}. Score: {score:.1f}.",
            recommended_action=action,
            status="CLOSED" if sev == "PASSED" else "OPEN",
        ))

    return findings, float(score)


def _findings_from_growth(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("ANALYTICAL_COMPARISON", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("AC"),
            category="ANALYTICAL_COMPARISON",
            severity=sev,
            title="Analytical Comparison Data Unavailable",
            description="YoY growth analysis could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 100.0
    overall_status = str(getattr(result, "status", "PASSED")).upper()
    sev, action = classify("ANALYTICAL_COMPARISON", overall_status if overall_status in ("PASSED", "WARNING", "NOT_AVAILABLE") else "PASSED")
    findings.append(Finding(
        finding_id=_new_id("AC"),
        category="ANALYTICAL_COMPARISON",
        severity=sev,
        title=f"Analytical Comparison — {overall_status}",
        description=(
            f"YoY growth computed for {getattr(result, 'total_metrics_evaluated', 0)} metrics. "
            f"{getattr(result, 'metrics_computed', 0)} computed, "
            f"{getattr(result, 'not_available_count', 0)} not available."
        ),
        recommended_action=action,
        status="CLOSED" if sev == "PASSED" else "OPEN",
    ))
    return findings, float(score)


def _findings_from_ratios(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("RATIOS", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("RT"),
            category="RATIOS",
            severity=sev,
            title="Ratios Data Unavailable",
            description="Financial ratios could not be computed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 100.0
    overall_status = str(getattr(result, "status", "PASSED")).upper()
    computed = getattr(result, "ratios_computed_count", 0)
    sev, action = classify("RATIOS", overall_status if overall_status in ("PASSED", "WARNING", "NOT_AVAILABLE") else "PASSED")
    findings.append(Finding(
        finding_id=_new_id("RT"),
        category="RATIOS",
        severity=sev,
        title=f"Financial Ratios — {overall_status}",
        description=f"{computed} financial ratios evaluated across Liquidity, Leverage, Profitability and Efficiency.",
        recommended_action=action,
        status="CLOSED" if sev == "PASSED" else "OPEN",
    ))
    return findings, float(score)


def _findings_from_unusual_fluctuation(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("UNUSUAL_FLUCTUATION", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("UF"),
            category="UNUSUAL_FLUCTUATION",
            severity=sev,
            title="Unusual Fluctuation Data Unavailable",
            description="Unusual fluctuation analysis could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0

    items = getattr(result, "items", []) or []
    for item in items:
        item_sev = str(getattr(item, "severity", "NOT_AVAILABLE")).upper()
        if item_sev in ("PASSED", "NOT_AVAILABLE"):
            if item_sev == "PASSED":
                sev, action = classify("UNUSUAL_FLUCTUATION", "PASSED")
                findings.append(Finding(
                    finding_id=_new_id("UF"),
                    category="UNUSUAL_FLUCTUATION",
                    severity=sev,
                    title=f"[PASSED] {getattr(item, 'metric', 'Unknown')} — Normal Fluctuation",
                    description=getattr(item, "note", "") or f"No unusual fluctuation detected.",
                    metric=getattr(item, "canonical_key", None),
                    current_value=_decimal_or_none(getattr(item, "current_value", None)),
                    previous_value=_decimal_or_none(getattr(item, "previous_value", None)),
                    change_percentage=getattr(item, "change_pct", None),
                    threshold=getattr(item, "threshold_pct", None),
                    status="CLOSED",
                    recommended_action=action,
                ))
            continue

        # HIGH or REVIEW
        trigger = item_sev  # "HIGH" or "REVIEW"
        sev, action = classify("UNUSUAL_FLUCTUATION", trigger)
        findings.append(Finding(
            finding_id=_new_id("UF"),
            category="UNUSUAL_FLUCTUATION",
            severity=sev,
            title=f"[{sev}] Unusual Fluctuation — {getattr(item, 'metric', 'Unknown')}",
            description=getattr(item, "note", "") or (
                f"{getattr(item, 'metric', 'Unknown')} changed by "
                f"{getattr(item, 'change_pct', 'N/A')}%, exceeding threshold "
                f"of {getattr(item, 'threshold_pct', 'N/A')}%."
            ),
            metric=getattr(item, "canonical_key", None),
            current_value=_decimal_or_none(getattr(item, "current_value", None)),
            previous_value=_decimal_or_none(getattr(item, "previous_value", None)),
            change_percentage=getattr(item, "change_pct", None),
            threshold=getattr(item, "threshold_pct", None),
            recommended_action=action,
        ))

    if not findings:
        sev, action = classify("UNUSUAL_FLUCTUATION", "PASSED")
        findings.append(Finding(
            finding_id=_new_id("UF"),
            category="UNUSUAL_FLUCTUATION",
            severity=sev,
            title="Unusual Fluctuation — All Metrics Passed",
            description="No unusual fluctuations detected across all 15 metrics.",
            status="CLOSED",
            recommended_action=action,
        ))

    return findings, float(score)


def _findings_from_unusual_gain(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("UNUSUAL_GAIN", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("UG"),
            category="UNUSUAL_GAIN",
            severity=sev,
            title="Unusual Gain Data Unavailable",
            description="Unusual gain analysis could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0
    trigger_status = str(getattr(result, "divergence_trigger_status", "INSUFFICIENT_DATA")).upper()
    overall_status = str(getattr(result, "status", "NOT_AVAILABLE")).upper()

    # Map trigger to classify() key
    trigger_key = "ELEVATED" if trigger_status == "ELEVATED" else (
        "NOT_AVAILABLE" if trigger_status == "INSUFFICIENT_DATA" else "NORMAL"
    )
    sev, action = classify("UNUSUAL_GAIN", trigger_key)

    divergence = getattr(result, "profit_vs_revenue_divergence_pp", None)
    findings.append(Finding(
        finding_id=_new_id("UG"),
        category="UNUSUAL_GAIN",
        severity=sev,
        title=f"[{sev}] Profit vs Revenue Divergence — {trigger_status}",
        description=(
            getattr(result, "details", None) or (
                f"Profit growth: {getattr(result, 'profit_growth_pct', 'N/A')}%, "
                f"Revenue growth: {getattr(result, 'revenue_growth_pct', 'N/A')}%, "
                f"Divergence: {divergence} pp."
            )
        ),
        metric="profit_vs_revenue_divergence",
        change_percentage=float(divergence) if divergence is not None else None,
        threshold=getattr(result, "divergence_threshold_pp", None),
        financial_impact=(
            f"Other Income: {getattr(result, 'gain_amount', 'N/A')} Cr "
            f"({getattr(result, 'gain_to_profit_pct', 'N/A')}% of profit)."
        ),
        recommended_action=action,
        status="CLOSED" if sev == "PASSED" else "OPEN",
    ))
    return findings, float(score)


def _findings_from_related_disclosure(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("RELATED_DISCLOSURE", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("RD"),
            category="RELATED_DISCLOSURE",
            severity=sev,
            title="Related Party Disclosure Data Unavailable",
            description="Related party disclosure review could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0
    overall_status = str(getattr(result, "status", "NOT_AVAILABLE")).upper()

    trigger = overall_status if overall_status in ("PASSED", "WARNING", "NOT_AVAILABLE") else "NOT_AVAILABLE"
    sev, action = classify("RELATED_DISCLOSURE", trigger)

    disc_diff = _decimal_or_none(getattr(result, "disclosure_difference", None))
    consistency = getattr(result, "disclosure_consistency_pct", None)

    findings.append(Finding(
        finding_id=_new_id("RD"),
        category="RELATED_DISCLOSURE",
        severity=sev,
        title=f"[{sev}] Related Party Disclosures — {overall_status}",
        description=(
            getattr(result, "details", None) or (
                f"Disclosure Consistency: {consistency}%. "
                f"Difference: {disc_diff} Cr. "
                f"Note Reference: {getattr(result, 'note_reference', 'N/A')}."
            )
        ),
        metric="disclosure_consistency_pct",
        change=disc_diff,
        change_percentage=float(100.0 - consistency) if consistency is not None else None,
        threshold=100.0,
        evidence=getattr(result, "note_reference", None),
        recommended_action=action,
        status="CLOSED" if sev == "PASSED" else "OPEN",
    ))
    return findings, float(score)


def _findings_from_document_quality(result: Any) -> Tuple[List[Finding], float]:
    findings: List[Finding] = []
    if result is None:
        sev, action = classify("DOCUMENT_QUALITY", "NOT_AVAILABLE")
        findings.append(Finding(
            finding_id=_new_id("DQ"),
            category="DOCUMENT_QUALITY",
            severity=sev,
            title="Document Quality Data Unavailable",
            description="Document quality check could not be performed.",
            recommended_action=action,
        ))
        return findings, 0.0

    score = getattr(result, "score", 0.0) or 0.0
    overall_status = str(getattr(result, "status", "NOT_AVAILABLE")).upper()

    trigger = overall_status if overall_status in ("PASSED", "FAILED", "WARNING", "NOT_AVAILABLE") else "NOT_AVAILABLE"
    sev, action = classify("DOCUMENT_QUALITY", trigger)

    completeness = getattr(result, "extraction_completeness_pct", None)
    findings.append(Finding(
        finding_id=_new_id("DQ"),
        category="DOCUMENT_QUALITY",
        severity=sev,
        title=f"[{sev}] Document Quality — {overall_status}",
        description=(
            f"Extraction completeness: {completeness}%. "
            f"Missing critical values: {getattr(result, 'missing_critical_values_count', 'N/A')}. "
            f"Data quality status: {getattr(result, 'data_quality_status', 'N/A')}."
        ),
        recommended_action=action,
        status="CLOSED" if sev == "PASSED" else "OPEN",
    ))
    return findings, float(score)


# ─────────────────────────────────────────────────────────────────────────────
# Master Engine
# ─────────────────────────────────────────────────────────────────────────────

class FindingEngine:
    """
    Master Team 2 orchestrator.

    Accepts pre-run engine results (or raw financial data to run engines inline),
    converts every check outcome into a standardised Finding, scores categories,
    computes the weighted overall score, and returns the canonical output contract.
    """

    @classmethod
    def run(
        cls,
        engine_results: Dict[str, Any],
        severity_map: Optional[Dict] = None,
        score_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Parameters
        ----------
        engine_results:
            Dict with keys:
                "mathematical_accuracy"  -> MathematicalAccuracyResult | None
                "cash_flow"              -> CashFlowCheckResult | None
                "prior_year_tieout"      -> PriorYearTieOutResult | None
                "internal_consistency"   -> InternalConsistencyResult | None
                "growth"                 -> AnalyticalComparisonResult | None
                "ratios"                 -> FinancialRatiosResult | None
                "unusual_fluctuation"    -> UnusualFluctuationResult | None
                "unusual_gain"           -> UnusualGainResult | None
                "related_disclosure"     -> RelatedDisclosureResult | None
                "document_quality"       -> DocumentQualityResult | None

        Returns
        -------
        Canonical Team 2 output dict.
        """
        all_findings: List[Finding] = []
        category_scores: Dict[str, Optional[float]] = {}

        # ── Run individual converters ────────────────────────────────────────
        converters = [
            ("mathematical_accuracy",  "MATHEMATICAL_ACCURACY",  _findings_from_mathematical_accuracy),
            ("cash_flow",              "CASH_FLOW",              _findings_from_cash_flow),
            ("prior_year_tieout",      "PRIOR_YEAR_TIEOUT",      _findings_from_prior_year_tieout),
            ("internal_consistency",   "INTERNAL_CONSISTENCY",   _findings_from_internal_consistency),
            ("growth",                 "ANALYTICAL_COMPARISON",  _findings_from_growth),
            ("ratios",                 "RATIOS",                 _findings_from_ratios),
            ("unusual_fluctuation",    "UNUSUAL_FLUCTUATION",    _findings_from_unusual_fluctuation),
            ("unusual_gain",           "UNUSUAL_GAIN",           _findings_from_unusual_gain),
            ("related_disclosure",     "RELATED_DISCLOSURE",     _findings_from_related_disclosure),
            ("document_quality",       "DOCUMENT_QUALITY",       _findings_from_document_quality),
        ]

        for result_key, category_key, converter in converters:
            result = engine_results.get(result_key)
            findings, cat_score = converter(result)
            all_findings.extend(findings)
            category_scores[category_key] = cat_score

        # ── Count severities ─────────────────────────────────────────────────
        counts = {"CRITICAL": 0, "HIGH": 0, "REVIEW": 0, "PASSED": 0}
        for f in all_findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        has_critical = counts["CRITICAL"] > 0

        # ── Overall score ────────────────────────────────────────────────────
        scoring_result = compute_overall_score(
            category_scores=category_scores,
            has_critical_finding=has_critical,
            weights=score_weights,
        )

        # ── Build findings summary ───────────────────────────────────────────
        findings_summary = {
            "critical": counts["CRITICAL"],
            "high":     counts["HIGH"],
            "review":   counts["REVIEW"],
            "passed":   counts["PASSED"],
            "details":  [f.model_dump() for f in all_findings],
        }

        return {
            "checks":             engine_results.get("checks", {}),
            "financial_metrics":  {
                "mathematical_accuracy": _serialise(engine_results.get("mathematical_accuracy")),
                "cash_flow":             _serialise(engine_results.get("cash_flow")),
                "prior_year_tieout":     _serialise(engine_results.get("prior_year_tieout")),
                "internal_consistency":  _serialise(engine_results.get("internal_consistency")),
            },
            "analytical_metrics": {
                "growth":                _serialise(engine_results.get("growth")),
                "ratios":                _serialise(engine_results.get("ratios")),
                "unusual_fluctuation":   _serialise(engine_results.get("unusual_fluctuation")),
                "unusual_gain":          _serialise(engine_results.get("unusual_gain")),
                "related_disclosure":    _serialise(engine_results.get("related_disclosure")),
                "document_quality":      _serialise(engine_results.get("document_quality")),
            },
            "findings":          findings_summary,
            "overall_score":     scoring_result["overall_score"],
            "overall_status":    scoring_result["overall_status"],
            "category_scores":   scoring_result["category_scores"],
            "weighted_components": scoring_result["weighted_components"],
            "integrity_override": scoring_result["integrity_override"],
        }


def _serialise(obj: Any) -> Any:
    """Convert Pydantic models / Decimals to plain Python objects for the output dict."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def run(engine_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Module-level convenience wrapper."""
    return FindingEngine.run(engine_results, **kwargs)
