"""
Comprehensive pytest / unittest test suite for segment2_financial_review/checks/cash_flow.py.

Coverage:
- Perfect cash flow reconciliation & BS cash tie-out
- Cash flow arithmetic mismatch
- Balance sheet cash vs cash flow closing cash mismatch
- Minor rounding difference handling (WARNING status)
- Missing value handling (NOT_AVAILABLE status, no silent zeros)
- Opening cash fallback derivation from previous period
- Real & sample financial datasets compatibility
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

from segment2_financial_review.checks import cash_flow as cf


def _build_mock_cf_data(
    opening_cash="245.60",
    cfo="577.55",
    cfi="-224.70",
    cff="-288.25",
    reported_cf_closing="310.20",
    bs_cash="310.20",
    prev_bs_cash="245.60",
    period="FY2024",
    prev_period="FY2023",
):
    cfs = {}
    if opening_cash is not None:
        cfs["opening_cash_and_cash_equivalents"] = {"values": {period: opening_cash}}
    if cfo is not None:
        cfs["net_cash_from_operating_activities"] = {"values": {period: cfo}}
    if cfi is not None:
        cfs["net_cash_from_investing_activities"] = {"values": {period: cfi}}
    if cff is not None:
        cfs["net_cash_from_financing_activities"] = {"values": {period: cff}}
    if reported_cf_closing is not None:
        cfs["closing_cash_and_cash_equivalents"] = {"values": {period: reported_cf_closing}}

    bs = {}
    bs_vals = {}
    if bs_cash is not None:
        bs_vals[period] = bs_cash
    if prev_bs_cash is not None:
        bs_vals[prev_period] = prev_bs_cash
    if bs_vals:
        bs["cash_and_cash_equivalents"] = {"values": bs_vals}

    return {
        "metadata": {
            "document_id": "DOC-TEST-CF",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": {},
        "cash_flow_statement": cfs,
    }


class TestCashFlow(unittest.TestCase):

    def test_01_perfect_cash_flow_reconciliation(self):
        """Test perfect cash flow arithmetic and BS cash match."""
        data = _build_mock_cf_data()
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.cash_reconciliation_status, "RECONCILED")
        self.assertEqual(res.bs_cash_vs_cf_cash_status, "MATCHED")
        self.assertEqual(res.opening_cash, Decimal("245.60"))
        self.assertEqual(res.operating_cash_flow, Decimal("577.55"))
        self.assertEqual(res.investing_cash_flow, Decimal("-224.70"))
        self.assertEqual(res.financing_cash_flow, Decimal("-288.25"))
        self.assertEqual(res.expected_closing_cash, Decimal("310.20"))
        self.assertEqual(res.reported_closing_cash, Decimal("310.20"))
        self.assertEqual(res.cash_difference, Decimal("0.00"))
        self.assertEqual(res.balance_sheet_cash, Decimal("310.20"))
        self.assertEqual(res.balance_sheet_cash_difference, Decimal("0.00"))
        self.assertEqual(len(res.issues), 0)

    def test_02_cash_flow_arithmetic_mismatch(self):
        """Test cash flow arithmetic mismatch (CFO + CFI + CFF + Opening != Reported Closing)."""
        # Reported closing 330.00 vs expected 310.20 -> diff 19.80 Cr
        data = _build_mock_cf_data(reported_cf_closing="330.00", bs_cash="330.00")
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.cash_reconciliation_status, "MISMATCH")
        self.assertEqual(res.cash_difference, Decimal("19.80"))
        self.assertLess(res.score, 100.0)
        self.assertTrue(any("Cash Flow does not reconcile" in issue for issue in res.issues))

    def test_03_balance_sheet_cash_mismatch(self):
        """Test Balance Sheet Cash != Cash Flow Closing Cash."""
        # CF Closing 310.20 vs BS Cash 290.00 -> diff 20.20 Cr
        data = _build_mock_cf_data(reported_cf_closing="310.20", bs_cash="290.00")
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.cash_reconciliation_status, "RECONCILED")
        self.assertEqual(res.bs_cash_vs_cf_cash_status, "MISMATCH")
        self.assertEqual(res.balance_sheet_cash_difference, Decimal("20.20"))
        self.assertTrue(any("Balance Sheet Cash" in issue for issue in res.issues))

    def test_04_rounding_difference_warning(self):
        """Test minor discrepancy within warning tolerance -> WARNING."""
        # Expected 310.20, reported 310.23 -> diff 0.03 Cr (<= warning_tolerance 0.05)
        data = _build_mock_cf_data(reported_cf_closing="310.23", bs_cash="310.23")
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.status, "WARNING")
        self.assertEqual(res.cash_reconciliation_status, "WARNING")
        self.assertEqual(res.cash_difference, Decimal("0.03"))
        self.assertEqual(res.score, 85.0)
        self.assertTrue(any("WARNING" in issue for issue in res.issues))

    def test_05_missing_value_no_silent_zero(self):
        """Test missing CFO or opening cash -> NOT_AVAILABLE (no silent zero)."""
        data = _build_mock_cf_data(cfo=None)
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertEqual(res.cash_reconciliation_status, "NOT_AVAILABLE")
        self.assertIsNone(res.operating_cash_flow)
        self.assertIsNone(res.expected_closing_cash)
        self.assertIsNone(res.cash_difference)
        self.assertTrue(any("operating_cash_flow" in issue for issue in res.issues))

    def test_06_opening_cash_fallback_derivation(self):
        """Test fallback of opening cash from previous period's BS cash when absent in CFS."""
        data = _build_mock_cf_data(opening_cash=None, prev_bs_cash="245.60")
        res = cf.run(data, period="FY2024")

        self.assertEqual(res.cash_reconciliation_status, "RECONCILED")
        self.assertEqual(res.opening_cash, Decimal("245.60"))
        self.assertEqual(res.expected_closing_cash, Decimal("310.20"))

    def test_07_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = cf.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])
            self.assertIsNotNone(res.cash_reconciliation_status)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = cf.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])


if __name__ == "__main__":
    unittest.main()
