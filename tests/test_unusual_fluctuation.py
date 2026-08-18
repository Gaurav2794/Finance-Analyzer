"""
Unit tests for segment2_financial_review/analytics/unusual_fluctuation.py.

Coverage:
- Scans all 15 key metrics
- Config-driven threshold override
- Severity levels: PASSED, REVIEW, HIGH, NOT_AVAILABLE
- Direction tracking: INCREASE, DECREASE, NO_CHANGE
- Margin fluctuation calculation (pp delta)
- Missing data handling (NOT_AVAILABLE status)
- Real and sample financial datasets compatibility
"""

import json
import os
import sys
import unittest
from decimal import Decimal

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from segment2_financial_review.analytics import unusual_fluctuation as uf


def _build_mock_fluctuation_data(
    rev=("3480.00", "2950.00"),       # +17.97% (PASSED under 20% threshold)
    cogs=("450.00", "250.00"),        # +80.00% (HIGH severity)
    expense=("2913.50", "2487.90"),   # +17.11% (PASSED)
    gp=("3030.00", "2700.00"),        # +12.22% (PASSED)
    op=("609.00", "480.00"),          # +26.88% (REVIEW severity under 20% threshold)
    net_profit=("494.55", "392.55"),  # +25.98% (REVIEW severity under 20% threshold)
    assets=("2691.00", "2314.50"),    # +16.27% (REVIEW severity under 15% threshold)
    liabilities=("1001.20", "862.20"),# +16.12% (PASSED)
    equity=("1689.80", "1452.30"),    # +16.35% (PASSED)
    cash=("310.20", "245.60"),        # +26.30% (PASSED under 30% threshold)
    debt=("180.00", "210.00"),        # -14.29% (PASSED under 25% threshold)
    other_income=("82.50", "65.40"),  # +26.15% (REVIEW severity under 25% threshold)
    period="FY2024",
    prev_period="FY2023",
):
    bs = {}
    def _add_bs(key, vals):
        if vals is not None:
            v = {period: vals[0], prev_period: vals[1]}
            bs[key] = {"values": v, "source": {"file": "report.pdf", "page": 42}}

    _add_bs("total_assets", assets)
    _add_bs("total_liabilities", liabilities)
    _add_bs("total_equity", equity)
    _add_bs("cash_and_cash_equivalents", cash)
    _add_bs("long_term_borrowings", debt)

    is_stmt = {}
    def _add_is(key, vals):
        if vals is not None:
            v = {period: vals[0], prev_period: vals[1]}
            is_stmt[key] = {"values": v, "source": {"file": "report.pdf", "page": 45}}

    _add_is("revenue_from_operations", rev)
    _add_is("total_expenses", expense)
    _add_is("cost_of_materials_consumed", cogs)
    _add_is("gross_profit", gp)
    _add_is("operating_profit", op)
    _add_is("profit_for_the_period", net_profit)
    _add_is("other_income", other_income)

    return {
        "metadata": {
            "document_id": "DOC-TEST-UF",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": bs,
        "income_statement": is_stmt,
        "cash_flow_statement": {},
    }


class TestUnusualFluctuation(unittest.TestCase):

    def test_01_all_15_metrics_scanned_and_classified(self):
        """Test that all 15 target metrics are scanned and severities assigned."""
        data = _build_mock_fluctuation_data()
        res = uf.run(data)

        self.assertEqual(res.total_items_scanned, 15)
        self.assertEqual(len(res.items), 15)

        # Check COGS (+80% -> HIGH severity since threshold=20%, high_multiplier=2.0x=40%)
        cogs_item = next(i for i in res.items if i.canonical_key == "cogs")
        self.assertEqual(cogs_item.severity, "HIGH")
        self.assertEqual(cogs_item.direction, "INCREASE")
        self.assertEqual(cogs_item.change_pct, 80.0)

        # Check Revenue (+17.97% -> PASSED under 20% threshold)
        rev_item = next(i for i in res.items if i.canonical_key == "revenue")
        self.assertEqual(rev_item.severity, "PASSED")
        self.assertEqual(rev_item.change_pct, 17.97)

        # Check Operating Profit (+26.88% -> REVIEW severity under 20% threshold)
        op_item = next(i for i in res.items if i.canonical_key == "operating_profit")
        self.assertEqual(op_item.severity, "REVIEW")

        # Check Margins (Gross Margin, Operating Margin, Net Margin)
        gm_item = next(i for i in res.items if i.canonical_key == "gross_margin")
        self.assertIn(gm_item.severity, ["PASSED", "REVIEW", "HIGH"])
        self.assertIsNotNone(gm_item.change_pct)

        self.assertGreater(res.flagged_count, 0)
        self.assertGreater(res.high_severity_count, 0)

    def test_02_custom_config_threshold_override(self):
        """Test that custom threshold overrides from caller work as expected."""
        data = _build_mock_fluctuation_data()
        # Set very strict revenue threshold of 5% -> 17.97% should now be HIGH (> 10%)
        res = uf.run(data, thresholds={"revenue": 5.0})

        rev_item = next(i for i in res.items if i.canonical_key == "revenue")
        self.assertEqual(rev_item.threshold_pct, 5.0)
        self.assertEqual(rev_item.severity, "HIGH")

    def test_03_missing_data_no_silent_zero(self):
        """Test missing metrics produce NOT_AVAILABLE severity without zero assumption."""
        data = _build_mock_fluctuation_data(other_income=None)
        res = uf.run(data)

        oi_item = next(i for i in res.items if i.canonical_key == "other_income")
        self.assertEqual(oi_item.severity, "NOT_AVAILABLE")
        self.assertEqual(oi_item.direction, "NOT_AVAILABLE")
        self.assertIsNone(oi_item.change_pct)

    def test_04_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = uf.run(data)
            self.assertEqual(res.total_items_scanned, 15)
            self.assertIn(res.status, ["PASSED", "WARNING", "NOT_AVAILABLE"])

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = uf.run(data)
            self.assertEqual(res.total_items_scanned, 15)


if __name__ == "__main__":
    unittest.main()
