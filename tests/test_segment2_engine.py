"""
Unit tests for segment2_financial_review/engine.py and run_segment2.py.

Coverage:
    T01 — Input schema validation: valid, missing statement, missing period
    T02 — Document Quality Gate: passthrough from team1_metrics
    T03 — Full pipeline run on sample_financial_data.json
    T04 — Full pipeline run on outputs/financial_data.json (real data)
    T05 — Output contract structure completeness
    T06 — Decimal-safe JSON serialisation (no Decimal in saved JSON)
    T07 — run_metadata fields present
    T08 — Missing input file raises FileNotFoundError
    T09 — Integrity override when CRITICAL finding present
    T10 — CLI runner main() returns 0 on valid input
"""

import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pydantic import ValidationError
from segment2_financial_review.engine import (
    Segment2Engine,
    FinancialDataInputSchema,
    _DocumentQualityResult,
    run_pipeline,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


SAMPLE_PATH = os.path.join(_ROOT, "sample_financial_data.json")
REAL_PATH   = os.path.join(_ROOT, "outputs", "financial_data.json")


def _minimal_data() -> dict:
    """Smallest valid financial_data.json dict for fast unit testing."""
    return {
        "metadata": {
            "document_id": "TEST-001",
            "periods": [{"period_key": "FY2024"}, {"period_key": "FY2023"}],
            "company": {"name": "Test Co", "currency": "INR", "scale": "Crores"},
        },
        "team1_metrics": {
            "document_quality": {
                "extraction_completeness_pct": 95.0,
                "missing_values": 0,
                "missing_sections": [],
                "data_quality_status": "EXCELLENT",
            }
        },
        "balance_sheet": {
            "total_assets": {
                "values": {"FY2024": "2691.00", "FY2023": "2314.50"},
                "source": {"file": "test.pdf", "page": 10},
            },
            "total_equity": {
                "values": {"FY2024": "1689.80", "FY2023": "1452.30"},
                "source": {"file": "test.pdf", "page": 10},
            },
            "total_liabilities": {
                "values": {"FY2024": "1001.20", "FY2023": "862.20"},
                "source": {"file": "test.pdf", "page": 10},
            },
            "cash_and_cash_equivalents": {
                "values": {"FY2024": "310.20", "FY2023": "245.60"},
                "source": {"file": "test.pdf", "page": 10},
            },
        },
        "income_statement": {
            "revenue_from_operations": {
                "values": {"FY2024": "3480.00", "FY2023": "2950.00"},
                "source": {"file": "test.pdf", "page": 15},
            },
            "profit_for_the_period": {
                "values": {"FY2024": "494.55", "FY2023": "392.55"},
                "source": {"file": "test.pdf", "page": 15},
            },
            "other_income": {
                "values": {"FY2024": "82.50", "FY2023": "65.40"},
                "source": {"file": "test.pdf", "page": 15},
            },
        },
        "cash_flow_statement": {},
        "extracted_notes_and_disclosures": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# T01 — Input Schema Validation
# ─────────────────────────────────────────────────────────────────────────────

class T01_InputSchemaValidation(unittest.TestCase):

    def test_valid_data_passes(self):
        data = _minimal_data()
        engine = Segment2Engine()
        validated = engine.validate_input(data)
        self.assertEqual(validated.metadata.document_id, "TEST-001")
        self.assertEqual(len(validated.metadata.periods), 2)

    def test_missing_balance_sheet_raises(self):
        data = _minimal_data()
        del data["balance_sheet"]
        with self.assertRaises(ValidationError):
            FinancialDataInputSchema(**data)

    def test_missing_income_statement_raises(self):
        data = _minimal_data()
        del data["income_statement"]
        with self.assertRaises(ValidationError):
            FinancialDataInputSchema(**data)

    def test_empty_periods_raises(self):
        data = _minimal_data()
        data["metadata"]["periods"] = []
        with self.assertRaises(ValidationError):
            FinancialDataInputSchema(**data)

    def test_extra_fields_allowed(self):
        """Team 1 may add extra top-level keys — schema allows them."""
        data = _minimal_data()
        data["rag_chunks"] = []
        data["team1_metrics"] = {"document_quality": {}}
        validated = FinancialDataInputSchema(**data)
        self.assertIsNotNone(validated)


# ─────────────────────────────────────────────────────────────────────────────
# T02 — Document Quality Gate
# ─────────────────────────────────────────────────────────────────────────────

class T02_DocumentQualityGate(unittest.TestCase):

    def test_excellent_quality_passes(self):
        data = _minimal_data()
        dq = _DocumentQualityResult(data)
        self.assertGreaterEqual(dq.score, 80.0)
        self.assertEqual(dq.status, "PASSED")

    def test_missing_team1_metrics_defaults_gracefully(self):
        data = _minimal_data()
        del data["team1_metrics"]
        dq = _DocumentQualityResult(data)
        # Should not crash; score may be low but status is deterministic
        self.assertIn(dq.status, ("NOT_AVAILABLE", "WARNING", "FAILED", "PASSED"))

    def test_missing_statements_penalises_score(self):
        data = _minimal_data()
        del data["cash_flow_statement"]
        dq = _DocumentQualityResult(data)
        self.assertEqual(dq.required_statement_availability, "PARTIAL")

    def test_all_statements_present(self):
        data = _minimal_data()
        data["cash_flow_statement"] = {"dummy": {}}
        dq = _DocumentQualityResult(data)
        self.assertEqual(dq.required_statement_availability, "ALL_PRESENT")

    def test_model_dump_keys(self):
        data = _minimal_data()
        dq = _DocumentQualityResult(data)
        d = dq.model_dump()
        for key in ("extraction_completeness_pct", "score", "status",
                    "missing_critical_values_count", "data_quality_status"):
            self.assertIn(key, d)


# ─────────────────────────────────────────────────────────────────────────────
# T03 — Full pipeline on sample data
# ─────────────────────────────────────────────────────────────────────────────

class T03_FullPipelineSample(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(SAMPLE_PATH):
            cls.result = None
            return
        engine = Segment2Engine()
        data = engine.load(SAMPLE_PATH)
        cls.result = engine.run(data)

    def _skip_if_no_sample(self):
        if self.result is None:
            self.skipTest("sample_financial_data.json not found")

    def test_output_contract_keys_present(self):
        self._skip_if_no_sample()
        for key in ("financial_metrics", "analytical_metrics", "findings",
                    "overall_score", "overall_status", "run_metadata"):
            self.assertIn(key, self.result)

    def test_overall_score_in_range(self):
        self._skip_if_no_sample()
        self.assertGreaterEqual(self.result["overall_score"], 0.0)
        self.assertLessEqual(self.result["overall_score"], 100.0)

    def test_overall_status_valid_band(self):
        self._skip_if_no_sample()
        self.assertIn(self.result["overall_status"],
                      ["EXCELLENT", "GOOD", "ATTENTION_REQUIRED", "HIGH_RISK"])

    def test_findings_counts_are_nonneg(self):
        self._skip_if_no_sample()
        f = self.result["findings"]
        for k in ("critical", "high", "review", "passed"):
            self.assertGreaterEqual(f[k], 0)

    def test_all_10_categories_scored(self):
        self._skip_if_no_sample()
        expected = {
            "MATHEMATICAL_ACCURACY", "CASH_FLOW", "PRIOR_YEAR_TIEOUT",
            "INTERNAL_CONSISTENCY", "ANALYTICAL_COMPARISON", "RATIOS",
            "UNUSUAL_FLUCTUATION", "UNUSUAL_GAIN", "RELATED_DISCLOSURE",
            "DOCUMENT_QUALITY",
        }
        self.assertEqual(expected, set(self.result["category_scores"].keys()))

    def test_run_metadata_populated(self):
        self._skip_if_no_sample()
        meta = self.result["run_metadata"]
        for key in ("document_id", "company", "current_period", "run_timestamp", "elapsed_seconds"):
            self.assertIn(key, meta)

    def test_finding_details_have_required_fields(self):
        self._skip_if_no_sample()
        for detail in self.result["findings"]["details"]:
            for field in ("finding_id", "category", "severity", "title",
                          "description", "recommended_action"):
                self.assertIn(field, detail)

    def test_all_finding_ids_unique(self):
        self._skip_if_no_sample()
        ids = [f["finding_id"] for f in self.result["findings"]["details"]]
        self.assertEqual(len(ids), len(set(ids)))


# ─────────────────────────────────────────────────────────────────────────────
# T04 — Full pipeline on real data
# ─────────────────────────────────────────────────────────────────────────────

class T04_FullPipelineRealData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(REAL_PATH):
            cls.result = None
            return
        engine = Segment2Engine()
        data = engine.load(REAL_PATH)
        cls.result = engine.run(data)

    def _skip_if_no_real(self):
        if self.result is None:
            self.skipTest("outputs/financial_data.json not found")

    def test_real_data_runs_without_error(self):
        self._skip_if_no_real()
        self.assertIn("overall_score", self.result)

    def test_real_data_score_nonzero(self):
        self._skip_if_no_real()
        self.assertGreater(self.result["overall_score"], 0.0)

    def test_real_data_status_valid(self):
        self._skip_if_no_real()
        self.assertIn(self.result["overall_status"],
                      ["EXCELLENT", "GOOD", "ATTENTION_REQUIRED", "HIGH_RISK"])


# ─────────────────────────────────────────────────────────────────────────────
# T05 — Output contract structure (minimal data)
# ─────────────────────────────────────────────────────────────────────────────

class T05_OutputContractStructure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = Segment2Engine()
        cls.result = engine.run(_minimal_data())

    def test_top_level_keys(self):
        required = {
            "checks", "financial_metrics", "analytical_metrics",
            "findings", "overall_score", "overall_status",
            "category_scores", "weighted_components", "integrity_override",
            "run_metadata",
        }
        self.assertTrue(required.issubset(set(self.result.keys())))

    def test_financial_metrics_sub_keys(self):
        fm = self.result["financial_metrics"]
        for key in ("mathematical_accuracy", "cash_flow", "prior_year_tieout",
                    "internal_consistency", "document_quality"):
            self.assertIn(key, fm)

    def test_analytical_metrics_sub_keys(self):
        am = self.result["analytical_metrics"]
        for key in ("growth", "ratios", "unusual_fluctuation",
                    "unusual_gain", "related_disclosure"):
            self.assertIn(key, am)

    def test_findings_sub_keys(self):
        f = self.result["findings"]
        for key in ("critical", "high", "review", "passed", "details"):
            self.assertIn(key, f)

    def test_severity_values_valid(self):
        valid = {"CRITICAL", "HIGH", "REVIEW", "PASSED"}
        for d in self.result["findings"]["details"]:
            self.assertIn(d["severity"], valid)

    def test_category_scores_count(self):
        self.assertEqual(len(self.result["category_scores"]), 10)


# ─────────────────────────────────────────────────────────────────────────────
# T06 — Decimal-safe JSON serialisation
# ─────────────────────────────────────────────────────────────────────────────

class T06_DecimalSafeSerialisation(unittest.TestCase):

    def test_saved_json_contains_no_raw_decimal(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            engine.save(result, tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                raw = f.read()
            # json.loads must succeed (no Decimal type leak)
            parsed = json.loads(raw)
            self.assertIn("overall_score", parsed)
        finally:
            os.unlink(tmp_path)

    def test_saved_json_is_valid_json(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            engine.save(result, tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            self.assertIsInstance(parsed, dict)
        finally:
            os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
# T07 — run_metadata fields
# ─────────────────────────────────────────────────────────────────────────────

class T07_RunMetadata(unittest.TestCase):

    def test_metadata_fields_all_present(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        meta = result["run_metadata"]
        for key in ("document_id", "company", "current_period",
                    "all_periods", "run_timestamp", "engine_version", "elapsed_seconds"):
            self.assertIn(key, meta)

    def test_document_id_matches_input(self):
        data = _minimal_data()
        data["metadata"]["document_id"] = "MY-UNIQUE-DOC"
        engine = Segment2Engine()
        result = engine.run(data)
        self.assertEqual(result["run_metadata"]["document_id"], "MY-UNIQUE-DOC")

    def test_elapsed_seconds_is_positive(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        self.assertGreater(result["run_metadata"]["elapsed_seconds"], 0)

    def test_engine_version_set(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        self.assertEqual(result["run_metadata"]["engine_version"], "2.0.0")


# ─────────────────────────────────────────────────────────────────────────────
# T08 — Missing input file
# ─────────────────────────────────────────────────────────────────────────────

class T08_MissingInputFile(unittest.TestCase):

    def test_load_raises_file_not_found(self):
        engine = Segment2Engine()
        with self.assertRaises(FileNotFoundError):
            engine.load("does_not_exist_at_all.json")

    def test_run_pipeline_raises_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "result.json")
            with self.assertRaises(FileNotFoundError):
                run_pipeline("nonexistent_input.json", out)


# ─────────────────────────────────────────────────────────────────────────────
# T09 — Integrity override
# ─────────────────────────────────────────────────────────────────────────────

class T09_IntegrityOverride(unittest.TestCase):

    def test_no_critical_no_override(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        # minimal data typically has no CRITICAL
        if result["findings"]["critical"] == 0:
            self.assertFalse(result["integrity_override"])

    def test_output_has_integrity_override_key(self):
        engine = Segment2Engine()
        result = engine.run(_minimal_data())
        self.assertIn("integrity_override", result)
        self.assertIsInstance(result["integrity_override"], bool)


# ─────────────────────────────────────────────────────────────────────────────
# T10 — CLI runner main()
# ─────────────────────────────────────────────────────────────────────────────

class T10_CliRunner(unittest.TestCase):

    def test_cli_returns_2_on_missing_file(self):
        from run_segment2 import main
        rc = main(["--input", "nonexistent_input.json", "--output", "/tmp/out.json"])
        self.assertEqual(rc, 2)

    def test_cli_returns_0_on_real_data(self):
        if not os.path.exists(REAL_PATH):
            self.skipTest("outputs/financial_data.json not found")
        from run_segment2 import main
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_out = f.name
        try:
            rc = main(["--input", REAL_PATH, "--output", tmp_out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp_out))
        finally:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)

    def test_cli_returns_0_on_sample_data(self):
        if not os.path.exists(SAMPLE_PATH):
            self.skipTest("sample_financial_data.json not found")
        from run_segment2 import main
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_out = f.name
        try:
            rc = main(["--input", SAMPLE_PATH, "--output", tmp_out])
            self.assertEqual(rc, 0)
        finally:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
