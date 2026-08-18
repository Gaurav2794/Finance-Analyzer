"""
Comprehensive test suite for the Findings + Score Engine.

Tests:
  T01 — severity.py: classify() determinism, fallback, custom maps
  T02 — scoring.py: weighted score, band classification, CRITICAL override
  T03 — finding_engine.py: CRITICAL from failed math accuracy
  T04 — finding_engine.py: CRITICAL from cash-flow mismatch
  T05 — finding_engine.py: HIGH from prior-year tie-out failure
  T06 — finding_engine.py: HIGH from internal consistency mismatch
  T07 — finding_engine.py: REVIEW from unusual fluctuation
  T08 — finding_engine.py: REVIEW from unusual gain divergence
  T09 — finding_engine.py: HIGH from related disclosure mismatch
  T10 — finding_engine.py: PASSED findings for clean engines
  T11 — finding_engine.py: None engine results -> NOT_AVAILABLE findings
  T12 — finding_engine.py: CRITICAL finding forces ATTENTION_REQUIRED status
  T13 — finding_engine.py: output contract structure
  T14 — finding_engine.py: sample + real dataset end-to-end
"""

import json
import os
import sys
import unittest
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from segment2_financial_review.findings import severity as sev_mod
from segment2_financial_review.findings import scoring as score_mod
from segment2_financial_review.findings import finding_engine as fe


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — lightweight mock result builders
# ─────────────────────────────────────────────────────────────────────────────

def _mock(attrs: Dict[str, Any]) -> MagicMock:
    """Build a MagicMock with preset attribute values and a no-op model_dump."""
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    m.model_dump.return_value = attrs
    return m


def _make_calc_detail(check_name: str, status: str, calc_val=None, rep_val=None, diff=None, pct_diff=None):
    return _mock({
        "check_id": f"CHECK_{check_name.upper().replace(' ', '_')}",
        "check_name": check_name,
        "formula": f"{check_name} formula",
        "status": status,
        "calculated_value": Decimal(str(calc_val)) if calc_val is not None else None,
        "reported_value": Decimal(str(rep_val)) if rep_val is not None else None,
        "absolute_difference": Decimal(str(diff)) if diff is not None else None,
        "percentage_difference": float(pct_diff) if pct_diff is not None else None,
        "details": f"{check_name}: calc={calc_val}, reported={rep_val}, diff={diff}",
    })


def _make_math_result(status: str, score: float, calc_statuses: Dict[str, str]):
    calcs = {k: _make_calc_detail(k, s) for k, s in calc_statuses.items()}
    return _mock({"status": status, "score": score, "calculations": calcs, "issues": []})


def _make_cf_result(recon_status: str, bs_status: str, score: float, cash_diff="0.00", bs_diff="0.00"):
    return _mock({
        "status": "PASSED" if recon_status == "RECONCILED" and bs_status == "MATCHED" else "WARNING",
        "score": score,
        "cash_reconciliation_status": recon_status,
        "bs_cash_vs_cf_cash_status": bs_status,
        "cash_difference": Decimal(cash_diff),
        "balance_sheet_cash_difference": Decimal(bs_diff),
        "issues": [],
    })


def _make_tieout_item(line_item: str, status: str, open_bal=None, prev_close=None, diff=None, pct=None):
    return _mock({
        "line_item": line_item,
        "balance_item_type": line_item,
        "tie_out_status": status,
        "opening_balance": Decimal(str(open_bal)) if open_bal is not None else None,
        "previous_closing_balance": Decimal(str(prev_close)) if prev_close is not None else None,
        "absolute_difference": Decimal(str(diff)) if diff is not None else None,
        "percentage_difference": float(pct) if pct is not None else None,
        "details": f"{line_item} tie-out: {status}",
    })


def _make_tieout_result(score: float, items: list):
    mismatches = sum(1 for i in items if getattr(i, "tie_out_status", "MATCHED") == "MISMATCH")
    return _mock({
        "status": "FAILED" if mismatches else "PASSED",
        "score": score,
        "items": items,
        "issues": [],
        "current_period": "FY2024",
    })


