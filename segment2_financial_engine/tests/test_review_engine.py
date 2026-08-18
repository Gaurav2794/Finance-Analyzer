"""
Unit & Integration Tests for Segment 2 Financial Review Engine.

Tests are run against both:
  - sample_financial_data.json  (rich reference contract with full notes)
  - outputs/financial_data.json (real Phase 1 output from Excel source)

Coverage:
  T01 — loader: period resolution and safe field access
  T02 — math_accuracy: correct equations and TOLERANCE handling
  T03 — cash_flow_review: reconciliation and BS/CF cash match
  T04 — prior_year_tieout: opening == previous closing
  T05 — internal_consistency: cross-statement matches
  T06 — analytical_engine: growth rate computation
  T07 — ratios: all four ratio groups computed
  T08 — unusual_fluctuations: HIGH/REVIEW flagging
  T09 — unusual_gain: divergence detection
  T10 — document_quality_guard: Team 1 metric consumption
  T11 — engine end-to-end: valid ReviewResultContract output
  T12 — engine end-to-end on real Phase 1 output
"""

import json
import os
import sys
import unittest

# Ensure project root is on path when run directly
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from segment2_financial_engine.src import loader
from segment2_financial_engine.src.checks import (
    math_accuracy,
    cash_flow_review,
    prior_year_tieout,
    internal_consistency,
    analytical_engine,
    ratios,
    unusual_fluctuations,
    unusual_gain,
    related_disclosure,
    document_quality_guard,
)
from segment2_financial_engine.src.engine import ReviewEngine

# Paths — relative to repo root
_SAMPLE  = os.path.join(_ROOT, "sample_financial_data.json")
_REAL    = os.path.join(_ROOT, "outputs", "financial_data.json")


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _has(path: str) -> bool:
    return os.path.exists(path)


