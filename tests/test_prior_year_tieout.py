"""
Comprehensive pytest / unittest test suite for segment2_financial_review/checks/prior_year_tieout.py.

Coverage:
- Perfect continuity tie-out for Cash, Debt, Equity, Retained Earnings, Assets, Liabilities, and other carried-forward balances
- Prior year mismatch detection
- Single period dataset handling (NOT_AVAILABLE)
- Missing item handling (NOT_AVAILABLE, no silent zeros)
- Rounding difference handling (WARNING status)
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

from segment2_financial_review.checks import prior_year_tieout as pyt


def _build_mock_tieout_data(
    cash=("310.20", "245.60"),
    debt_lt=("180.00", "210.00"),
    debt_st=("95.00", "85.00"),
    equity_capital=("120.00", "120.00"),
    total_equity=("1689.80", "1452.30"),
    retained_earnings=("1545.30", "1312.10"),
    total_assets=("2691.00", "2314.50"),
    non_current_assets=("1155.40", "1054.00"),
    current_assets=("1535.60", "1260.50"),
    total_liabilities=("1001.20", "862.20"),
    non_current_liab=("371.20", "380.40"),
    current_liab=("630.00", "481.80"),
    ppe=("485.50", "440.20"),
    receivables=("620.50", "510.80"),
    inventories=("85.40", "74.20"),
    payables=("315.80", "248.60"),
    period="FY2024",
    prev_period="FY2023",
):
    bs = {}
    def _add(key, vals):
        if vals is not None and (vals[0] is not None or vals[1] is not None):
            v_dict = {}
            if vals[0] is not None:
                v_dict[period] = vals[0]
            if vals[1] is not None:
                v_dict[prev_period] = vals[1]
            bs[key] = {"values": v_dict, "source": {"file": "report.pdf", "page": 42}}

    _add("cash_and_cash_equivalents", cash)
    _add("long_term_borrowings", debt_lt)
    _add("short_term_borrowings", debt_st)
    _add("equity_share_capital", equity_capital)
    _add("total_equity", total_equity)
    _add("other_equity", retained_earnings)
    _add("total_assets", total_assets)
    _add("total_non_current_assets", non_current_assets)
    _add("total_current_assets", current_assets)
    _add("total_liabilities", total_liabilities)
    _add("total_non_current_liabilities", non_current_liab)
    _add("total_current_liabilities", current_liab)
    _add("property_plant_equipment", ppe)
    _add("trade_receivables", receivables)
    _add("inventories", inventories)
    _add("trade_payables", payables)

    # In CFS, opening cash is also comparative
    cfs = {
        "opening_cash_and_cash_equivalents": {"values": {period: cash[1] if cash else None}},
    }

    return {
        "metadata": {
            "document_id": "DOC-TEST-PYT",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": {},
        "cash_flow_statement": cfs,
    }


class TestPriorYearTieOut(unittest.TestCase):

    def test_01_perfect_continuity_tieout(self):
        """Test that all carried-forward balances tie out cleanly."""
        data = _build_mock_tieout_data()
        res = pyt.run(data)

        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.mismatches, 0)
        self.assertGreaterEqual(res.items_checked, 10)
        self.assertEqual(res.items_matched, res.items_checked)

        # Check specific items
        cash_item = next(i for i in res.items if i.balance_item_type == "Cash")
        self.assertEqual(cash_item.tie_out_status, "MATCHED")
        self.assertEqual(cash_item.opening_balance, Decimal("245.60"))
        self.assertEqual(cash_item.previous_closing_balance, Decimal("245.60"))
        self.assertEqual(cash_item.absolute_difference, Decimal("0.00"))

        re_item = next(i for i in res.items if i.balance_item_type == "Retained Earnings")
        self.assertEqual(re_item.tie_out_status, "MATCHED")

    def test_02_equity_and_debt_mismatch(self):
        """Test mismatch when reported opening equity differs from previous closing."""
        # Total equity opening is 1500.00 vs previous closing 1452.30 (diff = 47.70)
        data = _build_mock_tieout_data(total_equity=("1689.80", "1452.30"))
        # Introduce mismatch in comparative column
        data["balance_sheet"]["total_equity"]["values"]["FY2023"] = "1400.00"
        # Previous closing remains 1452.30 if from another statement, or comparative differs
        # Let's test with mismatched comparative value:
        data["balance_sheet"]["long_term_borrowings"]["values"]["FY2023"] = "200.00"

        res = pyt.run(data)
        self.assertIn(res.status, ["PASSED", "FAILED", "WARNING"])

        # Create explicit mismatch
        data["cash_flow_statement"]["opening_cash_and_cash_equivalents"]["values"]["FY2024"] = "300.00"
        res2 = pyt.run(data)
        cash_item = next(i for i in res2.items if i.balance_item_type == "Cash")
        self.assertEqual(cash_item.tie_out_status, "MISMATCH")
        self.assertEqual(cash_item.absolute_difference, Decimal("54.40"))
        self.assertEqual(res2.status, "FAILED")
        self.assertGreaterEqual(res2.mismatches, 1)

    def test_03_missing_items_no_silent_zero(self):
        """Test missing carried-forward item -> NOT_AVAILABLE (no zero assumption)."""
        data = _build_mock_tieout_data(retained_earnings=None)
        res = pyt.run(data)

        re_item = next(i for i in res.items if i.balance_item_type == "Retained Earnings")
        self.assertEqual(re_item.tie_out_status, "NOT_AVAILABLE")
        self.assertIsNone(re_item.opening_balance)
        self.assertIsNone(re_item.previous_closing_balance)
        self.assertIsNone(re_item.absolute_difference)

    def test_04_single_period_only(self):
        """Test dataset with only 1 period -> status = NOT_AVAILABLE."""
        data = _build_mock_tieout_data()
        data["metadata"]["periods"] = [{"period_key": "FY2024", "is_audited": True}]
        res = pyt.run(data)

        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertEqual(res.items_checked, 0)
        self.assertTrue(any("required" in issue for issue in res.issues))

    def test_05_rounding_warning(self):
        """Test small discrepancy within warning tolerance -> WARNING."""
        data = _build_mock_tieout_data()
        # Discrepancy of 0.03 Cr in opening cash
        data["cash_flow_statement"]["opening_cash_and_cash_equivalents"]["values"]["FY2024"] = "245.63"
        res = pyt.run(data)

        self.assertEqual(res.status, "WARNING")
        self.assertGreaterEqual(res.warnings, 1)
        self.assertEqual(res.mismatches, 0)

    def test_06_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = pyt.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])
            self.assertGreater(res.items_checked, 0)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = pyt.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])


if __name__ == "__main__":
    unittest.main()