def _make_ic_comp(comp_id: str, metric: str, status: str, va=None, vb=None, diff=None, pct=None,
                  src_a="Balance Sheet", src_b="Cash Flow"):
    return _mock({
        "comparison_id": comp_id,
        "source_a": src_a,
        "source_b": src_b,
        "metric": metric,
        "status": status,
        "value_a": Decimal(str(va)) if va is not None else None,
        "value_b": Decimal(str(vb)) if vb is not None else None,
        "absolute_difference": Decimal(str(diff)) if diff is not None else None,
        "percentage_difference": float(pct) if pct is not None else None,
        "source_a_page": 42,
        "source_b_page": 55,
        "evidence": {},
        "details": f"{metric}: {src_a}={va}, {src_b}={vb}, diff={diff}",
    })


def _make_ic_result(score: float, comparisons: list):
    mismatches = sum(1 for c in comparisons if getattr(c, "status", "MATCHED") == "MISMATCH")
    return _mock({
        "status": "FAILED" if mismatches else "PASSED",
        "score": score,
        "comparisons": comparisons,
        "issues": [],
        "period": "FY2024",
    })


def _make_growth_result(status: str = "PASSED", score: float = 100.0, total: int = 11, computed: int = 11, na: int = 0):
    return _mock({
        "status": status,
        "score": score,
        "total_metrics_evaluated": total,
        "metrics_computed": computed,
        "not_available_count": na,
    })


def _make_ratios_result(status: str = "PASSED", score: float = 100.0, total_computed: int = 12):
    return _mock({
        "status": status,
        "score": score,
        "total_ratios_computed": total_computed,
    })


def _make_uf_item(metric: str, canonical_key: str, severity: str, change_pct=None, threshold=20.0,
                  curr=None, prev=None, note=""):
    return _mock({
        "metric": metric,
        "canonical_key": canonical_key,
        "severity": severity,
        "change_pct": change_pct,
        "threshold_pct": threshold,
        "current_value": Decimal(str(curr)) if curr is not None else None,
        "previous_value": Decimal(str(prev)) if prev is not None else None,
        "note": note,
    })


def _make_uf_result(score: float, items: list, high_count: int = 0, review_count: int = 0):
    return _mock({
        "score": score,
        "items": items,
        "high_severity_count": high_count,
        "review_severity_count": review_count,
        "flagged_count": high_count + review_count,
        "total_items_scanned": len(items),
        "status": "WARNING" if high_count + review_count else "PASSED",
        "issues": [],
    })


def _make_ug_result(trigger: str, divergence: Optional[float], score: float, status: str):
    return _mock({
        "status": status,
        "score": score,
        "divergence_trigger_status": trigger,
        "profit_vs_revenue_divergence_pp": divergence,
        "profit_growth_pct": 25.0,
        "revenue_growth_pct": 15.0,
        "gain_amount": Decimal("45.00"),
        "gain_to_profit_pct": 9.10,
        "divergence_threshold_pp": 8.0,
        "details": f"Divergence={divergence} pp, trigger={trigger}.",
        "issues": [],
    })


def _make_rd_result(status: str, score: float, diff="0.00", consistency=100.0):
    return _mock({
        "status": status,
        "score": score,
        "disclosure_difference": Decimal(diff),
        "disclosure_consistency_pct": consistency,
        "note_reference": "Note 40",
        "details": f"Consistency={consistency}%, diff={diff}.",
        "issues": [],
    })


def _make_dq_result(status: str, score: float, completeness=95.0, missing=0):
    return _mock({
        "status": status,
        "score": score,
        "extraction_completeness_pct": completeness,
        "missing_critical_values_count": missing,
        "data_quality_status": "COMPLETE" if missing == 0 else "PARTIAL",
        "issues": [],
    })


def _build_engine_results(
    math=None, cf=None, py=None, ic=None,
    growth=None, ratios=None, uf=None, ug=None, rd=None, dq=None,
):
    return {
        "mathematical_accuracy": math,
        "cash_flow":             cf,
        "prior_year_tieout":     py,
        "internal_consistency":  ic,
        "growth":                growth,
        "ratios":                ratios,
        "unusual_fluctuation":   uf,
        "unusual_gain":          ug,
        "related_disclosure":    rd,
        "document_quality":      dq,
    }


