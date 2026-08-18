"""
Comprehensive pytest / unittest test suite for segment2_financial_review/checks/internal_consistency.py.

Coverage:
- Exact match across statements, statement-to-notes, and disclosures
- Rounding match within warning tolerance (WARNING status)
- Cross-statement and statement-to-note mismatches
- Missing source data handling (NOT_AVAILABLE status, no zero assumption)
- Multiple statements evaluation (BS, IS, CFS)
- Multiple notes evaluation (Debt, Receivables, PPE, Related Party)
- Real and sample financial datasets compatibility
"""

import json
import os
import sys
import unittest
from decimal import Decimal

# Ensure project root is on sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from segment2_financial_review.checks import internal_consistency as ic


def _build_mock_consistency_data(
    bs_cash="310.20",
    cf_cash="310.20",
    is_pbt="649.00",
    cf_pbt="649.00",
    net_income="494.55",
    other_equity_curr="1545.30",
    other_equity_prev="1050.75",  # delta = 494.55
    bs_debt="180.00",
    note_debt="180.00",
    bs_tr="620.50",
    note_tr="620.50",
    bs_ppe="485.50",
    note_ppe="485.50",
    rp_total="63.80",
    period="FY2024",
    prev_period="FY2023",
):
    bs = {}
    if bs_cash is not None:
        bs["cash_and_cash_equivalents"] = {"values": {period: bs_cash}, "source": {"file": "report.pdf", "page": 42}}
    if other_equity_curr is not None:
        v = {period: other_equity_curr}
        if other_equity_prev is not None:
            v[prev_period] = other_equity_prev
        bs["other_equity"] = {"values": v, "source": {"file": "report.pdf", "page": 43}}
    if bs_debt is not None:
        bs["long_term_borrowings"] = {"values": {period: bs_debt}, "source": {"file": "report.pdf", "page": 43}}
    if bs_tr is not None:
        bs["trade_receivables"] = {"values": {period: bs_tr}, "source": {"file": "report.pdf", "page": 42}}
    if bs_ppe is not None:
        bs["property_plant_equipment"] = {"values": {period: bs_ppe}, "source": {"file": "report.pdf", "page": 42}}

    is_stmt = {}
    if is_pbt is not None:
        is_stmt["profit_before_tax"] = {"values": {period: is_pbt}, "source": {"file": "report.pdf", "page": 45}}
    if net_income is not None:
        is_stmt["profit_for_the_period"] = {"values": {period: net_income}, "source": {"file": "report.pdf", "page": 45}}

    cfs = {}
    if cf_cash is not None:
        cfs["closing_cash_and_cash_equivalents"] = {"values": {period: cf_cash}, "source": {"file": "report.pdf", "page": 48}}
    if cf_pbt is not None:
        cfs["profit_before_tax"] = {"values": {period: cf_pbt}, "source": {"file": "report.pdf", "page": 47}}

    notes = []
    if note_debt is not None:
        notes.append({
            "note_number": "Note 20",
            "topic": "Borrowings and Debt Disclosures",
            "disclosed_value": note_debt,
            "source": {"file": "report.pdf", "page": 63},
        })
    if note_tr is not None:
        notes.append({
            "note_number": "Note 12",
            "topic": "Trade Receivables Aging",
            "disclosed_value": note_tr,
            "source": {"file": "report.pdf", "page": 58},
        })
    if note_ppe is not None:
        notes.append({
            "note_number": "Note 4",
            "topic": "Property, Plant and Equipment",
            "disclosed_value": note_ppe,
            "source": {"file": "report.pdf", "page": 52},
        })
    if rp_total is not None:
        notes.append({
            "note_number": "Note 40",
            "topic": "Related Party Disclosures",
            "disclosed_value": rp_total,
            "source": {"file": "report.pdf", "page": 77},
        })

    return {
        "metadata": {
            "document_id": "DOC-TEST-IC",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": is_stmt,
        "cash_flow_statement": cfs,
        "extracted_notes_and_disclosures": notes,
    }


class TestInternalConsistency(unittest.TestCase):

    def test_01_exact_matches_across_all_sources(self):
        """Test exact matches across statements, statement-to-notes, and disclosures."""
        data = _build_mock_consistency_data()
        res = ic.run(data)

        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertGreaterEqual(res.cross_statement_matches, 3)
        self.assertGreaterEqual(res.statement_to_notes_matches, 3)
        self.assertGreaterEqual(res.disclosure_matches, 1)
        self.assertEqual(res.cross_statement_mismatches, 0)
        self.assertEqual(res.statement_to_notes_mismatches, 0)
        self.assertEqual(res.disclosure_mismatches, 0)

        # Check specific comparison details
        bs_cf_cash = next(c for c in res.comparisons if c.comparison_id == "IC_001_BS_CF_CASH")
        self.assertEqual(bs_cf_cash.status, "MATCHED")
        self.assertEqual(bs_cf_cash.value_a, Decimal("310.20"))
        self.assertEqual(bs_cf_cash.value_b, Decimal("310.20"))
        self.assertEqual(bs_cf_cash.absolute_difference, Decimal("0.00"))
        self.assertEqual(bs_cf_cash.source_a_page, 42)
        self.assertEqual(bs_cf_cash.source_b_page, 48)

    def test_02_rounding_match_warning(self):
        """Test minor discrepancy within warning tolerance -> WARNING status."""
        # BS Cash 310.20 vs CF Cash 310.23 (diff = 0.03 <= warning 0.05)
        data = _build_mock_consistency_data(cf_cash="310.23")
        res = ic.run(data)

        self.assertEqual(res.status, "WARNING")
        self.assertGreaterEqual(res.warnings_count, 1)
        bs_cf_cash = next(c for c in res.comparisons if c.comparison_id == "IC_001_BS_CF_CASH")
        self.assertEqual(bs_cf_cash.status, "WARNING")
        self.assertEqual(bs_cf_cash.absolute_difference, Decimal("0.03"))

    def test_03_cross_statement_mismatch(self):
        """Test cross-statement mismatch (BS Cash != CF Cash by 20.00 Cr)."""
        data = _build_mock_consistency_data(cf_cash="290.20")
        res = ic.run(data)

        self.assertEqual(res.status, "FAILED")
        self.assertGreaterEqual(res.cross_statement_mismatches, 1)
        bs_cf_cash = next(c for c in res.comparisons if c.comparison_id == "IC_001_BS_CF_CASH")
        self.assertEqual(bs_cf_cash.status, "MISMATCH")
        self.assertEqual(bs_cf_cash.absolute_difference, Decimal("20.00"))

    def test_04_statement_to_note_mismatch(self):
        """Test Statement to Note mismatch (BS Debt 180.00 vs Note Debt 210.00)."""
        data = _build_mock_consistency_data(note_debt="210.00")
        res = ic.run(data)

        self.assertEqual(res.status, "FAILED")
        self.assertGreaterEqual(res.statement_to_notes_mismatches, 1)
        debt_comp = next(c for c in res.comparisons if c.comparison_id == "IC_004_BS_DEBT_DISCLOSURE")
        self.assertEqual(debt_comp.status, "MISMATCH")
        self.assertEqual(debt_comp.absolute_difference, Decimal("30.00"))

    def test_05_missing_source_data_no_silent_zero(self):
        """Test missing note or statement data -> NOT_AVAILABLE (no silent zero)."""
        data = _build_mock_consistency_data(note_debt=None, cf_pbt=None)
        res = ic.run(data)

        debt_comp = next(c for c in res.comparisons if c.comparison_id == "IC_004_BS_DEBT_DISCLOSURE")
        self.assertEqual(debt_comp.status, "NOT_AVAILABLE")
        self.assertIsNone(debt_comp.value_b)
        self.assertIsNone(debt_comp.absolute_difference)

        pbt_comp = next(c for c in res.comparisons if c.comparison_id == "IC_002_IS_CF_NET_INCOME")
        self.assertEqual(pbt_comp.status, "NOT_AVAILABLE")
        self.assertIsNone(pbt_comp.value_b)

    def test_06_multiple_notes_and_statements_evaluated(self):
        """Test that multiple notes (PPE, Receivables, Debt, RP) and statements are evaluated."""
        data = _build_mock_consistency_data()
        res = ic.run(data)

        ids = [c.comparison_id for c in res.comparisons]
        self.assertIn("IC_001_BS_CF_CASH", ids)
        self.assertIn("IC_002_IS_CF_NET_INCOME", ids)
        self.assertIn("IC_003_IS_EQUITY_MOVEMENT", ids)
        self.assertIn("IC_004_BS_DEBT_DISCLOSURE", ids)
        self.assertIn("IC_005_BS_RECEIVABLES_NOTE", ids)
        self.assertIn("IC_006_BS_PPE_NOTE", ids)
        self.assertIn("IC_007_RELATED_PARTY_DISCLOSURE", ids)

    def test_07_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ic.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])
            self.assertGreater(len(res.comparisons), 0)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ic.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])


if __name__ == "__main__":
    unittest.main()
