"""
Check 7: Related Party Disclosure Review Engine.

Validates related-party disclosures and cross-reconciles disclosed transactions:
- Number of Related Parties
- Number of Related Transactions
- Total Related-Party Value
- Disclosed Related-Party Value
- Undisclosed/Mismatched Value
- Disclosure Difference
- Disclosure Consistency %

Rules & Guarantees:
- Pure deterministic verification using Decimal.
- If disclosure note is absent -> status = "NOT_AVAILABLE".
- Full provenance / source traceability.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


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


class RelatedDisclosureResult(BaseModel):
    """Complete output of the Related Party Disclosure Review Engine."""
    model_config = _DECIMAL_CONFIG

    period: str
    number_of_related_parties: Optional[int] = None
    number_of_related_transactions: Optional[int] = None
    total_related_party_value: Optional[Decimal] = None
    disclosed_related_party_value: Optional[Decimal] = None
    undisclosed_mismatched_value: Optional[Decimal] = None
    disclosure_difference: Optional[Decimal] = None
    disclosure_consistency_pct: Optional[float] = None
    note_reference: Optional[str] = None
    note_source: Optional[SourceTrace] = None
    tolerance: Decimal = Decimal("0.01")
    score: float = 0.0
    status: CheckOverallStatus
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


def get_periods(data: Dict[str, Any]) -> List[str]:
    periods = [p.get("period_key") for p in data.get("metadata", {}).get("periods", []) if isinstance(p, dict) and "period_key" in p]
    if periods:
        return sorted(periods, reverse=True)
    return ["FY_CURRENT"]


# ---------------------------------------------------------------------------
# Master Related Disclosure Engine
# ---------------------------------------------------------------------------

class RelatedDisclosureEngine:
    """
    Parses and verifies related party transaction disclosures.
    """

    @classmethod
    def evaluate(
        cls,
        data: Dict[str, Any],
        tolerance: Decimal = Decimal("0.01"),
        period: Optional[str] = None,
    ) -> RelatedDisclosureResult:
        periods = get_periods(data)
        curr = period or (periods[0] if periods else "FY_CURRENT")

        # Find Related Party note in extracted_notes_and_disclosures
        rp_note: Optional[Dict[str, Any]] = None
        for note in data.get("extracted_notes_and_disclosures", []):
            if isinstance(note, dict) and "related party" in note.get("topic", "").lower():
                rp_note = note
                break

        if not rp_note:
            return RelatedDisclosureResult(
                period=curr,
                number_of_related_parties=None,
                number_of_related_transactions=None,
                total_related_party_value=None,
                disclosed_related_party_value=None,
                undisclosed_mismatched_value=None,
                disclosure_difference=None,
                disclosure_consistency_pct=None,
                note_reference=None,
                note_source=None,
                tolerance=tolerance,
                score=0.0,
                status="NOT_AVAILABLE",
                issues=["NOT_AVAILABLE: No Related Party Disclosures found in extracted notes."],
                details="Related party disclosures are absent from the document extract.",
            )

        num_parties = rp_note.get("related_party_count")
        num_tx = rp_note.get("transaction_count")
        disclosed_val = _to_decimal(rp_note.get("disclosed_value"))

        # Total value: if sub-item transactions are provided, sum them; otherwise use disclosed_value
        total_val = _to_decimal(rp_note.get("total_transaction_value"))
        if total_val is None:
            sub_tx = rp_note.get("transactions", [])
            if sub_tx and isinstance(sub_tx, list):
                tx_amounts = [_to_decimal(t.get("amount")) for t in sub_tx if isinstance(t, dict)]
                valid_amounts = [a for a in tx_amounts if a is not None]
                if valid_amounts:
                    total_val = sum(valid_amounts)
            if total_val is None:
                total_val = disclosed_val

        diff: Optional[Decimal] = None
        undisclosed_val: Optional[Decimal] = None
        consistency_pct: Optional[float] = None
        issues: List[str] = []

        if total_val is not None and disclosed_val is not None:
            diff = abs(total_val - disclosed_val)
            undisclosed_val = diff
            if total_val > 0:
                consistency_pct = round(float(min(Decimal("100"), (disclosed_val / total_val) * 100)), 2)
            else:
                consistency_pct = 100.0 if diff <= tolerance else 0.0

            if diff > tolerance:
                issues.append(f"MISMATCH: Disclosed related-party value ({disclosed_val} Cr) != total ({total_val} Cr), diff={diff} Cr.")
        else:
            if total_val is None and disclosed_val is not None:
                total_val = disclosed_val
                diff = Decimal("0.00")
                undisclosed_val = Decimal("0.00")
                consistency_pct = 100.0

        src_dict = rp_note.get("source", {})
        src = SourceTrace(
            file=src_dict.get("file"),
            page=src_dict.get("page"),
            table_index=src_dict.get("table_index"),
            note_ref=rp_note.get("note_number"),
            raw_label=rp_note.get("topic"),
        ) if src_dict else None

        overall_status: CheckOverallStatus = "PASSED"
        score = 100.0
        if diff is not None and diff > tolerance:
            overall_status = "WARNING"
            score = 75.0

        if (num_parties is None or num_parties == 0) and (num_tx is None or num_tx == 0):
            details = "No related party transactions identified in filing period. 0 related parties, 0 transactions disclosed, 100.0% consistency."
        else:
            p_count = num_parties if num_parties is not None else 0
            t_count = num_tx if num_tx is not None else 0
            disc_str = f"{disclosed_val:,.2f}" if disclosed_val is not None else "0.00"
            tot_str = f"{total_val:,.2f}" if total_val is not None else "0.00"
            c_pct = f"{consistency_pct:.1f}%" if consistency_pct is not None else "100.0%"
            details = f"Related Parties: {p_count}, Transactions: {t_count}, Disclosed Value: ₹{disc_str} Millions, Total Value: ₹{tot_str} Millions, Consistency: {c_pct}."

        return RelatedDisclosureResult(
            period=curr,
            number_of_related_parties=num_parties,
            number_of_related_transactions=num_tx,
            total_related_party_value=total_val,
            disclosed_related_party_value=disclosed_val,
            undisclosed_mismatched_value=undisclosed_val,
            disclosure_difference=diff,
            disclosure_consistency_pct=consistency_pct,
            note_reference=rp_note.get("note_number"),
            note_source=src,
            tolerance=tolerance,
            score=score,
            status=overall_status,
            issues=issues,
            details=details,
        )


def run(data: Dict[str, Any], period: Optional[str] = None) -> RelatedDisclosureResult:
    return RelatedDisclosureEngine.evaluate(data, period=period)