# ─────────────────────────────────────────────────────────────────────────────
# T01 — severity.py
# ─────────────────────────────────────────────────────────────────────────────

class T01_Severity(unittest.TestCase):

    def test_critical_math_failed(self):
        sev, action = sev_mod.classify("MATHEMATICAL_ACCURACY", "FAILED")
        self.assertEqual(sev, "CRITICAL")
        self.assertIn("escalate", action.lower())

    def test_high_math_warning(self):
        sev, _ = sev_mod.classify("MATHEMATICAL_ACCURACY", "WARNING")
        self.assertEqual(sev, "HIGH")

    def test_critical_cash_flow_mismatch(self):
        sev, _ = sev_mod.classify("CASH_FLOW", "MISMATCH")
        self.assertEqual(sev, "CRITICAL")

    def test_high_prior_year_failed(self):
        sev, _ = sev_mod.classify("PRIOR_YEAR_TIEOUT", "FAILED")
        self.assertEqual(sev, "HIGH")

    def test_critical_internal_consistency_failed(self):
        sev, _ = sev_mod.classify("INTERNAL_CONSISTENCY", "FAILED")
        self.assertEqual(sev, "CRITICAL")

    def test_review_unusual_fluctuation(self):
        sev, _ = sev_mod.classify("UNUSUAL_FLUCTUATION", "REVIEW")
        self.assertEqual(sev, "REVIEW")

    def test_high_unusual_fluctuation(self):
        sev, _ = sev_mod.classify("UNUSUAL_FLUCTUATION", "HIGH")
        self.assertEqual(sev, "HIGH")

    def test_review_unusual_gain_elevated(self):
        sev, _ = sev_mod.classify("UNUSUAL_GAIN", "ELEVATED")
        self.assertEqual(sev, "REVIEW")

    def test_high_related_disclosure_warning(self):
        sev, _ = sev_mod.classify("RELATED_DISCLOSURE", "WARNING")
        self.assertEqual(sev, "HIGH")

    def test_passed_produces_correct_action(self):
        sev, action = sev_mod.classify("CASH_FLOW", "PASSED")
        self.assertEqual(sev, "PASSED")
        self.assertIn("no further action", action.lower())

    def test_unmapped_trigger_falls_back_to_review(self):
        sev, _ = sev_mod.classify("MATHEMATICAL_ACCURACY", "SOME_UNKNOWN_TRIGGER")
        self.assertEqual(sev, "REVIEW")

    def test_custom_severity_map_override(self):
        custom = {("MATHEMATICAL_ACCURACY", "WARNING"): "CRITICAL"}
        sev, _ = sev_mod.classify("MATHEMATICAL_ACCURACY", "WARNING", severity_map=custom)
        self.assertEqual(sev, "CRITICAL")


# ─────────────────────────────────────────────────────────────────────────────
# T02 — scoring.py
# ─────────────────────────────────────────────────────────────────────────────

