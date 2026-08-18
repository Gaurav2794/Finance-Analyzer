"""
Unit tests for segment2_financial_review/checks/mathematical_accuracy.py.

Required Test Scenarios:
1. Perfect financial statement
2. Balance sheet mismatch
3. Gross profit mismatch
4. Operating income mismatch
5. Net income mismatch
6. Rounding difference
7. Missing value
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

from segment2_financial_review.checks import mathematical_accuracy as ma
from segment2_financial_review.checks.mathematical_accuracy import (
    MathematicalAccuracyEngine,
    CalculationDetail,
    MathematicalAccuracyResult,
)


def _build_mock_data(
    assets="2691.00",
    equity="1689.80",
    liabilities="1001.20",
    revenue="3480.00",
    cogs="320.40",
    gross_profit="3159.60",
    emp_exp="1820.00",
    other_opex="612.00",
    da="118.60",
    operating_profit="609.00",
    other_income="82.50",
    finance_costs="42.50",
    tax_expense="154.45",
    net_income="494.55",
    period="FY2024",
):
    """
    Builds a clean, valid Phase 1-style financial data structure with controllable values.
    """
    bs = {}
    if assets is not None:
        bs["total_assets"] = {"values": {period: assets}, "source": {"file": "report.pdf", "page": 1}}
    if equity is not None:
        bs["total_equity"] = {"values": {period: equity}, "source": {"file": "report.pdf", "page": 1}}
    if liabilities is not None:
        bs["total_liabilities"] = {"values": {period: liabilities}, "source": {"file": "report.pdf", "page": 1}}

    is_stmt = {}
    if revenue is not None:
        is_stmt["revenue_from_operations"] = {"values": {period: revenue}, "source": {"file": "report.pdf", "page": 2}}
    if cogs is not None:
        is_stmt["cost_of_materials_consumed"] = {"values": {period: cogs}, "source": {"file": "report.pdf", "page": 2}}
    if gross_profit is not None:
        is_stmt["gross_profit"] = {"values": {period: gross_profit}, "source": {"file": "report.pdf", "page": 2}}
    if emp_exp is not None:
        is_stmt["employee_benefit_expenses"] = {"values": {period: emp_exp}, "source": {"file": "report.pdf", "page": 2}}
    if other_opex is not None:
        is_stmt["other_operating_expenses"] = {"values": {period: other_opex}, "source": {"file": "report.pdf", "page": 2}}
    if da is not None:
        is_stmt["depreciation_and_amortization"] = {"values": {period: da}, "source": {"file": "report.pdf", "page": 2}}
    if operating_profit is not None:
        is_stmt["operating_profit"] = {"values": {period: operating_profit}, "source": {"file": "report.pdf", "page": 2}}
    if other_income is not None:
        is_stmt["other_income"] = {"values": {period: other_income}, "source": {"file": "report.pdf", "page": 2}}
    if finance_costs is not None:
        is_stmt["finance_costs"] = {"values": {period: finance_costs}, "source": {"file": "report.pdf", "page": 2}}
    if tax_expense is not None:
        is_stmt["total_tax_expense"] = {"values": {period: tax_expense}, "source": {"file": "report.pdf", "page": 2}}
    if net_income is not None:
        is_stmt["profit_for_the_period"] = {"values": {period: net_income}, "source": {"file": "report.pdf", "page": 2}}

    return {
        "metadata": {
            "document_id": "DOC-TEST-001",
            "source_file": "report.pdf",
            "periods": [{"period_key": period, "is_audited": True}],
        },
        "balance_sheet": bs,
        "income_statement": is_stmt,
        "cash_flow_statement": {},
    }


class TestMathematicalAccuracy(unittest.TestCase):

    def test_01_perfect_financial_statement(self):
        """Scenario 1: All 4 equations perfectly balance -> PASSED, 100% accuracy."""
        data = _build_mock_data()
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.total_accuracy, 100.0)
        self.assertEqual(res.subtotal_accuracy, 100.0)
        self.assertEqual(res.cross_cast_accuracy, 100.0)
        self.assertEqual(res.arithmetic_accuracy, 100.0)
        self.assertEqual(res.formula_accuracy, 100.0)
        self.assertEqual(res.rounding_difference, Decimal("0.00"))

        # Verify each calculation
        bs = res.calculations["balance_sheet"]
        self.assertEqual(bs.status, "PASSED")
        self.assertEqual(bs.calculated_value, Decimal("2691.00"))
        self.assertEqual(bs.reported_value, Decimal("2691.00"))
        self.assertEqual(bs.absolute_difference, Decimal("0.00"))

        gp = res.calculations["gross_profit"]
        self.assertEqual(gp.status, "PASSED")
        self.assertEqual(gp.calculated_value, Decimal("3159.60"))
        self.assertEqual(gp.reported_value, Decimal("3159.60"))

        op = res.calculations["operating_income"]
        self.assertEqual(op.status, "PASSED")
        self.assertEqual(op.calculated_value, Decimal("609.00"))
        self.assertEqual(op.reported_value, Decimal("609.00"))

        ni = res.calculations["net_income"]
        self.assertEqual(ni.status, "PASSED")
        self.assertEqual(ni.calculated_value, Decimal("494.55"))
        self.assertEqual(ni.reported_value, Decimal("494.55"))

    def test_02_balance_sheet_mismatch(self):
        """Scenario 2: Balance sheet does not balance (Assets != Liabilities + Equity)."""
        # Assets 2700 vs Liabilities 1001.20 + Equity 1689.80 = 2691.00 (diff = 9.00)
        data = _build_mock_data(assets="2700.00")
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        bs = res.calculations["balance_sheet"]
        self.assertEqual(bs.status, "FAILED")
        self.assertEqual(bs.reported_value, Decimal("2700.00"))
        self.assertEqual(bs.calculated_value, Decimal("2691.00"))
        self.assertEqual(bs.absolute_difference, Decimal("9.00"))
        self.assertGreater(bs.percentage_difference, 0.0)
        self.assertLess(res.total_accuracy, 100.0)
        self.assertEqual(res.cross_cast_accuracy, 0.0)
        self.assertTrue(any("Balance Sheet" in issue for issue in res.issues))

    def test_03_gross_profit_mismatch(self):
        """Scenario 3: Gross profit mismatch (Revenue - COGS != Reported GP)."""
        # Revenue 3480 - COGS 320.40 = 3159.60, reported 3100.00 (diff = 59.60)
        data = _build_mock_data(gross_profit="3100.00")
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        gp = res.calculations["gross_profit"]
        self.assertEqual(gp.status, "FAILED")
        self.assertEqual(gp.calculated_value, Decimal("3159.60"))
        self.assertEqual(gp.reported_value, Decimal("3100.00"))
        self.assertEqual(gp.absolute_difference, Decimal("59.60"))
        self.assertTrue(any("Gross Profit" in issue for issue in res.issues))

    def test_04_operating_income_mismatch(self):
        """Scenario 4: Operating income mismatch (GP - Operating Expenses != Reported Operating Income)."""
        # GP 3159.60 - Opex 2550.60 = 609.00, reported 550.00 (diff = 59.00)
        data = _build_mock_data(operating_profit="550.00")
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        op = res.calculations["operating_income"]
        self.assertEqual(op.status, "FAILED")
        self.assertEqual(op.calculated_value, Decimal("609.00"))
        self.assertEqual(op.reported_value, Decimal("550.00"))
        self.assertEqual(op.absolute_difference, Decimal("59.00"))
        self.assertTrue(any("Operating Income" in issue for issue in res.issues))

    def test_05_net_income_mismatch(self):
        """Scenario 5: Net income mismatch (OpIncome + OtherIncome - Interest - Tax != Net Income)."""
        # Op 609 + OI 82.50 - Fin 42.50 - Tax 154.45 = 494.55, reported 400.00 (diff = 94.55)
        data = _build_mock_data(net_income="400.00")
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "FAILED")
        ni = res.calculations["net_income"]
        self.assertEqual(ni.status, "FAILED")
        self.assertEqual(ni.calculated_value, Decimal("494.55"))
        self.assertEqual(ni.reported_value, Decimal("400.00"))
        self.assertEqual(ni.absolute_difference, Decimal("94.55"))
        self.assertTrue(any("Net Income" in issue for issue in res.issues))

    def test_06_rounding_difference(self):
        """Scenario 6: Small discrepancy within warning tolerance (diff = 0.02, tolerance = 0.01, warning = 0.05)."""
        # Net income reported 494.57 vs calculated 494.55 (diff = 0.02)
        data = _build_mock_data(net_income="494.57")
        res = ma.run(data, period="FY2024")

        self.assertEqual(res.status, "WARNING")
        ni = res.calculations["net_income"]
        self.assertEqual(ni.status, "WARNING")
        self.assertEqual(ni.absolute_difference, Decimal("0.02"))
        self.assertEqual(res.rounding_difference, Decimal("0.02"))
        self.assertTrue(any("WARNING" in issue for issue in res.issues))

    def test_07_missing_value_no_silent_zero(self):
        """Scenario 7: Missing value produces NOT_AVAILABLE, never assumes zero."""
        # Omit COGS entirely
        data = _build_mock_data(cogs=None)
        res = ma.run(data, period="FY2024")

        gp = res.calculations["gross_profit"]
        self.assertEqual(gp.status, "NOT_AVAILABLE")
        self.assertIsNone(gp.calculated_value)
        self.assertIsNone(gp.absolute_difference)
        self.assertIsNone(gp.percentage_difference)
        self.assertIsNone(gp.inputs["cogs"])
        self.assertIn("cogs", gp.details)

        # Omit liabilities from Balance Sheet
        data_no_liab = _build_mock_data(liabilities=None)
        res_no_liab = ma.run(data_no_liab, period="FY2024")
        bs = res_no_liab.calculations["balance_sheet"]
        self.assertEqual(bs.status, "NOT_AVAILABLE")
        self.assertIsNone(bs.calculated_value)
        self.assertIsNone(bs.absolute_difference)

    def test_08_sample_and_real_dataset_compatibility(self):
        """Scenario 8: Run against sample_financial_data.json and real output."""
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ma.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])
            self.assertEqual(len(res.calculations), 4)

        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        if os.path.exists(real_path):
            with open(real_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            res = ma.run(data)
            self.assertIn(res.status, ["PASSED", "WARNING", "FAILED"])
            self.assertEqual(len(res.calculations), 4)


if __name__ == "__main__":
    unittest.main()
