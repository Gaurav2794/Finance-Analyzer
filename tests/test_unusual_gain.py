"""
Unit tests for segment2_financial_review/analytics/unusual_gain.py.

Coverage:
- Profit Growth vs Revenue Growth Divergence calculation
- Divergence trigger status: ELEVATED vs NORMAL
- Other Income / Revenue % and Gain / Profit % ratios
- Non-operating gain itemizations (investment, asset disposal, exceptional)
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

from segment2_financial_review.analytics import unusual_gain as ug


def _build_mock_gain_data(
    rev_curr="3480.00",
    rev_prev="2950.00",        # +17.97%
    pat_curr="494.55",
    pat_prev="392.55",        # +25.98% -> divergence = +8.01 pp (ELEVATED under 8.0 threshold)
    oi_curr="82.50",
    oi_prev="65.40",          # +26.15%
    inv_gain="20.00",
    disposal_gain="15.00",
    exceptional_gain="10.00",
    period="FY2024",
    prev_period="FY2023",
):
    is_stmt = {}
    def _add(key, curr_val, prev_val):
        v = {}
        if curr_val is not None:
            v[period] = curr_val
        if prev_val is not None:
            v[prev_period] = prev_val
        if v:
            is_stmt[key] = {"values": v, "source": {"file": "report.pdf", "page": 45}}

    _add("revenue_from_operations", rev_curr, rev_prev)
    _add("profit_for_the_period", pat_curr, pat_prev)
    _add("other_income", oi_curr, oi_prev)
    _add("investment_gain", inv_gain, None)
    _add("asset_disposal_gain", disposal_gain, None)
    _add("exceptional_items", exceptional_gain, None)

    return {
        "metadata": {
            "document_id": "DOC-TEST-UG",
            "periods": [
                {"period_key": period, "is_audited": True},
                {"period_key": prev_period, "is_audited": True},
            ],
        },
        "balance_sheet": {},
        "income_statement": is_stmt,
        "cash_flow_statement": {},
    }


class TestUnusualGain(unittest.TestCase):

    def test_01_elevated_divergence_detected(self):
        """Test elevated divergence (profit growth 25.98% - rev growth 17.97% = 8.01 pp >= 8.0 pp threshold)."""
        data = _build_mock_gain_data()
        res = ug.run(data, divergence_threshold_pp=8.0)

        self.assertEqual(res.revenue_growth_pct, 17.97)
        self.assertEqual(res.profit_growth_pct, 25.98)
        self.assertEqual(res.profit_vs_revenue_divergence_pp, 8.01)
        self.assertEqual(res.divergence_trigger_status, "ELEVATED")
        self.assertEqual(res.status, "WARNING")
        self.assertEqual(res.score, 80.0)

        # Non-operating gains: 20 + 15 + 10 = 45 Cr
        self.assertEqual(res.gain_amount, Decimal("45.00"))
        # Gain / Profit % = 45 / 494.55 * 100 = 9.10%
        self.assertEqual(res.gain_to_profit_pct, 9.10)
        # Other income / Revenue % = 82.50 / 3480 * 100 = 2.37%
        self.assertEqual(res.other_income_to_revenue_pct, 2.37)

    def test_02_normal_divergence(self):
        """Test normal divergence when profit growth matches revenue growth."""
        # Rev +20%, PAT +22% -> divergence = 2.0 pp (< 8.0 pp threshold)
        data = _build_mock_gain_data(
            rev_curr="3600.00", rev_prev="3000.00",  # +20.00%
            pat_curr="488.00", pat_prev="400.00",    # +22.00%
        )
        res = ug.run(data, divergence_threshold_pp=8.0)

        self.assertEqual(res.profit_vs_revenue_divergence_pp, 2.0)
        self.assertEqual(res.divergence_trigger_status, "NORMAL")
        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)

    def test_03_missing_data_no_silent_zero(self):
        """Test missing values produce NOT_AVAILABLE / INSUFFICIENT_DATA."""
        data = _build_mock_gain_data(rev_prev=None)
        res = ug.run(data)

        self.assertEqual(res.status, "NOT_AVAILABLE")
        self.assertEqual(res.divergence_trigger_status, "INSUFFICIENT_DATA")
        self.assertIsNone(res.revenue_growth_pct)
        self.assertIsNone(res.profit_vs_revenue_divergence_pp)

    def test_04_sample_and_real_dataset_compatibility(self):
        """Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ug.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "NOT_AVAILABLE"])
            self.assertIsNotNone(res.divergence_trigger_status)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ug.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "NOT_AVAILABLE"])


if __name__ == "__main__":
    unittest.main()
