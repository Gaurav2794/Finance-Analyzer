"""
Check 4: Internal Consistency & Cross-Statement Matching.

Verifies that the same figure reported in multiple places (statement ↔ statement,
statement ↔ disclosure note) is identical.

Cross-statement checks:
  A. BS Cash == CF Closing Cash
  B. IS Profit Before Tax == CF PBT (operating section)
  C. BS Long-Term Debt == Note "Borrowings" disclosed_value
  D. BS Trade Receivables == Note "Trade Receivables" disclosed_value

Statement-to-note checks scan extracted_notes_and_disclosures by topic keyword.
Gracefully skips when notes are absent (empty disclosures list is a known real-output risk).
No LLM. Pure comparison.
"""

from typing import Any, Dict, List
from ..loader import (
    TOLERANCE, current_and_previous, get_value, get_note_by_topic, get_all_notes,
)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    curr, _, _ = current_and_previous(data)
    if not curr:
        return _skip("No periods found in metadata")

    comparisons: List[Dict[str, Any]] = []
    mismatches = 0

    # ------------------------------------------------------------------
    # A. Balance Sheet Cash ↔ Cash Flow Statement Closing Cash
    # ------------------------------------------------------------------
    bs_cash = get_value(data, "balance_sheet",     "cash_and_cash_equivalents", curr)
    cf_cash = get_value(data, "cash_flow_statement", "cash_and_cash_equivalents", curr)
    if bs_cash is not None and cf_cash is not None:
        diff   = round(abs(bs_cash - cf_cash), 4)
        status = "MATCHED" if diff <= TOLERANCE else "MISMATCH"
        if status == "MISMATCH":
            mismatches += 1
        comparisons.append({
            "check": "Balance Sheet Cash ↔ Cash Flow Closing Cash",
            "bs_amount": bs_cash,
            "cf_amount": cf_cash,
            "difference": diff,
            "status": status,
        })

    # ------------------------------------------------------------------
    # B. IS Profit Before Tax ↔ CF PBT (operating section start)
    # ------------------------------------------------------------------
    is_pbt = get_value(data, "income_statement",    "profit_before_tax", curr)
    cf_pbt = get_value(data, "cash_flow_statement", "profit_before_tax", curr)  # only in sample
    if is_pbt is not None and cf_pbt is not None:
        diff   = round(abs(is_pbt - cf_pbt), 4)
        status = "MATCHED" if diff <= TOLERANCE else "MISMATCH"
        if status == "MISMATCH":
            mismatches += 1
        comparisons.append({
            "check": "Income Statement PBT ↔ Cash Flow PBT (operating section)",
            "is_amount": is_pbt,
            "cf_amount": cf_pbt,
            "difference": diff,
            "status": status,
        })

    # ------------------------------------------------------------------
    # C. BS Long-Term Debt ↔ Borrowings Disclosure Note
    # ------------------------------------------------------------------
    bs_debt = get_value(data, "balance_sheet", "long_term_borrowings", curr)
    debt_note = get_note_by_topic(data, "Borrowing")
    if bs_debt is not None and debt_note is not None:
        disc_val = debt_note.get("disclosed_value")
        if disc_val is not None:
            diff   = round(abs(bs_debt - float(disc_val)), 4)
            status = "MATCHED" if diff <= TOLERANCE else "MISMATCH"
            if status == "MISMATCH":
                mismatches += 1
            comparisons.append({
                "check": f"Balance Sheet Debt ↔ {debt_note.get('note_number', 'Debt Note')}",
                "bs_amount": bs_debt,
                "disclosure_amount": float(disc_val),
                "difference": diff,
                "status": status,
            })

    # ------------------------------------------------------------------
    # D. BS Trade Receivables ↔ Trade Receivables Disclosure Note
    # ------------------------------------------------------------------
    bs_tr = get_value(data, "balance_sheet", "trade_receivables", curr)
    tr_note = get_note_by_topic(data, "Trade Receivable")
    if bs_tr is not None and tr_note is not None:
        disc_val = tr_note.get("disclosed_value")
        if disc_val is not None:
            diff   = round(abs(bs_tr - float(disc_val)), 4)
            status = "MATCHED" if diff <= TOLERANCE else "MISMATCH"
            if status == "MISMATCH":
                mismatches += 1
            comparisons.append({
                "check": f"Balance Sheet Receivables ↔ {tr_note.get('note_number', 'Receivables Note')}",
                "bs_amount": bs_tr,
                "disclosure_amount": float(disc_val),
                "difference": diff,
                "status": status,
            })

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------
    notes_available = len(get_all_notes(data))
    cross_stmt      = sum(1 for c in comparisons if "cf_amount" in c or "is_amount" in c)
    stmt_to_notes   = sum(1 for c in comparisons if "disclosure_amount" in c)
    note_mismatches = sum(1 for c in comparisons if "disclosure_amount" in c and c["status"] == "MISMATCH")
    stmt_mismatches = mismatches - note_mismatches

    checked = len(comparisons)
    passed  = checked - mismatches
    score   = round((passed / checked * 100) if checked > 0 else 95.0, 1)
    status  = "PASSED" if mismatches == 0 else "FAILED"

    result: Dict[str, Any] = {
        "score": score,
        "status": status,
        "cross_statement_matches":    cross_stmt - stmt_mismatches,
        "cross_statement_mismatches": stmt_mismatches,
        "statement_to_notes_matches":    stmt_to_notes - note_mismatches,
        "statement_to_notes_mismatches": note_mismatches,
        "comparisons": comparisons,
    }
    if notes_available == 0:
        result["note_checks_status"] = "SKIPPED — no disclosure notes in this document"
    return result


def _skip(reason: str) -> Dict[str, Any]:
    return {"score": 0.0, "status": "SKIPPED", "reason": reason, "comparisons": []}
