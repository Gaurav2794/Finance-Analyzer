"""
tests/test_auth_e2e_verification.py

End-to-End Verification of Authentication, Bearer Token Attachment,
Ownership Validation, and Multi-Tenant Isolation.
"""
import json
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.wp514_service import WP514Service

client = TestClient(app)
SAMPLE_EXCEL = REPO_ROOT / "sample_data" / "sample_financials.xlsx"


class TestAuthE2EVerification(unittest.TestCase):

    def test_01_unauthenticated_upload_rejected(self):
        """Unauthenticated upload without Bearer token must be rejected with 401."""
        self.assertTrue(SAMPLE_EXCEL.exists())
        with open(SAMPLE_EXCEL, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Bearer token missing", res.json()["detail"])

    def test_02_authenticated_upload_and_pipeline(self):
        """Authenticated upload with Bearer token must succeed."""
        # Register user
        reg_res = client.post(
            "/api/auth/register",
            json={"email": "lead_auditor@firm.com", "password": "SecurePassword123!", "full_name": "Lead Auditor"},
        )
        if reg_res.status_code == 201:
            token = reg_res.json()["access_token"]
        else:
            login_res = client.post(
                "/api/auth/login",
                json={"email": "lead_auditor@firm.com", "password": "SecurePassword123!"},
            )
            self.assertEqual(login_res.status_code, 200)
            token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Verify /me
        me_res = client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], "lead_auditor@firm.com")

        # Authenticated upload
        with open(SAMPLE_EXCEL, "rb") as f:
            up_res = client.post(
                "/api/documents/upload",
                headers=headers,
                files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        self.assertEqual(up_res.status_code, 200)
        doc_id = up_res.json()["document_id"]
        self.assertTrue(doc_id.startswith("DOC-"))

        # Verify status endpoint with token
        st_res = client.get(f"/api/documents/{doc_id}/status", headers=headers)
        self.assertEqual(st_res.status_code, 200)

    def test_03_two_user_tenant_isolation(self):
        """User B cannot access User A document (404 Not Found)."""
        # User A
        res_a = client.post("/api/auth/register", json={"email": "tenant_a@firm.com", "password": "Password123!"})
        token_a = res_a.json()["access_token"] if res_a.status_code == 201 else client.post("/api/auth/login", json={"email": "tenant_a@firm.com", "password": "Password123!"}).json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A uploads document
        with open(SAMPLE_EXCEL, "rb") as f:
            up_a = client.post(
                "/api/documents/upload",
                headers=headers_a,
                files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        doc_a_id = up_a.json()["document_id"]

        # User B
        res_b = client.post("/api/auth/register", json={"email": "tenant_b@firm.com", "password": "Password123!"})
        token_b = res_b.json()["access_token"] if res_b.status_code == 201 else client.post("/api/auth/login", json={"email": "tenant_b@firm.com", "password": "Password123!"}).json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to access User A document -> 404 NOT FOUND
        cross_res = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
        self.assertEqual(cross_res.status_code, 404)

        # User B attempts to access User A status -> 404 NOT FOUND
        cross_st = client.get(f"/api/documents/{doc_a_id}/status", headers=headers_b)
        self.assertEqual(cross_st.status_code, 404)

        # User B attempts to delete User A document -> 404 NOT FOUND
        cross_del = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
        self.assertEqual(cross_del.status_code, 404)

    def test_04_wp514_regression_scores_preserved(self):
        """Verify WP-514 regression benchmarks match exact expected values."""
        datasets = [
            ("AUTO_ALL_PASS", REPO_ROOT / "outputs" / "TEST_E2E_Apex_ALL_PASS", 100.0, 82),
            ("AUTO_REVIEW", REPO_ROOT / "outputs" / "TEST_E2E_Apex_REVIEW", 96.61, 82),
            ("AUTO_FAIL", REPO_ROOT / "outputs" / "TEST_E2E_Apex_FAIL", 53.03, 82),
        ]
        for label, path, exp_score, exp_total in datasets:
            with open(path / "financial_data.json") as f:
                fd = json.load(f)
            with open(path / "review_result.json") as f:
                rr = json.load(f)
            wp = WP514Service.generate_review_matrix(fd, rr)
            ov = wp["overall"]
            self.assertEqual(ov["score"], exp_score, f"{label} score mismatch: {ov['score']} != {exp_score}")
            self.assertEqual(ov["total_checks"], exp_total, f"{label} total checks mismatch: {ov['total_checks']} != {exp_total}")
            print(f"[{label}] Verified: score={ov['score']}, total_checks={ov['total_checks']}, passed={ov['passed']}, review={ov['review']}, failed={ov['failed']}")


if __name__ == "__main__":
    unittest.main()