class T02_Scoring(unittest.TestCase):

    def test_all_perfect_scores_yields_excellent(self):
        cat = {k: 100.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["overall_status"], "EXCELLENT")

    def test_critical_finding_forces_attention_required(self):
        cat = {k: 100.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=True)
        self.assertEqual(result["overall_status"], "ATTENTION_REQUIRED")
        self.assertTrue(result["integrity_override"])

    def test_score_band_good(self):
        # Score each category 90 -> should land in GOOD
        cat = {k: 90.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        self.assertAlmostEqual(result["overall_score"], 90.0, places=1)
        self.assertEqual(result["overall_status"], "GOOD")

    def test_score_band_attention_required(self):
        # Score each category 75 -> ATTENTION_REQUIRED
        cat = {k: 75.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        self.assertAlmostEqual(result["overall_score"], 75.0, places=1)
        self.assertEqual(result["overall_status"], "ATTENTION_REQUIRED")

    def test_score_band_high_risk(self):
        cat = {k: 60.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        self.assertAlmostEqual(result["overall_score"], 60.0, places=1)
        self.assertEqual(result["overall_status"], "HIGH_RISK")

    def test_missing_category_score_treated_as_zero(self):
        # Only provide math accuracy = 100; all others missing -> dragged down
        cat = {"MATHEMATICAL_ACCURACY": 100.0}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        # Only 25% of 100 = 25.0 -> HIGH_RISK
        self.assertEqual(result["overall_status"], "HIGH_RISK")

    def test_weighted_components_present(self):
        cat = {k: 100.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False)
        self.assertEqual(len(result["weighted_components"]), len(score_mod.DEFAULT_CATEGORY_WEIGHTS))

    def test_custom_weights_accepted(self):
        cat = {k: 80.0 for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        custom = {k: 1.0 / len(score_mod.DEFAULT_CATEGORY_WEIGHTS) for k in score_mod.DEFAULT_CATEGORY_WEIGHTS}
        result = score_mod.compute_overall_score(cat, has_critical_finding=False, weights=custom)
        self.assertAlmostEqual(result["overall_score"], 80.0, places=1)


# ─────────────────────────────────────────────────────────────────────────────
# T03 — CRITICAL from failed mathematical accuracy
# ─────────────────────────────────────────────────────────────────────────────

class T03_CriticalMathAccuracy(unittest.TestCase):

    def setUp(self):
        math_result = _make_math_result("FAILED", 0.0, {
            "Balance Sheet Reconciliation": "FAILED",
            "Gross Profit":                 "PASSED",
        })
        self.output = fe.run(_build_engine_results(math=math_result))

    def test_has_critical_finding(self):
        self.assertGreater(self.output["findings"]["critical"], 0)

    def test_overall_status_is_attention_required(self):
        self.assertEqual(self.output["overall_status"], "ATTENTION_REQUIRED")

    def test_integrity_override_set(self):
        self.assertTrue(self.output["integrity_override"])

    def test_critical_finding_detail_present(self):
        crits = [f for f in self.output["findings"]["details"] if f["severity"] == "CRITICAL"]
        self.assertTrue(len(crits) > 0)

    def test_math_finding_has_category(self):
        crits = [f for f in self.output["findings"]["details"]
                 if f["severity"] == "CRITICAL" and f["category"] == "MATHEMATICAL_ACCURACY"]
        self.assertTrue(len(crits) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# T04 — CRITICAL from cash flow mismatch
# ─────────────────────────────────────────────────────────────────────────────

class T04_CriticalCashFlow(unittest.TestCase):

    def setUp(self):
        cf_result = _make_cf_result("MISMATCH", "MATCHED", 50.0, cash_diff="25.00")
        self.output = fe.run(_build_engine_results(cf=cf_result))

    def test_has_critical_finding(self):
        self.assertGreater(self.output["findings"]["critical"], 0)

    def test_cash_flow_finding_present(self):
        cf_crits = [f for f in self.output["findings"]["details"]
                    if f["category"] == "CASH_FLOW" and f["severity"] == "CRITICAL"]
        self.assertTrue(len(cf_crits) > 0)

    def test_cash_diff_captured(self):
        cf_crits = [f for f in self.output["findings"]["details"]
                    if f["category"] == "CASH_FLOW" and f["severity"] == "CRITICAL"]
        self.assertIsNotNone(cf_crits[0]["change"])


# ─────────────────────────────────────────────────────────────────────────────
# T05 — HIGH from prior year tie-out failure
# ─────────────────────────────────────────────────────────────────────────────

class T05_HighPriorYearTieOut(unittest.TestCase):

    def setUp(self):
        items = [
            _make_tieout_item("Equity", "MISMATCH", open_bal="1689.80", prev_close="1720.00", diff="30.20", pct=1.76),
            _make_tieout_item("Cash",   "MATCHED",  open_bal="310.20",  prev_close="310.20",  diff="0.00",  pct=0.0),
        ]
        py_result = _make_tieout_result(75.0, items)
        self.output = fe.run(_build_engine_results(py=py_result))

    def test_has_high_finding(self):
        self.assertGreater(self.output["findings"]["high"], 0)

    def test_equity_mismatch_is_high(self):
        high = [f for f in self.output["findings"]["details"]
                if f["category"] == "PRIOR_YEAR_TIEOUT" and f["severity"] == "HIGH"]
        self.assertTrue(any("Equity" in f["title"] for f in high))

    def test_matched_item_is_passed(self):
        passed = [f for f in self.output["findings"]["details"]
                  if f["category"] == "PRIOR_YEAR_TIEOUT" and f["severity"] == "PASSED"]
        self.assertTrue(any("Cash" in f["title"] for f in passed))


# ─────────────────────────────────────────────────────────────────────────────
# T06 — HIGH from internal consistency mismatch
# ─────────────────────────────────────────────────────────────────────────────

class T06_HighInternalConsistency(unittest.TestCase):

    def setUp(self):
        comps = [
            _make_ic_comp("IC001", "Cash", "MISMATCH", va="310.20", vb="290.20", diff="20.00", pct=6.89),
            _make_ic_comp("IC002", "Net Income", "MATCHED",  va="494.55", vb="494.55", diff="0.00"),
        ]
        ic_result = _make_ic_result(70.0, comps)
        self.output = fe.run(_build_engine_results(ic=ic_result))

    def test_cash_mismatch_is_critical_or_high(self):
        bad = [f for f in self.output["findings"]["details"]
               if f["category"] == "INTERNAL_CONSISTENCY" and f["severity"] in ("CRITICAL", "HIGH")]
        self.assertTrue(len(bad) > 0)

    def test_net_income_match_is_passed(self):
        passed = [f for f in self.output["findings"]["details"]
                  if f["category"] == "INTERNAL_CONSISTENCY" and f["severity"] == "PASSED"]
        self.assertTrue(any("Net Income" in f["title"] for f in passed))


# ─────────────────────────────────────────────────────────────────────────────
# T07 — REVIEW from unusual fluctuation
# ─────────────────────────────────────────────────────────────────────────────

class T07_ReviewUnusualFluctuation(unittest.TestCase):

    def setUp(self):
        items = [
            _make_uf_item("Revenue",  "revenue",  "PASSED",  change_pct=17.97, threshold=20.0, curr="3480", prev="2950"),
            _make_uf_item("COGS",     "cogs",     "HIGH",    change_pct=80.0,  threshold=20.0, curr="450",  prev="250",
                          note="High fluctuation: COGS changed by +80.00%."),
            _make_uf_item("Cash",     "cash",     "REVIEW",  change_pct=26.30, threshold=30.0, curr="310",  prev="245",
                          note="Elevated fluctuation: Cash changed by +26.30%."),
        ]
        uf_result = _make_uf_result(score=65.0, items=items, high_count=1, review_count=1)
        self.output = fe.run(_build_engine_results(uf=uf_result))

    def test_high_item_produces_high_finding(self):
        high = [f for f in self.output["findings"]["details"]
                if f["category"] == "UNUSUAL_FLUCTUATION" and f["severity"] == "HIGH"]
        self.assertTrue(any("COGS" in f["title"] for f in high))

    def test_review_item_produces_review_finding(self):
        reviews = [f for f in self.output["findings"]["details"]
                   if f["category"] == "UNUSUAL_FLUCTUATION" and f["severity"] == "REVIEW"]
        self.assertTrue(any("Cash" in f["title"] for f in reviews))

    def test_passed_item_produces_passed_finding(self):
        passed = [f for f in self.output["findings"]["details"]
                  if f["category"] == "UNUSUAL_FLUCTUATION" and f["severity"] == "PASSED"]
        self.assertTrue(any("Revenue" in f["title"] for f in passed))


# ─────────────────────────────────────────────────────────────────────────────
# T08 — REVIEW from unusual gain divergence
# ─────────────────────────────────────────────────────────────────────────────

class T08_ReviewUnusualGain(unittest.TestCase):

    def setUp(self):
        ug_result = _make_ug_result("ELEVATED", divergence=8.01, score=80.0, status="WARNING")
        self.output = fe.run(_build_engine_results(ug=ug_result))

    def test_unusual_gain_produces_review_finding(self):
        ug = [f for f in self.output["findings"]["details"]
              if f["category"] == "UNUSUAL_GAIN" and f["severity"] == "REVIEW"]
        self.assertTrue(len(ug) > 0)

    def test_divergence_in_description(self):
        ug = [f for f in self.output["findings"]["details"] if f["category"] == "UNUSUAL_GAIN"]
        self.assertTrue(any("8.01" in f["description"] for f in ug))

    def test_threshold_captured(self):
        ug = [f for f in self.output["findings"]["details"] if f["category"] == "UNUSUAL_GAIN"]
        self.assertTrue(any(f.get("threshold") == 8.0 for f in ug))


# ─────────────────────────────────────────────────────────────────────────────
# T09 — HIGH from related disclosure mismatch
# ─────────────────────────────────────────────────────────────────────────────

class T09_HighRelatedDisclosure(unittest.TestCase):

    def setUp(self):
        rd_result = _make_rd_result("WARNING", score=75.0, diff="10.00", consistency=86.45)
        self.output = fe.run(_build_engine_results(rd=rd_result))

    def test_related_disclosure_produces_high_finding(self):
        high = [f for f in self.output["findings"]["details"]
                if f["category"] == "RELATED_DISCLOSURE" and f["severity"] == "HIGH"]
        self.assertTrue(len(high) > 0)

    def test_disclosure_diff_captured(self):
        rd = [f for f in self.output["findings"]["details"] if f["category"] == "RELATED_DISCLOSURE"]
        self.assertTrue(any(f.get("change") is not None for f in rd))


# ─────────────────────────────────────────────────────────────────────────────
# T10 — All PASSED (clean engines)
# ─────────────────────────────────────────────────────────────────────────────

class T10_AllPassed(unittest.TestCase):

    def setUp(self):
        math_result = _make_math_result("PASSED", 100.0, {
            "Balance Sheet Reconciliation": "PASSED",
            "Gross Profit":                 "PASSED",
            "Operating Income":             "PASSED",
            "Net Income":                   "PASSED",
        })
        cf_result  = _make_cf_result("RECONCILED", "MATCHED", 100.0)
        items = [_make_tieout_item("Cash", "MATCHED", "310.20", "310.20", "0.00", 0.0)]
        py_result  = _make_tieout_result(100.0, items)
        ic_comps   = [_make_ic_comp("IC001", "Cash", "MATCHED", va="310.20", vb="310.20", diff="0.00")]
        ic_result  = _make_ic_result(100.0, ic_comps)
        ug_result  = _make_ug_result("NORMAL", divergence=2.0, score=100.0, status="PASSED")
        rd_result  = _make_rd_result("PASSED", score=100.0, diff="0.00", consistency=100.0)
        dq_result  = _make_dq_result("PASSED", score=100.0)
        uf_items   = [_make_uf_item("Revenue", "revenue", "PASSED", change_pct=5.0)]
        uf_result  = _make_uf_result(score=100.0, items=uf_items)
        gr_result  = _make_growth_result("PASSED", 100.0)
        rt_result  = _make_ratios_result("PASSED", 100.0)

        self.output = fe.run(_build_engine_results(
            math=math_result, cf=cf_result, py=py_result, ic=ic_result,
            growth=gr_result, ratios=rt_result, uf=uf_result,
            ug=ug_result, rd=rd_result, dq=dq_result,
        ))

    def test_no_critical_findings(self):
        self.assertEqual(self.output["findings"]["critical"], 0)

    def test_no_high_findings(self):
        self.assertEqual(self.output["findings"]["high"], 0)

    def test_overall_status_is_excellent(self):
        self.assertEqual(self.output["overall_status"], "EXCELLENT")

    def test_score_is_100(self):
        self.assertAlmostEqual(self.output["overall_score"], 100.0, places=1)

    def test_integrity_override_false(self):
        self.assertFalse(self.output["integrity_override"])


# ─────────────────────────────────────────────────────────────────────────────
# T11 — None engine results -> NOT_AVAILABLE
# ─────────────────────────────────────────────────────────────────────────────

class T11_NoneEngines(unittest.TestCase):

    def setUp(self):
        self.output = fe.run(_build_engine_results())  # all None

    def test_findings_generated_for_all_engines(self):
        cats = {f["category"] for f in self.output["findings"]["details"]}
        expected = {
            "MATHEMATICAL_ACCURACY", "CASH_FLOW", "PRIOR_YEAR_TIEOUT",
            "INTERNAL_CONSISTENCY", "ANALYTICAL_COMPARISON", "RATIOS",
            "UNUSUAL_FLUCTUATION", "UNUSUAL_GAIN", "RELATED_DISCLOSURE", "DOCUMENT_QUALITY",
        }
        self.assertEqual(expected, cats)

    def test_no_critical_from_missing_data(self):
        # NOT_AVAILABLE should not produce CRITICAL
        self.assertEqual(self.output["findings"]["critical"], 0)

    def test_score_is_zero_or_low(self):
        # All None -> all scores 0 -> overall 0
        self.assertAlmostEqual(self.output["overall_score"], 0.0, places=1)

    def test_status_is_high_risk(self):
        self.assertEqual(self.output["overall_status"], "HIGH_RISK")


# ─────────────────────────────────────────────────────────────────────────────
# T12 — CRITICAL finding always forces ATTENTION_REQUIRED
# ─────────────────────────────────────────────────────────────────────────────

class T12_CriticalOverridesScore(unittest.TestCase):

    def test_critical_overrides_otherwise_perfect_score(self):
        """Even if all other engines return 100, a single CRITICAL -> ATTENTION_REQUIRED."""
        math_result = _make_math_result("FAILED", 0.0, {
            "Balance Sheet Reconciliation": "FAILED",
        })
        # Make every other engine perfect
        cf_result  = _make_cf_result("RECONCILED", "MATCHED", 100.0)
        items = [_make_tieout_item("Cash", "MATCHED", "310.20", "310.20", "0.00", 0.0)]
        py_result  = _make_tieout_result(100.0, items)
        ic_comps   = [_make_ic_comp("IC001", "Cash", "MATCHED", va="310.20", vb="310.20", diff="0.00")]
        ic_result  = _make_ic_result(100.0, ic_comps)
        ug_result  = _make_ug_result("NORMAL", 2.0, 100.0, "PASSED")
        rd_result  = _make_rd_result("PASSED", 100.0)
        dq_result  = _make_dq_result("PASSED", 100.0)
        uf_items   = [_make_uf_item("Revenue", "revenue", "PASSED", 5.0)]
        uf_result  = _make_uf_result(100.0, uf_items)
        gr_result  = _make_growth_result("PASSED", 100.0)
        rt_result  = _make_ratios_result("PASSED", 100.0)

        output = fe.run(_build_engine_results(
            math=math_result, cf=cf_result, py=py_result, ic=ic_result,
            growth=gr_result, ratios=rt_result, uf=uf_result,
            ug=ug_result, rd=rd_result, dq=dq_result,
        ))
        self.assertEqual(output["overall_status"], "ATTENTION_REQUIRED")
        self.assertTrue(output["integrity_override"])
        self.assertGreater(output["findings"]["critical"], 0)


# ─────────────────────────────────────────────────────────────────────────────
# T13 — Output contract structure validation
# ─────────────────────────────────────────────────────────────────────────────

class T13_OutputContractStructure(unittest.TestCase):

    def setUp(self):
        self.output = fe.run(_build_engine_results())

    def test_top_level_keys_present(self):
        required = {
            "checks", "financial_metrics", "analytical_metrics",
            "findings", "overall_score", "overall_status",
            "category_scores", "weighted_components", "integrity_override",
        }
        self.assertTrue(required.issubset(set(self.output.keys())))

    def test_findings_structure(self):
        f = self.output["findings"]
        self.assertIn("critical", f)
        self.assertIn("high", f)
        self.assertIn("review", f)
        self.assertIn("passed", f)
        self.assertIn("details", f)
        self.assertIsInstance(f["details"], list)

    def test_finding_detail_fields(self):
        for detail in self.output["findings"]["details"]:
            for field in ("finding_id", "category", "severity", "title", "description", "recommended_action"):
                self.assertIn(field, detail, f"Missing field '{field}' in finding {detail.get('finding_id')}")

    def test_overall_score_is_float(self):
        self.assertIsInstance(self.output["overall_score"], float)

    def test_category_scores_has_all_categories(self):
        expected = {
            "MATHEMATICAL_ACCURACY", "CASH_FLOW", "PRIOR_YEAR_TIEOUT", "INTERNAL_CONSISTENCY",
            "ANALYTICAL_COMPARISON", "RATIOS", "UNUSUAL_FLUCTUATION", "UNUSUAL_GAIN",
            "RELATED_DISCLOSURE", "DOCUMENT_QUALITY",
        }
        self.assertEqual(expected, set(self.output["category_scores"].keys()))

    def test_all_finding_ids_unique(self):
        ids = [f["finding_id"] for f in self.output["findings"]["details"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_severity_values_valid(self):
        valid = {"CRITICAL", "HIGH", "REVIEW", "PASSED"}
        for f in self.output["findings"]["details"]:
            self.assertIn(f["severity"], valid)


# ─────────────────────────────────────────────────────────────────────────────
# T14 — End-to-end with real engines on sample / real output
# ─────────────────────────────────────────────────────────────────────────────

class T14_EndToEnd(unittest.TestCase):

    def _load_data(self, path):
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _run_all_engines(self, data):
        from segment2_financial_review.checks.mathematical_accuracy import MathematicalAccuracyEngine
        from segment2_financial_review.checks.cash_flow import CashFlowEngine
        from segment2_financial_review.checks.prior_year_tieout import PriorYearTieOutEngine
        from segment2_financial_review.checks.internal_consistency import InternalConsistencyEngine
        from segment2_financial_review.analytics.growth import AnalyticalComparisonEngine
        from segment2_financial_review.analytics.ratios import FinancialRatiosEngine
        from segment2_financial_review.analytics.unusual_fluctuation import UnusualFluctuationScanner
        from segment2_financial_review.analytics.unusual_gain import UnusualGainEngine
        from segment2_financial_review.analytics.related_disclosure import RelatedDisclosureEngine

        return {
            "mathematical_accuracy": MathematicalAccuracyEngine.evaluate(data),
            "cash_flow":             CashFlowEngine.evaluate(data),
            "prior_year_tieout":     PriorYearTieOutEngine.evaluate(data),
            "internal_consistency":  InternalConsistencyEngine.evaluate(data),
            "growth":                AnalyticalComparisonEngine.evaluate(data),
            "ratios":                FinancialRatiosEngine.evaluate(data),
            "unusual_fluctuation":   UnusualFluctuationScanner.evaluate(data),
            "unusual_gain":          UnusualGainEngine.evaluate(data),
            "related_disclosure":    RelatedDisclosureEngine.evaluate(data),
            "document_quality":      None,  # not yet implemented as separate engine
        }

    def _assert_contract(self, output):
        self.assertIn("findings", output)
        self.assertIn("overall_score", output)
        self.assertIn("overall_status", output)
        self.assertIn(output["overall_status"], ["EXCELLENT", "GOOD", "ATTENTION_REQUIRED", "HIGH_RISK"])
        self.assertIsInstance(output["findings"]["details"], list)
        self.assertGreater(len(output["findings"]["details"]), 0)
        for detail in output["findings"]["details"]:
            self.assertIn(detail["severity"], {"CRITICAL", "HIGH", "REVIEW", "PASSED"})
            self.assertTrue(len(detail["finding_id"]) > 0)

    def test_sample_dataset_end_to_end(self):
        sample_path = os.path.join(_ROOT, "sample_financial_data.json")
        data = self._load_data(sample_path)
        if data is None:
            self.skipTest("sample_financial_data.json not found")
        engine_results = self._run_all_engines(data)
        output = fe.run(engine_results)
        self._assert_contract(output)
        # Sample data has related party notes -> should NOT be NOT_AVAILABLE
        rd_findings = [f for f in output["findings"]["details"] if f["category"] == "RELATED_DISCLOSURE"]
        self.assertTrue(len(rd_findings) > 0)

    def test_real_output_end_to_end(self):
        real_path = os.path.join(_ROOT, "outputs", "financial_data.json")
        data = self._load_data(real_path)
        if data is None:
            self.skipTest("outputs/financial_data.json not found")
        engine_results = self._run_all_engines(data)
        output = fe.run(engine_results)
        self._assert_contract(output)
        self.assertGreater(output["overall_score"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
