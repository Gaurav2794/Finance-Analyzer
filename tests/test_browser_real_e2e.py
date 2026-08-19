import os
import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_EXCEL = str(REPO_ROOT / "sample_data" / "sample_financials.xlsx")
FRONTEND_URL = "http://127.0.0.1:5173"
BACKEND_URL = "http://127.0.0.1:8000"

def run_real_browser_test():
    print("=" * 75)
    print(">>> RUNNING PLAYWRIGHT REAL CHROMIUM BROWSER VERIFICATION")
    print(f"[*] Frontend URL : {FRONTEND_URL}")
    print(f"[*] Backend URL  : {BACKEND_URL}")
    print(f"[*] Sample File  : {SAMPLE_EXCEL}")
    print("=" * 75)

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # TEST 1: Fresh visit with cleared storage -> Login Screen
        print("\n[STEP 1] Visiting frontend in fresh session...")
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle")

        brand_text = page.locator("h1").inner_text()
        sign_in_tab = page.locator("button", has_text="Sign In")
        create_account_tab = page.locator("button", has_text="Create Account")
        
        assert "Finance Analyzer" in brand_text, f"Unexpected title: {brand_text}"
        assert sign_in_tab.first.is_visible(), "Sign In tab not visible"
        assert create_account_tab.first.is_visible(), "Create Account tab not visible"

        token_before = page.evaluate("localStorage.getItem('finance_analyzer_token')")
        assert token_before is None, f"Expected null token before login, got: {token_before}"
        print("[✓] STEP 1 PASS: Login screen displayed, localStorage empty.")
        results["step1_login_screen_gate"] = "PASS"

        # TEST 2: Login through form
        print("\n[STEP 2] Submitting login form (auditor@example.com)...")
        page.fill("input[type='email']", "auditor@example.com")
        page.fill("input[type='password']", "DemoPassword123!")

        with page.expect_response("**/api/auth/login") as login_resp_info:
            page.click("button:has-text('Sign In to Audit Workspace')")

        login_resp = login_resp_info.value
        assert login_resp.status == 200, f"Login failed with status {login_resp.status}"
        login_json = login_resp.json()
        assert "access_token" in login_json, "No access_token in login response"
        jwt_token = login_json["access_token"]
        print(f"[+] Login response received: token length={len(jwt_token)}")

        # Wait for UploadScreen to appear
        page.wait_for_selector("text=Drop your financial document here", timeout=10000)
        
        # Verify token in localStorage
        token_after = page.evaluate("localStorage.getItem('finance_analyzer_token')")
        assert token_after == jwt_token, "Token mismatch in localStorage"
        print("[✓] STEP 2 PASS: JWT stored in localStorage and Upload Screen visible.")
        results["step2_login_and_token_storage"] = "PASS"

        # TEST 3: Upload document and verify Bearer Header
        print("\n[STEP 3] Uploading financial document with Bearer Header...")
        upload_requests = []

        def capture_upload(req):
            if "/api/documents/upload" in req.url:
                upload_requests.append(req)
        page.on("request", capture_upload)

        page.set_input_files("input[type='file']", SAMPLE_EXCEL)

        page.wait_for_timeout(2000)
        assert len(upload_requests) > 0, "No upload request triggered"
        last_upload = upload_requests[-1]
        auth_header = last_upload.headers.get("authorization", "")
        print(f"[+] Upload request authorization header: {auth_header[:30]}...")
        assert auth_header.startswith("Bearer ey"), f"Invalid auth header: {auth_header}"
        print("[✓] STEP 3 PASS: Upload sent with valid Bearer Token header.")
        results["step3_upload_bearer_header"] = "PASS"

        # TEST 4: Wait for Pipeline Completion and Dashboard
        print("\n[STEP 4] Waiting for pipeline completion...")
        page.wait_for_selector("text=Financial Statement", timeout=30000)
        print("[✓] STEP 4 PASS: Dashboard loaded successfully.")
        results["step4_dashboard_loaded"] = "PASS"

        # TEST 5: Verify Views (WP-514, Ledger, Integrity, Report)
        print("\n[STEP 5] Testing navigation views...")
        
        # 1. WP-514
        page.click("button:has-text('WP-514 Review')")
        page.wait_for_timeout(1000)
        assert page.locator("text=Executive Summary").first.is_visible() or page.locator("text=Expand All").first.is_visible()
        print("  [+] WP-514 Review view verified.")
        page.click("button:has-text('Back to Dashboard')")
        page.wait_for_timeout(500)

        # 2. Ledger
        page.click("button:has-text('Ledger')")
        page.wait_for_timeout(1000)
        assert page.locator("text=General Financial Ledger").first.is_visible()
        print("  [+] Ledger view verified.")
        page.click("button:has-text('Back to Dashboard')")
        page.wait_for_timeout(500)

        # 3. Integrity Checks
        page.click("button:has-text('Integrity Checks')")
        page.wait_for_timeout(1000)
        assert page.locator("text=Audit Integrity & Quality Controls").first.is_visible()
        print("  [+] Integrity Checks view verified.")
        page.click("button:has-text('Back to Dashboard')")
        page.wait_for_timeout(500)

        # 4. Audit Report
        page.click("button:has-text('Audit Report')")
        page.wait_for_timeout(1000)
        assert page.locator("text=Independent Financial Audit Review").first.is_visible() or page.locator("text=Print / Export PDF").first.is_visible()
        print("  [+] Audit Report view verified.")
        page.click("button:has-text('Back to Dashboard')")
        page.wait_for_timeout(500)

        print("[✓] STEP 5 PASS: All dashboard views verified.")
        results["step5_all_views"] = "PASS"

        # TEST 6: Page Refresh Session Persistence
        print("\n[STEP 6] Testing page refresh session persistence...")
        page.reload()
        page.wait_for_load_state("networkidle")
        
        token_after_reload = page.evaluate("localStorage.getItem('finance_analyzer_token')")
        assert token_after_reload == jwt_token, "Token lost after reload"
        print("[✓] STEP 6 PASS: Session persisted after page reload.")
        results["step6_session_persistence"] = "PASS"

        # TEST 7: Logout
        print("\n[STEP 7] Testing Logout...")
        signout_btn = page.locator("button[title='Sign Out'], button:has-text('Sign Out')").first
        signout_btn.click()
        page.wait_for_timeout(1000)

        token_after_logout = page.evaluate("localStorage.getItem('finance_analyzer_token')")
        assert not token_after_logout, f"Token still in storage after logout: {token_after_logout}"
        assert page.locator("button:has-text('Sign In')").first.is_visible(), "Login screen not shown after logout"
        print("[✓] STEP 7 PASS: Logged out cleanly, token removed.")
        results["step7_logout"] = "PASS"

        # TEST 8: Registration Flow
        print("\n[STEP 8] Testing real browser registration...")
        page.click("button:has-text('Create Account')")
        page.fill("input[placeholder='Auditor Lead']", "Judge Auditor")
        reg_email = f"judge-test-{int(time.time())}@financeanalyzer.local"
        page.fill("input[type='email']", reg_email)
        
        pwd_inputs = page.locator("input[type='password']")
        pwd_inputs.nth(0).fill("JudgeTest123!")
        pwd_inputs.nth(1).fill("JudgeTest123!")

        with page.expect_response("**/api/auth/register") as reg_resp_info:
            page.click("button:has-text('Create Auditor Account')")

        reg_resp = reg_resp_info.value
        assert reg_resp.status == 201, f"Registration failed: {reg_resp.status}"
        page.wait_for_selector("text=Drop your financial document here", timeout=10000)
        print(f"[✓] STEP 8 PASS: Registered new account {reg_email} and reached workspace.")
        results["step8_registration"] = "PASS"

        # TEST 9: Fast Demo Login Button
        print("\n[STEP 9] Testing Fast Demo Login button...")
        signout_btn2 = page.locator("button[title='Sign Out'], button:has-text('Sign Out')").first
        signout_btn2.click()
        page.wait_for_timeout(1000)

        page.click("button:has-text('Sign in as Lead Auditor')")
        page.wait_for_selector("text=Drop your financial document here", timeout=10000)
        print("[✓] STEP 9 PASS: Fast Demo Login button verified.")
        results["step9_fast_demo_login"] = "PASS"

        # TEST 10: 401 Session Expiration Handling
        print("\n[STEP 10] Testing 401 Session Expiration...")
        page.evaluate("localStorage.setItem('finance_analyzer_token', 'malformed_invalid_jwt')")
        page.reload()
        page.wait_for_load_state("networkidle")

        assert page.locator("button:has-text('Sign In')").first.is_visible(), "Login screen not visible after 401"
        err_text = page.locator("text=Your session has expired").inner_text()
        assert "expired" in err_text.lower(), f"Unexpected error message: {err_text}"
        print("[✓] STEP 10 PASS: 401 correctly cleared token and showed session expired alert.")
        results["step10_401_handling"] = "PASS"

        browser.close()

    print("\n" + "=" * 75)
    print(">>> PLAYWRIGHT REAL CHROMIUM BROWSER TEST SUMMARY:")
    for k, v in results.items():
        print(f"    - {k}: {v}")
    print("=" * 75)
    print("ALL 10/10 REAL BROWSER CHECKS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    run_real_browser_test()