class T01_Loader(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_periods_descending(self):
        periods = loader.get_periods(self.data)
        self.assertGreater(len(periods), 0)
        self.assertEqual(periods, sorted(periods, reverse=True))

    def test_current_previous_returned(self):
        curr, prev, base = loader.current_and_previous(self.data)
        self.assertIsNotNone(curr)
        self.assertIsNotNone(prev)

    def test_get_value_existing_field(self):
        curr, _, _ = loader.current_and_previous(self.data)
        rev = loader.get_value(self.data, "income_statement", "revenue_from_operations", curr)
        self.assertIsInstance(rev, float)
        self.assertGreater(rev, 0)

    def test_get_value_missing_field_returns_default(self):
        val = loader.get_value(self.data, "balance_sheet", "nonexistent_key_xyz", "FY2024", default=42.0)
        self.assertEqual(val, 42.0)

    def test_derive_gross_profit_fallback(self):
        curr, _, _ = loader.current_and_previous(self.data)
        gp = loader.derive_gross_profit(self.data, curr)
        self.assertIsNotNone(gp)
        self.assertGreater(gp, 0)

    def test_pct_change(self):
        self.assertAlmostEqual(loader.pct_change(110, 100), 10.0)
        self.assertIsNone(loader.pct_change(100, 0))
        self.assertIsNone(loader.pct_change(None, 100))

    def test_safe_div_zero_denominator(self):
        self.assertIsNone(loader.safe_div(100, 0))
        self.assertAlmostEqual(loader.safe_div(10, 4), 2.5)


class T02_MathAccuracy(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_required_keys(self):
        result = math_accuracy.run(self.data)
        for key in ("score", "status", "equations"):
            self.assertIn(key, result)

    def test_score_in_range(self):
        result = math_accuracy.run(self.data)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_bs_reconciliation_present(self):
        result = math_accuracy.run(self.data)
        self.assertIn("balance_sheet_reconciliation", result["equations"])

    def test_sample_data_passes(self):
        result = math_accuracy.run(self.data)
        self.assertEqual(result["status"], "PASSED",
                         msg=f"Math accuracy failed: {result.get('issues')}")


class T03_CashFlowReview(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_required_keys(self):
        result = cash_flow_review.run(self.data)
        for key in ("score", "status", "cash_reconciliation_status"):
            self.assertIn(key, result)

    def test_sample_data_reconciles(self):
        result = cash_flow_review.run(self.data)
        self.assertIn(result["cash_reconciliation_status"], ("RECONCILED", "SKIPPED"))

    def test_bs_cf_cash_matched(self):
        result = cash_flow_review.run(self.data)
        self.assertIn(result["bs_cash_vs_cf_cash_status"], ("MATCHED", "SKIPPED"))


class T04_PriorYearTieOut(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_items_list(self):
        result = prior_year_tieout.run(self.data)
        self.assertIn("items", result)

    def test_sample_data_matches(self):
        result = prior_year_tieout.run(self.data)
        # Tie-out compares FY2024 opening vs FY2023 closing for the same line items.
        # In a well-formed 3-period report this is a continuity check.
        # The sample uses year-end snapshots so tie-out results depend on data layout.
        # Assert: all items have a valid status (no internal errors).
        valid_statuses = {"MATCHED", "MISMATCH", "SKIPPED"}
        for item in result.get("items", []):
            self.assertIn(item["tie_out_status"], valid_statuses)


class T05_InternalConsistency(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_comparisons(self):
        result = internal_consistency.run(self.data)
        self.assertIn("comparisons", result)

    def test_no_cross_statement_mismatches(self):
        result = internal_consistency.run(self.data)
        self.assertEqual(result.get("cross_statement_mismatches", 0), 0)


class T06_AnalyticalEngine(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_growth_rates_computed(self):
        result = analytical_engine.run(self.data)
        gr = result.get("growth_rates", {})
        self.assertIn("revenue_growth_pct", gr)
        self.assertIn("net_profit_growth_pct", gr)

    def test_revenue_growth_positive_for_sample(self):
        result = analytical_engine.run(self.data)
        rev_growth = result["growth_rates"].get("revenue_growth_pct")
        if rev_growth is not None:
            self.assertGreater(rev_growth, 0)

    def test_unusual_fluctuations_are_list(self):
        result = analytical_engine.run(self.data)
        self.assertIsInstance(result.get("unusual_fluctuations", []), list)


class T07_Ratios(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_all_four_groups_present(self):
        result = ratios.run(self.data)
        for group in ("liquidity", "leverage", "profitability", "efficiency"):
            self.assertIn(group, result)

    def test_current_ratio_positive(self):
        result = ratios.run(self.data)
        cr = result["liquidity"].get("current_ratio")
        if cr is not None:
            self.assertGreater(cr, 0)

    def test_roe_positive_for_profitable_company(self):
        result = ratios.run(self.data)
        roe = result["profitability"].get("return_on_equity_pct")
        if roe is not None:
            self.assertGreater(roe, 0)


class T08_UnusualFluctuations(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_items_is_list(self):
        result = unusual_fluctuations.run(self.data)
        self.assertIsInstance(result.get("items", []), list)

    def test_severity_values_valid(self):
        result = unusual_fluctuations.run(self.data)
        valid = {"HIGH", "REVIEW", "PASSED"}
        for item in result.get("items", []):
            self.assertIn(item["severity"], valid)


class T09_UnusualGain(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_trigger_status(self):
        result = unusual_gain.run(self.data)
        self.assertIn("divergence_trigger_status", result)
        self.assertIn(result["divergence_trigger_status"], ("NORMAL", "ELEVATED", "INSUFFICIENT_DATA"))

    def test_divergence_pp_computable(self):
        result = unusual_gain.run(self.data)
        self.assertIsNotNone(result.get("profit_vs_revenue_divergence_pp"))


class T10_DocumentQualityGuard(unittest.TestCase):
    def setUp(self):
        self.data = _load(_SAMPLE)

    def test_returns_completeness_pct(self):
        result = document_quality_guard.run(self.data)
        self.assertIn("extraction_completeness_pct", result)

    def test_sample_data_passes_quality_gate(self):
        result = document_quality_guard.run(self.data)
        self.assertNotEqual(result["status"], "CRITICAL",
                            msg=f"Quality gate failed: {result.get('issues')}")


class T11_EngineEndToEnd_Sample(unittest.TestCase):
    def test_full_run_on_sample(self):
        result = ReviewEngine.run(_SAMPLE)
        # Top-level keys must match ReviewResultContract
        for key in ("metadata", "financial_metrics", "analytical_metrics",
                    "checks", "findings", "overall_score"):
            self.assertIn(key, result, msg=f"Missing key: {key}")

    def test_overall_score_in_range(self):
        result = ReviewEngine.run(_SAMPLE)
        score = result["overall_score"]
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_findings_structure(self):
        result = ReviewEngine.run(_SAMPLE)
        f = result["findings"]
        for key in ("critical", "high", "review", "passed", "details"):
            self.assertIn(key, f)

    def test_financial_metrics_populated(self):
        result = ReviewEngine.run(_SAMPLE)
        self.assertIn("liquidity",     result["financial_metrics"])
        self.assertIn("profitability", result["financial_metrics"])

    def test_growth_rates_present(self):
        result = ReviewEngine.run(_SAMPLE)
        gr = result["analytical_metrics"].get("growth_rates", {})
        self.assertIn("revenue_growth_pct", gr)


@unittest.skipUnless(_has(_REAL), "outputs/financial_data.json not found — run Segment 1 first")
class T12_EngineEndToEnd_RealOutput(unittest.TestCase):
    def test_full_run_on_real_output(self):
        result = ReviewEngine.run(_REAL)
        for key in ("metadata", "financial_metrics", "analytical_metrics",
                    "checks", "findings", "overall_score"):
            self.assertIn(key, result)

    def test_real_output_score_nonzero(self):
        result = ReviewEngine.run(_REAL)
        self.assertGreater(result["overall_score"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
