"""
Comprehensive pytest / unittest test suite for segment2_financial_review/analytics/growth.py.

Coverage:
- All 11 major financial metrics computed (Revenue, COGS, OpEx, GP, OpProfit, NetProfit, Assets, Liab, Equity, Cash, Debt)
- Exact arithmetic: Absolute Change = Current - Previous, Percentage Change = (Curr - Prev)/|Prev| * 100
- Direction validation: INCREASE, DECREASE, NO_CHANGE, NOT_AVAILABLE
- Safe zero-base handling (no ZeroDivisionError)
- Missing data handling (NOT_AVAILABLE status, no silent zeros)
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

from segment2_financial_review.analytics import growth


def _build_mock_analytics_data(
    rev=("3480.00", "2950.00"),
    cogs=("320.40", "280.10"),
    emp_exp=("1820.00", "1540.00"),
    other_opex=("612.00", "525.40"),
    da=("118.60", "104.20"),
    gp=("3159.60", "2669.90"),
    op=("609.00", "500.30"),
    net_profit=("494.55", "392.55"),
    assets=("2691.00", "2314.50"),
    liabilities=("1001.20", "862.20"),
    equity=("1689.80", "1452.30"),
    cash=("310.20", "245.60"),
    lt_debt=("180.00", "210.00"),
    st_debt=("95.00", "85.00"),
    period="FY2024",
    prev_period="FY2023",
):
    bs = {}
    def _add_bs(key, vals):
        if vals is not None:
            v_dict = {}
            if vals[0] is not None:
                v_dict[period] = vals[0]
            if vals[1] is not None:
                v_dict[prev_period] = vals[1]
            if v_dict:
                bs[key] = {"values": v_dict, "source": {"file": "report.pdf", "page": 42}}

    _add_bs("total_assets", assets)
    _add_bs("total_liabilities", liabilities)
    _add_bs("total_equity", equity)
    _add_bs("cash_and_cash_equivalents", cash)
    _add_bs("long_term_borrowings", lt_debt)
    _add_bs("short_term_borrowings", st_debt)

    is_stmt = {}
    def _add_is(key, vals):
        if vals is not None:
            v_dict = {}
            if vals[0] is not None:
                v_dict[period] = vals[0]
            if vals[1] is not None:
                v_dict[prev_period] = vals[1]
            if v_dict:
                is_stmt[key] = {"values": v_dict, "source": {"file": "report.pdf", "page": 45}}

    _add_is("revenue_from_operations", rev)
    _add_is("cost_of_materials_consumed", cogs)
    _add_is("employee_benefit_expenses", emp_exp)
    _add_is("other_operating_expenses", other_opex)
    _add_is("depreciation_and_amortization", da)
    _add_is("gross_profit", gp)
    _add_is("operating_profit", op)
    _add_is("profit_for_the_period", net_profit)

    return {
        "metadata": {
            "document_id": "DOC-TEST-ANALYTICS",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": is_stmt,
        "cash_flow_statement": {},
    }


class TestGrowthAnalytics(unittest.TestCase):

    def test_01_all_11_metrics_computed_correctly(self):
        """Test that all 11 core financial metrics compute exact growth and directions."""
        data = _build_mock_analytics_data()
        res = growth.run(data)

        self.assertEqual(res.status, "COMPUTED")
        self.assertEqual(res.total_metrics_evaluated, 11)
        self.assertEqual(res.metrics_computed, 11)

        expected_metrics = [
            "revenue", "cogs", "operating_expenses", "gross_profit",
            "operating_profit", "net_profit", "assets", "liabilities",
            "equity", "cash", "debt",
        ]
        for key in expected_metrics:
            self.assertIn(key, res.metrics)
            m = res.metrics[key]
            self.assertEqual(m.status, "COMPUTED")
            self.assertIsNotNone(m.current_value)
            self.assertIsNotNone(m.previous_value)
            self.assertIsNotNone(m.absolute_change)
            self.assertIsNotNone(m.percentage_change)
            self.assertIn(m.direction, ["INCREASE", "DECREASE", "NO_CHANGE"])

        # Specific metric checks
        rev = res.metrics["revenue"]
        self.assertEqual(rev.current_value, Decimal("3480.00"))
        self.assertEqual(rev.previous_value, Decimal("2950.00"))
        self.assertEqual(rev.absolute_change, Decimal("530.00"))
        # (3480 - 2950) / 2950 * 100 = 17.97%
        self.assertEqual(rev.percentage_change, 17.97)
        self.assertEqual(rev.direction, "INCREASE")

        # Debt: 180+95=275 vs 210+85=295 -> -20 Cr
        debt = res.metrics["debt"]
        self.assertEqual(debt.current_value, Decimal("275.00"))
        self.assertEqual(debt.previous_value, Decimal("295.00"))
        self.assertEqual(debt.absolute_change, Decimal("-20.00"))
        self.assertEqual(debt.direction, "DECREASE")

    def test_02_direction_and_flat_no_change(self):
        """Test NO_CHANGE and DECREASE directions."""
        data = _build_mock_analytics_data(
            rev=("3000.00", "3000.00"),      # flat
            net_profit=("200.00", "300.00"),  # decrease
        )
        res = growth.run(data)

        rev = res.metrics["revenue"]
        self.assertEqual(rev.direction, "NO_CHANGE")
        self.assertEqual(rev.absolute_change, Decimal("0.00"))
        self.assertEqual(rev.percentage_change, 0.0)

        np = res.metrics["net_profit"]
        self.assertEqual(np.direction, "DECREASE")
        self.assertEqual(np.absolute_change, Decimal("-100.00"))
        self.assertEqual(np.percentage_change, -33.33)

    def test_03_zero_base_previous_value(self):
        """Test zero previous value handled safely without ZeroDivisionError."""
        data = _build_mock_analytics_data(cogs=("150.00", "0.00"))
        res = growth.run(data)

        cogs = res.metrics["cogs"]
        self.assertEqual(cogs.status, "ZERO_BASE")
        self.assertEqual(cogs.direction, "INCREASE")
        self.assertEqual(cogs.absolute_change, Decimal("150.00"))
        self.assertIsNone(cogs.percentage_change)

    def test_04_missing_values_no_silent_zero(self):
        """Test missing values produce NOT_AVAILABLE without assuming zero."""
        data = _build_mock_analytics_data(rev=(None, "2950.00"), cash=("310.20", None))
        res = growth.run(data)

        rev = res.metrics["revenue"]
        self.assertEqual(rev.status, "NOT_AVAILABLE")
        self.assertEqual(rev.direction, "NOT_AVAILABLE")
        self.assertIsNone(rev.absolute_change)
        self.assertIsNone(rev.percentage_change)

        cash = res.metrics["cash"]
        self.assertEqual(cash.status, "NOT_AVAILABLE")
        self.assertEqual(cash.direction, "NOT_AVAILABLE")

    def test_05_single_period_only(self):
        """Test single period dataset -> all metrics NOT_AVAILABLE for growth."""
        data = _build_mock_analytics_data()
        data["metadata"]["periods"] = [{"period_key": "FY2024", "is_audited": True}]
        res = growth.run(data)

        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertEqual(res.metrics_computed, 0)

    def test_06_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = growth.run(data)
            self.assertIn(res.status, ["COMPUTED", "PARTIAL", "NOT_AVAILABLE"])
            self.assertGreater(res.metrics_computed, 0)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = growth.run(data)
            self.assertIn(res.status, ["COMPUTED", "PARTIAL", "NOT_AVAILABLE"])


if __name__ == "__main__":
    unittest.main()
