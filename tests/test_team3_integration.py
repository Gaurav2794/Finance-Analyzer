"""
tests/test_team3_integration.py

Comprehensive End-to-End Integration Test Suite for Team 3:
Uses standard library unittest + FastAPI TestClient with Authentication.
"""
import os
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.storage_service import JobStatus

client = TestClient(app)
SAMPLE_EXCEL = REPO_ROOT / "sample_data" / "sample_financials.xlsx"


class TestTeam3Integration(unittest.TestCase):
    def test_01_health(self):
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_02_e2e_pipeline_and_all_endpoints(self):
        self.assertTrue(SAMPLE_EXCEL.exists(), f"Sample excel not found at {SAMPLE_EXCEL}")

        # 0. Register & Authenticate User
        reg_res = client.post(
            "/api/auth/register",
            json={"email": "e2e_auditor@example.com", "password": "Password123!", "full_name": "E2E Auditor"},
        )
        if reg_res.status_code == 201:
            token = reg_res.json()["access_token"]
        else:
            login_res = client.post(
                "/api/auth/login",
                json={"email": "e2e_auditor@example.com", "password": "Password123!"},
            )
            self.assertEqual(login_res.status_code, 200)
            token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 1. Upload
        with open(SAMPLE_EXCEL, "rb") as f:
            upload_res = client.post(
                "/api/documents/upload",
                headers=headers,
                files={"file": ("sample_financials.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        self.assertEqual(upload_res.status_code, 200)
        data = upload_res.json()
        doc_id = data["document_id"]
        self.assertTrue(doc_id.startswith("DOC-"))
        print(f"\n[E2E] Uploaded successfully, doc_id: {doc_id}")

        # 2. Poll Status until COMPLETED
        max_wait = 30
        start_time = time.time()
        final_status = None

        while time.time() - start_time < max_wait:
            status_res = client.get(f"/api/documents/{doc_id}/status", headers=headers)
            self.assertEqual(status_res.status_code, 200)
            st = status_res.json()
            final_status = st["status"]
            print(f"[E2E] Polling status: {st["status"]} ({st.get("step")})")
            if final_status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
            time.sleep(0.5)

        self.assertEqual(final_status, JobStatus.COMPLETED, f"Pipeline ended with status {final_status}: {st.get("error")}")

        # 3. Financial Data (Raw Team 1)
        fd_res = client.get(f"/api/documents/{doc_id}/financial-data", headers=headers)
        self.assertEqual(fd_res.status_code, 200)
        fd = fd_res.json()
        self.assertIn("metadata", fd)
        self.assertIn("balance_sheet", fd)
        self.assertIn("income_statement", fd)
        print(f"[E2E] Team 1 Financial Data verified: {len(fd.get("balance_sheet", {}))} BS items, {len(fd.get("income_statement", {}))} IS items")

        # 4. Review Result (Raw Team 2)
        rr_res = client.get(f"/api/documents/{doc_id}/review", headers=headers)
        self.assertEqual(rr_res.status_code, 200)
        rr = rr_res.json()
        self.assertIn("overall_score", rr)
        self.assertIn("findings", rr)
        print(f"[E2E] Team 2 Review verified: Overall score = {rr["overall_score"]}")

        # 5. Dashboard (Combined Presentation Adapter)
        dash_res = client.get(f"/api/documents/{doc_id}/dashboard", headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        dash = dash_res.json()
        self.assertIn("extraction_result", dash)
        self.assertIn("analysis_result", dash)
        extraction = dash["extraction_result"]
        analysis = dash["analysis_result"]
        self.assertTrue(bool(extraction["period"]["current"]))
        self.assertIn("financial_metrics", analysis)
        self.assertIn("revenue", analysis["financial_metrics"])
        self.assertIsNotNone(analysis["financial_metrics"]["revenue"]["current"])
        print(f"[E2E] Dashboard verified: Period = {extraction["period"]["current"]}, Revenue = {analysis["financial_metrics"]["revenue"]["current"]}")

        # 6. Findings Endpoint
        find_res = client.get(f"/api/documents/{doc_id}/findings", headers=headers)
        self.assertEqual(find_res.status_code, 200)
        findings_data = find_res.json()
        details = findings_data.get("details", [])
        self.assertTrue(len(details) > 0)
        print(f"[E2E] Findings verified: {len(details)} finding details returned")

        # 7. Evidence Endpoint
        finding_id = details[0].get("id") or details[0].get("finding_id")
        ev_res = client.get(f"/api/documents/{doc_id}/evidence/{finding_id}", headers=headers)
        self.assertEqual(ev_res.status_code, 200)
        ev = ev_res.json()
        self.assertEqual(ev["finding_id"], finding_id)
        self.assertIn(ev["status"], ["AVAILABLE", "METADATA_ONLY"])
        print(f"[E2E] Evidence verified for {finding_id}: status={ev["status"]}")

        # 8. AI Endpoint
        ai_res = client.post(
            f"/api/documents/{doc_id}/ai",
            headers=headers,
            json={"finding_id": finding_id, "question": "Why was this flagged?"},
        )
        self.assertEqual(ai_res.status_code, 200)
        ai_data = ai_res.json()
        self.assertIn("answer", ai_data)
        self.assertTrue(ai_data["grounded"])
        print(f"[E2E] AI response verified: grounded={ai_data["grounded"]}, answer len={len(ai_data["answer"])}")

        # 9. Report Endpoint
        rep_res = client.get(f"/api/documents/{doc_id}/report", headers=headers)
        self.assertEqual(rep_res.status_code, 200)
        rep = rep_res.json()
        self.assertIn("extraction_result", rep)
        self.assertIn("analysis_result", rep)
        self.assertIn("full_financial_metrics", rep)
        print(f"[E2E] Report endpoint verified successfully")

        # 10. Audit History List
        docs_res = client.get("/api/documents", headers=headers)
        self.assertEqual(docs_res.status_code, 200)
        docs = docs_res.json()
        self.assertTrue(len(docs) >= 1)
        print(f"[E2E] Audit History verified: {len(docs)} documents returned for user")


if __name__ == "__main__":
    unittest.main()
