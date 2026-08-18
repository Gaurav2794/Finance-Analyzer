"""
Comprehensive pytest / unittest test suite for segment2_financial_review/analytics/ratios.py.

Coverage:
- Liquidity: Current Ratio, Quick Ratio
- Leverage: Debt-to-Equity, Debt Ratio
- Profitability: Gross Margin, Operating Margin, Net Margin, ROA, ROE
- Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover (when data exists)
- Average balance preference for ROA, ROE, Turnovers
- Zero denominator safety (ZERO_DENOMINATOR status, no ZeroDivisionError)
- Missing data handling (NOT_AVAILABLE / DATA_INSUFFICIENT, no fabrication)
- Return attributes: formula, numerator, denominator, period, status, source
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

from segment2_financial_review.analytics import ratios


def _build_mock_ratios_data(
    tca="1535.60",
    tcl="630.00",
    inventories_curr="85.40",
    inventories_prev="74.20",
    tr_curr="620.50",
    tr_prev="510.80",
    ta_curr="2691.00",
    ta_prev="2314.50",
    te_curr="1689.80",
    te_prev="1452.30",
    lt_debt="180.00",
    st_debt="95.00",
    rev="3480.00",
    cogs="320.40",
    gp="3159.60",
    op="609.00",
    pat="494.55",
    period="FY2024",
    prev_period="FY2023",
):
    bs = {}
    def _add_bs(key, curr_val, prev_val):
        v = {}
        if curr_val is not None:
            v[period] = curr_val
        if prev_val is not None:
            v[prev_period] = prev_val
        if v:
            bs[key] = {"values": v, "source": {"file": "report.pdf", "page": 42}}

    _add_bs("total_current_assets", tca, None)
    _add_bs("total_current_liabilities", tcl, None)
    _add_bs("inventories", inventories_curr, inventories_prev)
    _add_bs("trade_receivables", tr_curr, tr_prev)
    _add_bs("total_assets", ta_curr, ta_prev)
    _add_bs("total_equity", te_curr, te_prev)
    _add_bs("long_term_borrowings", lt_debt, None)
    _add_bs("short_term_borrowings", st_debt, None)

    is_stmt = {}
    def _add_is(key, curr_val):
        if curr_val is not None:
            is_stmt[key] = {"values": {period: curr_val}, "source": {"file": "report.pdf", "page": 45}}

    _add_is("revenue_from_operations", rev)
    _add_is("cost_of_materials_consumed", cogs)
    _add_is("gross_profit", gp)
    _add_is("operating_profit", op)
    _add_is("profit_for_the_period", pat)

    return {
        "metadata": {
            "document_id": "DOC-TEST-RATIOS",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": is_stmt,
        "cash_flow_statement": {},
    }


class TestFinancialRatios(unittest.TestCase):

    def test_01_all_four_ratio_categories_computed(self):
        """Test that Liquidity, Leverage, Profitability, and Efficiency ratios compute cleanly."""
        data = _build_mock_ratios_data()
        res = ratios.run(data, period="FY2024")

        self.assertEqual(res.status, "COMPUTED")
        self.assertTrue(res.efficiency_data_sufficient)
        self.assertGreaterEqual(res.ratios_computed_count, 12)

        # 1. Liquidity
        cr = res.liquidity["current_ratio"]
        self.assertEqual(cr.status, "COMPUTED")
        self.assertEqual(cr.category, "Liquidity")
        self.assertEqual(cr.numerator, Decimal("1535.60"))
        self.assertEqual(cr.denominator, Decimal("630.00"))
        # 1535.60 / 630.00 = 2.4375
        self.assertEqual(cr.value, 2.4375)

        qr = res.liquidity["quick_ratio"]
        self.assertEqual(qr.status, "COMPUTED")
        # Quick assets = 1535.60 - 85.40 = 1450.20; 1450.20 / 630 = 2.3019
        self.assertEqual(qr.value, 2.3019)

        # 2. Leverage
        de = res.leverage["debt_to_equity"]
        self.assertEqual(de.status, "COMPUTED")
        # Total debt = 180 + 95 = 275; 275 / 1689.80 = 0.1627
        self.assertEqual(de.value, 0.1627)

        dr = res.leverage["debt_ratio"]
        self.assertEqual(dr.status, "COMPUTED")
        # 275 / 2691.00 = 0.1022
        self.assertEqual(dr.value, 0.1022)

        # 3. Profitability (all in %)
        gpm = res.profitability["gross_profit_margin"]
        self.assertEqual(gpm.status, "COMPUTED")
        # 3159.60 / 3480.00 * 100 = 90.79%
        self.assertEqual(gpm.value, 90.79)

        npm = res.profitability["net_profit_margin"]
        self.assertEqual(npm.status, "COMPUTED")
        # 494.55 / 3480.00 * 100 = 14.21%
        self.assertEqual(npm.value, 14.21)

        # 4. ROA & ROE with Average Balances
        roa = res.profitability["return_on_assets"]
        self.assertEqual(roa.status, "COMPUTED")
        # Avg assets = (2691 + 2314.50)/2 = 2502.75; 494.55 / 2502.75 * 100 = 19.76%
        self.assertEqual(roa.denominator, Decimal("2502.75"))
        self.assertEqual(roa.value, 19.76)

        roe = res.profitability["return_on_equity"]
        self.assertEqual(roe.status, "COMPUTED")
        # Avg equity = (1689.80 + 1452.30)/2 = 1571.05; 494.55 / 1571.05 * 100 = 31.48%
        self.assertEqual(roe.denominator, Decimal("1571.05"))
        self.assertEqual(roe.value, 31.48)

        # 5. Efficiency
        inv_turnover = res.efficiency["inventory_turnover"]
        self.assertEqual(inv_turnover.status, "COMPUTED")
        # Avg inv = (85.40 + 74.20)/2 = 79.80; 320.40 / 79.80 = 4.015
        self.assertEqual(inv_turnover.value, 4.015)

    def test_02_zero_denominator_safe_handling(self):
        """Test zero denominator returns ZERO_DENOMINATOR status without error."""
        data = _build_mock_ratios_data(tcl="0.00", rev="0.00")
        res = ratios.run(data)

        cr = res.liquidity["current_ratio"]
        self.assertEqual(cr.status, "ZERO_DENOMINATOR")
        self.assertIsNone(cr.value)

        gpm = res.profitability["gross_profit_margin"]
        self.assertEqual(gpm.status, "ZERO_DENOMINATOR")
        self.assertIsNone(gpm.value)

    def test_03_missing_data_no_fabrication(self):
        """Test missing inputs produce NOT_AVAILABLE / DATA_INSUFFICIENT without fabricating values."""
        data = _build_mock_ratios_data(inventories_curr=None, inventories_prev=None)
        res = ratios.run(data)

        # Quick ratio cannot be computed without inventory
        qr = res.liquidity["quick_ratio"]
        self.assertEqual(qr.status, "NOT_AVAILABLE")
        self.assertIsNone(qr.value)

        # Inventory turnover cannot be computed
        it = res.efficiency["inventory_turnover"]
        self.assertEqual(it.status, "DATA_INSUFFICIENT")
        self.assertIsNone(it.value)
        self.assertFalse(res.efficiency_data_sufficient)

    def test_04_single_period_fallback_to_ending_balance(self):
        """Test that ROA/ROE fallback to ending balance when previous period is absent."""
        data = _build_mock_ratios_data(ta_prev=None, te_prev=None)
        res = ratios.run(data)

        roa = res.profitability["return_on_assets"]
        self.assertEqual(roa.status, "COMPUTED")
        # Denominator should equal ending total assets 2691.00 directly
        self.assertEqual(roa.denominator, Decimal("2691.00"))

    def test_05_return_attributes_completeness(self):
        """Test that all required attributes (formula, numerator, denominator, period, status, source) are present."""
        data = _build_mock_ratios_data()
        res = ratios.run(data)

        for name, r in res.all_ratios.items():
            self.assertIsNotNone(r.ratio_name)
            self.assertIsNotNone(r.formula)
            self.assertEqual(r.period, "FY2024")
            self.assertIn(r.status, ["COMPUTED", "NOT_AVAILABLE", "ZERO_DENOMINATOR", "DATA_INSUFFICIENT"])
            if r.status == "COMPUTED":
                self.assertIsNotNone(r.numerator)
                self.assertIsNotNone(r.denominator)
                self.assertIsNotNone(r.value)

    def test_06_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ratios.run(data)
            self.assertIn(res.status, ["COMPUTED", "PARTIAL", "NOT_AVAILABLE"])
            self.assertGreater(res.ratios_computed_count, 0)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ratios.run(data)
            self.assertIn(res.status, ["COMPUTED", "PARTIAL", "NOT_AVAILABLE"])


if __name__ == "__main__":
    unittest.main()
