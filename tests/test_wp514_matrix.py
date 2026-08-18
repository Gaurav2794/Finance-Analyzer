"""
Unit and Integration Tests for WP-514 Financial Statement Review Matrix.

Validates:
1. Exact 10 top-level WP-514 review categories.
2. Standardized check data contract.
3. Preservation of all underlying Team 1 + Team 2 scores, statuses, and findings.
4. Language quality integration into Document Quality category.
5. FastAPI endpoint /api/documents/{doc_id}/wp514.
"""

import unittest
from backend.services.wp514_service import WP514Service
from backend.services.storage_service import load_json, financial_data_path, review_result_path
from segment2_financial_review.engine import Segment2Engine
from fastapi.testclient import TestClient
from backend.main import app


class TestWP514ReviewMatrix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        from pathlib import Path
        cls.raw_fd = load_json(Path("outputs/DOC-071A561E3FB1/financial_data.json")) or load_json(Path("sample_financial_data.json"))
        engine = Segment2Engine()
        cls.raw_rr = engine.run(cls.raw_fd)

    def test_1_ten_required_categories_present(self):
        """Verify all 10 required WP-514 categories are generated in exact order."""
        matrix = WP514Service.generate_review_matrix(self.raw_fd, self.raw_rr)
        expected_cat_ids = [
            "MATHEMATICAL_ACCURACY",
            "CASH_FLOW",
            "PRIOR_YEAR_TIEOUT",
            "INTERNAL_CONSISTENCY",
            "ANALYTICAL_COMPARISON",
            "RATIOS",
            "UNUSUAL_FLUCTUATION",
            "UNUSUAL_GAIN",
            "RELATED_DISCLOSURE",
            "DOCUMENT_QUALITY"
        ]
        actual_cat_ids = [c["id"] for c in matrix["categories"]]
        self.assertEqual(actual_cat_ids, expected_cat_ids)
        self.assertEqual(len(matrix["categories"]), 10)

    def test_2_standardized_check_contract(self):
        """Verify every check adheres to the required contract."""
        matrix = WP514Service.generate_review_matrix(self.raw_fd, self.raw_rr)
        required_keys = {
            "id", "category", "check", "status",
            "expected_value", "actual_value", "difference",
            "difference_percent", "threshold", "source",
            "evidence", "finding_id"
        }
        self.assertGreater(len(matrix["checks"]), 20)
        for chk in matrix["checks"]:
            self.assertTrue(required_keys.issubset(chk.keys()), f"Check {chk.get('id')} missing required keys")
            self.assertIn(chk["status"], ["PASSED", "REVIEW", "WARNING", "FAILED", "NOT_AVAILABLE"])

    def test_3_document_information_populated(self):
        """Verify document metadata is populated dynamically without hardcoding."""
        matrix = WP514Service.generate_review_matrix(self.raw_fd, self.raw_rr)
        doc_info = matrix["document_information"]
        self.assertEqual(doc_info["company_name"], self.raw_fd["metadata"]["company"]["name"])
        self.assertEqual(doc_info["currency"], "INR")
        self.assertEqual(doc_info["scale"], "Crores")
        self.assertIn("FY2024", doc_info["financial_year"])

    def test_4_scores_and_statuses_faithfully_preserved(self):
        """Verify zero recalculation: overall score matches Team 2 exactly."""
        matrix = WP514Service.generate_review_matrix(self.raw_fd, self.raw_rr)
        self.assertEqual(matrix["overall"]["score"], self.raw_rr["overall_score"])
        self.assertEqual(matrix["overall"]["status"], self.raw_rr["overall_status"])

    def test_5_language_quality_checks_in_document_quality(self):
        """Verify Spelling & Grammar checks are present under DOCUMENT_QUALITY."""
        matrix = WP514Service.generate_review_matrix(self.raw_fd, self.raw_rr)
        dq_checks = [c for c in matrix["checks"] if c["category"] == "DOCUMENT_QUALITY"]
        check_names = [c["check"] for c in dq_checks]
        self.assertTrue(any("Spelling" in name for name in check_names))
        self.assertTrue(any("Grammar" in name for name in check_names))

    def test_6_api_endpoint_wp514_integration(self):
        """Test full pipeline via API and verify GET /api/documents/{doc_id}/wp514."""
        with open("sample_data/sample_financials.xlsx", "rb") as f:
            upload_resp = self.client.post("/api/documents/upload", files={"file": ("sample_financials.xlsx", f)})
        self.assertEqual(upload_resp.status_code, 200)
        doc_id = upload_resp.json()["document_id"]

        wp514_resp = self.client.get(f"/api/documents/{doc_id}/wp514")
        self.assertEqual(wp514_resp.status_code, 200)
        data = wp514_resp.json()
        self.assertEqual(data["title"], "WP-514 Financial Statement Review")
        self.assertEqual(len(data["categories"]), 10)
        self.assertGreater(len(data["checks"]), 20)
        self.assertEqual(data["overall"]["score"], 81.5)


if __name__ == "__main__":
    unittest.main()
